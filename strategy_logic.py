import pandas as pd
import talib
from database_manager import DatabaseManager
from technical_indicators_generator import TechnicalIndicatorsGenerator
from decimal import Decimal

class StrategyLogic:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def atr_signals(self, data, atr_period, atr_multip):
        """
        data: DataFrame with columns ['open', 'high', 'low', 'close_price']
        Returns a DataFrame with ATR trailing stops and buy/sell signals.
        """

        # Calculate ATR
        data['atr'] = talib.ATR(data['high_price'], data['low_price'], data['close_price'], timeperiod=atr_period)

        # ATR Trailing Stop function
        data['atr_trailing_stop'] = StrategyLogic.atr_trailing_stop(data['close_price'], data['atr'], atr_multip)

        # Generate buy and sell signals
        data['buy_signal'] = (data['close_price'].shift(1) < data['atr_trailing_stop'].shift(1)) & (data['close_price'] > data['atr_trailing_stop'])
        data['sell_signal'] = (data['close_price'].shift(1) > data['atr_trailing_stop'].shift(1)) & (data['close_price'] < data['atr_trailing_stop'])

        # Assign signal values: 0 for no signal, 1 for a positive signal, and -1 for a short signal
        data['signal'] = 0
        data.loc[data['buy_signal'], 'signal'] = 1
        data.loc[data['sell_signal'], 'signal'] = -1

        # Add stop loss column
        data['stop_loss'] = data['atr_trailing_stop'].shift(1)

        return data  # return the DataFrame

    @staticmethod
    def atr_trailing_stop(close_price, atr, atr_multip):
        atr = atr.apply(Decimal)  # convert each element in atr to Decimal
        n_loss = Decimal(atr_multip) * atr  # now this should work
        atr_trailing_stop = [0] * len(close_price)
        for i in range(1, len(close_price)):
            if pd.isnull(n_loss[i]):  # check if n_loss[i] is NaN
                atr_trailing_stop[i] = atr_trailing_stop[i-1]  # use the previous value if n_loss[i] is NaN
            elif close_price[i] > atr_trailing_stop[i-1]:
                atr_trailing_stop[i] = max([atr_trailing_stop[i-1], close_price[i] - n_loss[i]])
            elif close_price[i] < atr_trailing_stop[i-1]:
                atr_trailing_stop[i] = min([atr_trailing_stop[i-1], close_price[i] + n_loss[i]])
            else:
                atr_trailing_stop[i] = close_price[i] + n_loss[i] if close_price[i] > atr_trailing_stop[i-1] else close_price[i] - n_loss[i]
        return atr_trailing_stop

    def generate_signals(self, ticker, timeframe, atr_period, atr_multip):
        # Define table names
        table_name = f"{ticker}_{timeframe}"

        # Fetch the first and last date from the database
        start_date = self.db_manager.get_first_date(table_name)
        end_date = self.db_manager.get_last_date(table_name)

        # Fetch raw stock data from the database
        data = self.db_manager.fetch_data(table_name, start_date, end_date)

        # Set the timestamp column as the index
        data.set_index('timestamp', inplace=True)

        # Convert the index to a datetime object
        data.index = pd.to_datetime(data.index)

        # Generate ATR signals
        data = self.atr_signals(data, atr_period, atr_multip)
        
        # Convert the index to a string format suitable for PostgreSQL
        data.index = data.index.strftime('%Y-%m-%d %H:%M:%S')

        # Store signals in the database
        self.db_manager.insert_data(table_name, data)

class ATRSignalsStrategy(StrategyLogic):
    def __init__(self, db_manager):
        super().__init__(db_manager)

    def generate_signals(self, ticker, start_date, end_date, atr_period_5m, atr_multip_5m, atr_period_1h, atr_multip_1h):
        # Fetch data for 5m and 1h timeframes
        data_5m = self.db_manager.fetch_data(f"{ticker}_5_mins", start_date, end_date)
        data_1h = self.db_manager.fetch_data(f"{ticker}_1_hour", start_date, end_date)

        # Generate ATR signals for both timeframes
        data_5m = self.atr_signals(data_5m, atr_period_5m, atr_multip_5m)
        data_1h = self.atr_signals(data_1h, atr_period_1h, atr_multip_1h)

        # Generate stop_loss column
        data_5m['stop_loss'] = data_5m['atr_trailing_stop'].shift(1)
        data_1h['stop_loss'] = data_1h['atr_trailing_stop'].shift(1)

        # Store signals in the database
        self.db_manager.insert_data(f"{ticker}_5_mins", data_5m)
        self.db_manager.insert_data(f"{ticker}_1_hour", data_1h)

if __name__ == "__main__":
    # Initialize DatabaseManager and StrategyLogic
    db_manager = DatabaseManager('interactive_brokers_database', 'macman', 'My@oNtpd6v-WUzqBgjfA')
    strategy = StrategyLogic(db_manager)

    # Define parameters
    ticker = "tsla"  # replace with your ticker
    atr_period = 14  # replace with your ATR period
    atr_multip = 3  # replace with your ATR multiplier

    # Generate signals for different timeframes
    for timeframe in ["5_mins", "1_hour"]:
        # Define table name
        table_name = f'{ticker}_{timeframe}'  # table name without double quotes

        # Fetch the first and last date from the database
        start_date = db_manager.get_first_date(table_name)
        end_date = db_manager.get_last_date(table_name)

        # Fetch raw stock data from the database
        data = db_manager.fetch_data(table_name, start_date, end_date)

        # Set the timestamp column as the index
        data.set_index('timestamp', inplace=True)

        # Convert the index to a datetime object
        data.index = pd.to_datetime(data.index)

        # Generate ATR signals
        data = strategy.atr_signals(data, atr_period, atr_multip)
        
        # Convert the index to a string format suitable for PostgreSQL
        data.index = data.index.strftime('%Y-%m-%d %H:%M:%S')

        # Store signals in the database
        db_manager.insert_data(table_name, data)

        # Fetch the updated data with stop loss column from the database
        data_with_stop_loss = db_manager.fetch_data(table_name, start_date, end_date)

        # Store stop_loss data in the database
        db_manager.insert_data(table_name, data_with_stop_loss)

    # Fetch 5-minute data with signals
    data_5m = db_manager.fetch_data(f'{ticker}_5_mins', start_date, end_date)

    # Print 5-minute data
    print(data_5m)