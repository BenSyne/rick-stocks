import pandas as pd
from database_manager import DatabaseManager

class DataCleaner:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def handle_missing_data(self, data):
        # Forward fill for missing data
        data.fillna(method='ffill', inplace=True)
        return data

    def adjust_for_splits_and_dividends(self, data, ticker):
        # Fetch split and dividend data from Interactive Brokers
        split_data = self.db_manager.fetch_split_data(ticker)
        dividend_data = self.db_manager.fetch_dividend_data(ticker)

        # Adjust data for splits
        for index, row in split_data.iterrows():
            split_ratio = row['split_ratio']
            split_date = row['split_date']
            data.loc[data.index < split_date, ['open', 'high', 'low', 'close']] /= split_ratio

        # Adjust data for dividends
        for index, row in dividend_data.iterrows():
            dividend_amount = row['dividend_amount']
            ex_date = row['ex_date']
            data.loc[data.index < ex_date, ['open', 'high', 'low', 'close']] -= dividend_amount

        return data

    def handle_outliers(self, data):
        # Define a function to detect outliers based on the Z-score
        def detect_outliers(series, z_score_threshold=3):
            mean = series.mean()
            std_dev = series.std()
            z_scores = (series - mean) / std_dev
            return z_scores.abs() > z_score_threshold

        # Apply the function to the 'close' column
        outliers = detect_outliers(data['close'])

        # Replace outliers with the median of the 'close' column
        data.loc[outliers, 'close'] = data['close'].median()

        return data

    def clean_data(self, ticker):
        # Fetch raw data from the database
        data = self.db_manager.fetch_raw_data(ticker)

        # Handle missing data
        data = self.handle_missing_data(data)

        # Adjust for splits and dividends
        data = self.adjust_for_splits_and_dividends(data, ticker)

        # Handle outliers
        data = self.handle_outliers(data)

        # Update the cleaned data in the database
        self.db_manager.update_cleaned_data(data, ticker)

        return data

