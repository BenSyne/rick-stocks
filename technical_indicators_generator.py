import pandas as pd
import talib
from database_manager import DatabaseManager

class TechnicalIndicatorsGenerator:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def calculate_indicators(self, data, ticker):
        # Calculate Moving Averages
        data['SMA_50'] = talib.SMA(data['close'], timeperiod=50)
        data['SMA_200'] = talib.SMA(data['close'], timeperiod=200)

        # Calculate RSI
        data['RSI'] = talib.RSI(data['close'], timeperiod=14)

        # Calculate MACD
        data['MACD'], data['MACD_signal'], data['MACD_hist'] = talib.MACD(data['close'], fastperiod=12, slowperiod=26, signalperiod=9)

        # Store computed indicators in the database
        self.db_manager.insert_data(ticker + '_indicators', data)

    def generate_indicators(self, ticker):
        # Fetch raw stock data from the database
        data = self.db_manager.fetch_data(ticker)

        # Calculate and store indicators
        self.calculate_indicators(data, ticker)

