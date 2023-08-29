import matplotlib.pyplot as plt
import pandas as pd
from database_manager import DatabaseManager

class PlottingModule:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def plot_stock_data(self, ticker, start_date, end_date):
        # Fetch data from the database
        data = self.db_manager.fetch_data(ticker, start_date, end_date)

        # Plot stock prices
        plt.figure(figsize=(14,7))
        plt.plot(data['close'], label='Close Price')
        plt.title(f'{ticker} Stock Price')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)
        plt.show()

    def plot_indicators(self, ticker, start_date, end_date):
        # Fetch data from the database
        data = self.db_manager.fetch_data(ticker + '_indicators', start_date, end_date)

        # Plot indicators
        plt.figure(figsize=(14,7))
        plt.plot(data['SMA_50'], label='SMA 50')
        plt.plot(data['SMA_200'], label='SMA 200')
        plt.plot(data['RSI'], label='RSI')
        plt.plot(data['MACD'], label='MACD')
        plt.title(f'{ticker} Technical Indicators')
        plt.xlabel('Date')
        plt.ylabel('Value')
        plt.legend()
        plt.grid(True)
        plt.show()

    def plot_signals(self, ticker, start_date, end_date):
        # Fetch data from the database
        data = self.db_manager.fetch_data(ticker + '_signals', start_date, end_date)

        # Plot buy and sell signals
        plt.figure(figsize=(14,7))
        plt.plot(data['close'], label='Close Price', color='blue')
        plt.scatter(data[data['buy_signal']].index, data[data['buy_signal']]['close'], color='green', label='Buy Signal', marker='^', alpha=1)
        plt.scatter(data[data['sell_signal']].index, data[data['sell_signal']]['close'], color='red', label='Sell Signal', marker='v', alpha=1)
        plt.title(f'{ticker} Buy and Sell Signals')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)
        plt.show()

