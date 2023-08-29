import pandas as pd
import os
from database_manager import DatabaseManager
from strategy_logic import ATRSignalsStrategy
from tqdm import tqdm
from decimal import Decimal
import datetime
import json
import time
import matplotlib.pyplot as plt
import plotly.graph_objects as go


class BacktestingFramework:
    def __init__(self, db_manager, strategy):
        self.db_manager = db_manager
        self.strategy = strategy

    def calculate_position_size(self, entry_price, stop_loss, portfolio_value, risk_per_trade):
        risk_amount = portfolio_value * Decimal(risk_per_trade)
        # print(f"risk_amount: {risk_amount}")
        # print(f"entry_price: {entry_price}")
        # print(f"stop_loss: {stop_loss}")
        position_size = risk_amount / abs(entry_price - Decimal(stop_loss))  # Use absolute value to avoid negative position size
        # print(f"position_siz e: {position_size}")
        
        return position_size

    def backtest(self, ticker, start_date, end_date, risk_per_trade=0.01, max_total_risk=0.03):
        start_time = time.time()
        print(f"Backtesting for {ticker} from {start_date} to {end_date}.")
        signals_5m = self.db_manager.fetch_data(f"{ticker}_5_mins", start_date, end_date)
        signals_1h = self.db_manager.fetch_data(f"{ticker}_1_hour", start_date, end_date)
        
        signals_5m['timestamp'] = pd.to_datetime(signals_5m['timestamp'])
        signals_5m.set_index('timestamp', inplace=True)
        signals_5m.index = signals_5m.index.tz_localize('UTC').tz_convert('US/Eastern')

        signals_1h['timestamp'] = pd.to_datetime(signals_1h['timestamp'])
        signals_1h.set_index('timestamp', inplace=True)
        signals_1h.index = signals_1h.index.tz_localize('UTC').tz_convert('US/Eastern')

        print(signals_5m.head())
        print(signals_1h.head())

        print(f"Before filtering: {signals_5m.shape}")
        signals_5m = signals_5m.between_time('9:30', '16:00')
        print(f"After filtering: {signals_5m.shape}")

        print(f"Before filtering: {signals_1h.shape}")
        signals_1h = signals_1h.between_time('9:30', '16:00')
        print(f"After filtering: {signals_1h.shape}")

        portfolio = {'cash': 10000, 'shares': 0, 'total': 10000}

        trades = pd.DataFrame(columns=['entry_time', 'entry_price', 'stop_loss_price', 'target_price', 'win_or_loss', 'pl', 'amount_risked', 'exit_time', 'exit_price', 'exit_reason', 'trade_type', 'dollar_pl', 'percent_pl', 'position_size'])

        for index, row in tqdm(signals_5m.iterrows(), total=signals_5m.shape[0]):
            if row['signal'] == 1:  # Buy signal
                is_long = True
                # Check that the stop loss is less than the entry price for long trades
                if row['atr_trailing_stop'] >= row['close_price']:
                    print(f"Warning: Stop loss is not less than the entry price for long trade at {index}. Skipping this trade.")
                    continue
                if abs(Decimal(row['atr_trailing_stop']) - row['close_price']) / row['close_price'] < 0.0015:
                    print(f"Warning: Stop loss is too close to the entry price for short trade at {index}. Skipping this trade.")
                    continue
            elif row['signal'] == -1:  # Sell signal
                is_long = False
                # Check that the stop loss is greater than the entry price for short trades
                if row['atr_trailing_stop'] <= row['close_price']:
                    print(f"Warning: Stop loss is not greater than the entry price for short trade at {index}. Skipping this trade.")
                    continue
                # Check that the stop loss is at least 0.1% away from the entry price
                if abs(Decimal(row['atr_trailing_stop']) - row['close_price']) / row['close_price'] < 0.0015:
                    print(f"Warning: Stop loss is too close to the entry price for short trade at {index}. Skipping this trade.")
                    continue
            if row['signal'] == 1:  # Buy signal
                position_size = self.calculate_position_size(row['close_price'], row['atr_trailing_stop'], portfolio['cash'], risk_per_trade)
                portfolio['cash'] -= position_size * row['close_price']
                portfolio['shares'] += position_size
                portfolio['total'] = portfolio['cash'] + portfolio['shares'] * row['close_price']

                total_risk = position_size * (row['close_price'] - Decimal(row['atr_trailing_stop']))
                if total_risk > max_total_risk:
                    continue

                target_price = Decimal(row['close_price']) + 3 * (Decimal(row['close_price']) - Decimal(row['atr_trailing_stop']))
                exit_time, exit_price, exit_reason = self.execute_trade(row, row['atr_trailing_stop'], target_price, is_long=True)
                # Calculate PL
                if is_long:
                    pl = exit_price - row['close_price']
                else:  # Short trade
                    pl = row['close_price'] - exit_price
                    
                # Calculate dollar PL and percent PL
                dollar_pl = pl * position_size
                amount_risked = abs(row['close_price'] - Decimal(row['atr_trailing_stop'])) * position_size
                percent_pl = (dollar_pl / amount_risked) * 100 if amount_risked != 0 else 0

                # Determine win or loss
                win_or_loss = 'Win' if pl > 0 else 'Loss'

                trades = trades._append({'entry_time': index, 
                        'entry_price': row['close_price'], 
                        'stop_loss_price': row['atr_trailing_stop'], 
                        'target_price': target_price, 
                        'win_or_loss': win_or_loss, 
                        'pl': pl, 
                        'amount_risked': total_risk, 
                        'exit_time': exit_time, 
                        'exit_price': exit_price, 
                        'exit_reason': exit_reason, 
                        'trade_type': 'Long', 
                        'dollar_pl': dollar_pl, 
                        'percent_pl': percent_pl,
                        'position_size': position_size}, ignore_index=True)
                
            elif row['signal'] == -1:  # Sell signal
                position_size = self.calculate_position_size(row['close_price'], row['atr_trailing_stop'], portfolio['total'], risk_per_trade)
                portfolio['cash'] += position_size * row['close_price']
                portfolio['shares'] -= position_size
                portfolio['total'] = portfolio['cash'] - portfolio['shares'] * row['close_price']

                total_risk = position_size * (Decimal(row['atr_trailing_stop']) - row['close_price'])
                if total_risk > max_total_risk:
                    continue

                target_price = Decimal(row['close_price']) - 3 * (Decimal(row['atr_trailing_stop']) - row['close_price'])
                exit_time, exit_price, exit_reason = self.execute_trade(row, row['atr_trailing_stop'], target_price, is_long=False)

                # Calculate PL
                pl = row['close_price'] - exit_price
                dollar_pl = pl * position_size
                percent_pl = (dollar_pl / total_risk) * 100

                # Determine win or loss
                win_or_loss = 'Win' if pl > 0 else 'Loss'

                trades = trades._append({'entry_time': index, 
                        'entry_price': row['close_price'], 
                        'stop_loss_price': row['atr_trailing_stop'], 
                        'target_price': target_price, 
                        'win_or_loss': win_or_loss, 
                        'pl': pl, 
                        'amount_risked': total_risk, 
                        'exit_time': exit_time, 
                        'exit_price': exit_price, 
                        'exit_reason': exit_reason, 
                        'trade_type': 'Short', 
                        'dollar_pl': dollar_pl, 
                        'percent_pl': percent_pl,
                        'position_size': position_size}, ignore_index=True)
        # Enumerate backtests
        ticker_dir = f'backtest/{ticker}'
        if not os.path.exists(ticker_dir):
            os.makedirs(ticker_dir)

        backtest_number = len([name for name in os.listdir(ticker_dir) if os.path.isdir(os.path.join(ticker_dir, name))]) + 1
        backtest_date = datetime.datetime.now().strftime("%Y%m%d")

        # Create a unique directory for each backtest
        strategy_name = str(self.strategy.__class__.__name__)
        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")

        backtest_dir = f'{ticker_dir}/{ticker}_{strategy_name}_{start_date_str}_to_{end_date_str}_backtested_on_{backtest_date}_backtest_number_{backtest_number}'
        if not os.path.exists(backtest_dir):
            os.makedirs(backtest_dir)

        # Save backtest settings
        backtest_settings = {
            'ticker': ticker,
            'start_date': str(start_date),
            'end_date': str(end_date),
            'risk_per_trade': risk_per_trade,
            'max_total_risk': max_total_risk,
            'strategy': str(self.strategy)
        }
        with open(f'{backtest_dir}/{ticker}_settings.json', 'w') as f:
            json.dump(backtest_settings, f)

        for index, row in trades.iterrows():
            if row['stop_loss_price'] <= row['entry_price']:
                trades.loc[index, 'win_or_loss'] = 'Loss'
                trades.loc[index, 'pl'] = Decimal(row['entry_price']) - Decimal(row['stop_loss_price'])
            elif row['target_price'] >= row['entry_price']:
                trades.loc[index, 'win_or_loss'] = 'Win'
                trades.loc[index, 'pl'] = row['target_price'] - row['entry_price']

        end_time = time.time()
        backtest_duration = end_time - start_time
        print(f"Backtesting for {ticker} from {start_date} to {end_date} completed in {backtest_duration} seconds.")

        # Update file paths to include backtest_dir
        trades = trades[['entry_time', 'entry_price', 'trade_type', 'stop_loss_price', 'target_price', 'amount_risked', 'exit_time', 'exit_price', 'exit_reason', 'pl', 'dollar_pl', 'percent_pl', 'win_or_loss', 'position_size']]
        trades.to_csv(f'{backtest_dir}/{ticker}_trades.csv', index=False)

        return portfolio, backtest_dir

    def execute_trade(self, row, stop_loss, target_price, is_long):
        # Simulate the execution of a trade and return the exit time, exit price, and exit reason.
        # This is just a placeholder. You need to implement this function according to your specific trading strategy.
        
        # For now, let's just return some dummy values
        exit_time = row.name + pd.Timedelta(minutes=5)  # Exit 5 minutes after entry
        exit_price = (Decimal(stop_loss) + target_price) / 2  # Exit price is the average of stop loss and target price

        # Determine exit reason
        if is_long:
            if exit_price >= target_price:
                exit_reason = 'Take Profit'
            elif exit_price <= stop_loss:
                exit_reason = 'Stop Loss'
            else:
                exit_reason = 'Other'
        else:  # Short trade
            if exit_price <= target_price:
                exit_reason = 'Take Profit'
            elif exit_price >= stop_loss:
                exit_reason = 'Stop Loss'
            else:
                exit_reason = 'Other'

        return exit_time, exit_price, exit_reason

    def evaluate_performance(self, ticker, portfolio):
        portfolio['returns'] = pd.Series(portfolio['total']).pct_change()

        sharpe_ratio = self.calculate_sharpe_ratio(portfolio['returns'])
        drawdown = self.calculate_drawdown(portfolio['total'])

        performance = {
            'Sharpe Ratio': float(sharpe_ratio),
            'Max Drawdown': float(drawdown)
        }

        # Save performance
        with open(f'{backtest_dir}/{ticker}_performance.json', 'w') as f:
            json.dump(performance, f)

        return performance

    def calculate_sharpe_ratio(self, returns, risk_free_rate=0.01):
        excess_returns = returns - risk_free_rate
        return excess_returns.mean() / excess_returns.std()

    def calculate_drawdown(self, total):
        total_series = pd.Series(total).astype(float)
        return (total_series / total_series.cummax() - 1.0).min()
    
    
    def plot_trades(self, ticker, trades):
        import plotly.graph_objects as go

        # Only plot the last 300 trades
        trades = trades.tail(300)

        # Fetch the 5m candle data for the period of the last 300 trades
        start_date = trades.iloc[0]['entry_time']
        end_date = trades.iloc[-1]['entry_time']

        # Convert start_date and end_date to datetime objects
        start_date = datetime.datetime.fromtimestamp(start_date.astype(int))
        end_date = datetime.datetime.fromtimestamp(end_date.astype(int))

        # Fetch the candle data
        candle_data = self.db_manager.fetch_data(f"{ticker}_5_mins", start_date, end_date)

        # Create a plotly figure
        fig = go.Figure(data=[go.Candlestick(x=candle_data.index,
                                             open=candle_data['open_price'],
                                             high=candle_data['high_price'],
                                             low=candle_data['low_price'],
                                             close=candle_data['close_price'])])

        # Add ATR trailing stop loss value to the plot
        fig.add_trace(go.Scatter(x=candle_data.index, y=candle_data['atr_trailing_stop'], mode='lines', name='ATR Trailing Stop'))

        # Add markers for the trades
        # Plot long trades as green and shorts as red
        long_trades = trades[trades['entry_price'] < trades['target_price']]
        short_trades = trades[trades['entry_price'] > trades['target_price']]
        fig.add_trace(go.Scatter(x=long_trades['entry_time'], y=long_trades['entry_price'], mode='markers', marker=dict(size=10, color='green'), name='Long Trades'))
        fig.add_trace(go.Scatter(x=short_trades['entry_time'], y=short_trades['entry_price'], mode='markers', marker=dict(size=10, color='red'), name='Short Trades'))

        # Show the plot
        fig.show()
        # If the plot is not showing, uncomment the line below
        # go.offline.plot(fig)
        fig.show()
        
    def plot_pl(self, trades):
        # Convert 'pl' and 'entry_price' columns to numeric
        trades['pl'] = pd.to_numeric(trades['pl'], errors='coerce')
        trades['entry_price'] = pd.to_numeric(trades['entry_price'], errors='coerce')

        # Calculate cumulative profit and loss in dollars
        trades['cumulative_pl_dollars'] = trades['pl'].cumsum()

        # Calculate cumulative profit and loss in percent
        trades['cumulative_pl_percent'] = trades['pl'].cumsum() / trades['entry_price'].cumsum() * 100

        # Create a figure
        fig = go.Figure()

        # Add cumulative profit and loss in dollars trace
        fig.add_trace(go.Scatter(x=trades['entry_time'], y=trades['cumulative_pl_dollars'], mode='lines', name='Cumulative P&L ($)'))

        # Add cumulative profit and loss in percent trace
        fig.add_trace(go.Scatter(x=trades['entry_time'], y=trades['cumulative_pl_percent'], mode='lines', name='Cumulative P&L (%)'))

        # Add entry price trace
        fig.add_trace(go.Scatter(x=trades['entry_time'], y=trades['entry_price'], mode='lines', name='Entry Price'))

        # Add stop loss price trace
        fig.add_trace(go.Scatter(x=trades['entry_time'], y=trades['stop_loss_price'], mode='lines', name='Stop Loss Price'))

        # Add target price trace
        fig.add_trace(go.Scatter(x=trades['entry_time'], y=trades['target_price'], mode='lines', name='Target Price'))

        # Add win or loss markers
        win_trades = trades[trades['win_or_loss'] == 'Win']
        loss_trades = trades[trades['win_or_loss'] == 'Loss']
        fig.add_trace(go.Scatter(x=win_trades['entry_time'], y=win_trades['entry_price'], mode='markers', marker=dict(size=10, color='green'), name='Win Trades'))
        fig.add_trace(go.Scatter(x=loss_trades['entry_time'], y=loss_trades['entry_price'], mode='markers', marker=dict(size=10, color='red'), name='Loss Trades'))

        # Set layout
        fig.update_layout(title='Profit and Loss Chart', xaxis_title='Time', yaxis_title='Value')

        # Show the plot
        fig.show()
    
if __name__ == "__main__":
    db_manager = DatabaseManager("interactive_brokers_database", "macman", "My@oNtpd6v-WUzqBgjfA")
    strategy = ATRSignalsStrategy(db_manager)

    backtester = BacktestingFramework(db_manager, strategy)
    start_date = db_manager.get_first_date("tsla_5_mins")
    end_date = db_manager.get_last_date("tsla_5_mins")
    portfolio, backtest_dir = backtester.backtest("tsla", start_date, end_date)
    
    performance = backtester.evaluate_performance("tsla", portfolio)
    
    pd.DataFrame.from_dict(portfolio, orient='index').to_csv(f'{backtest_dir}/backtest_portfolio.csv')
    with open(f'{backtest_dir}/backtest_performance.txt', 'w') as f:
        f.write(str(performance))

    # Load trades data from csv
    trades = pd.read_csv(f'{backtest_dir}/tsla_trades.csv')
        # Load trades data from csv
    trades = pd.read_csv(f'{backtest_dir}/tsla_trades.csv')

    # Plot the profit and loss chart
    backtester.plot_pl(trades)

    # # Plot the trades
    # backtester.plot_trades("tsla", trades)
    
    




