from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import BarData
from time import sleep
import threading
import pandas as pd
import os
from database_manager import DatabaseManager
from tqdm import tqdm  # Import tqdm for the progress bar

class IBDataDownloader(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = []
        self.done = False  # Add this line
        self.bar = tqdm()  # Initialize the progress bar
        print("IBDataDownloader initialized")

    def historicalData(self, reqId, bar: BarData):
        self.data.append([bar.date, bar.open, bar.high, bar.low, bar.close])
        self.bar.update()  # Update the progress bar
        # print(f"Data appended for request {reqId}")

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        super().historicalDataEnd(reqId, start, end)
        self.done = True  # Add this line
        self.bar.close()  # Close the progress bar
        # print(f"Historical data ended for request {reqId}")

    def error(self, reqId, errorCode, errorString):
        print(f"Error {errorCode}: {errorString}")

    def disconnect(self):
        while not self.done:  # Add this line
            sleep(1)  # Add this line
        super().disconnect()
        print("Disconnected")

def download_data(tickers, start_date, end_date, time_frames):
    for ticker in tickers:
        for time_frame in time_frames:
            print(f"Downloading data for {ticker} with time frame {time_frame}")
            app = IBDataDownloader()
            app.connect("127.0.0.1", 7496, 0)

            contract = Contract()
            contract.symbol = ticker
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"

            # Start the socket in a thread
            api_thread = threading.Thread(target=app.run)
            api_thread.start()

            sleep(1)  # Sleep interval to allow time for connection to server

            # Request historical bars
            app.reqHistoricalData(1, contract, end_date+"-23:59:59", "1 Y", time_frame, 'MIDPOINT', 0, 1, False, [])
            print("Requested historical data")

            sleep(5)  # Allow some time for data to be fetched
            app.disconnect()

            app.data = pd.DataFrame(app.data, columns=['timestamp', 'open', 'high', 'low', 'close'])
            app.data.set_index('timestamp', inplace=True)

            # Save the data to a CSV file and a database table
            print(f"Saving data for {ticker} with time frame {time_frame} to CSV and database")
            save_to_csv(app.data, ticker, time_frame)
            save_to_database(app.data, ticker, time_frame, db_manager)
            print(f"Data for {ticker} with time frame {time_frame} saved to db successfully")

def save_to_csv(data, ticker, time_frame):
    # Create a nested folder structure with 'data' as the top-level folder
    folder_path = os.path.join('data', ticker, time_frame.replace(' ', '_'))
    os.makedirs(folder_path, exist_ok=True)
    print(f"Created folder {folder_path}")

    # Save the data to a CSV file within this folder
    filename = os.path.join(folder_path, f'{ticker}.csv')
    i = 1
    while os.path.exists(filename):
        filename = os.path.join(folder_path, f'{ticker}_{i}.csv')
        i += 1
    data.to_csv(filename)
    print(f"Saved data to {filename}")
    
def save_to_database(data, ticker, time_frame, db_manager):
    # Create a table name from the ticker and time frame
    table_name = f"{ticker}_{time_frame.replace(' ', '_')}"

    # Check if the table exists in the database
    if db_manager.create_table_if_not_exists(table_name):
        # If the table exists, fetch the existing data
        existing_data = db_manager.fetch_data(table_name)
        print(f"Fetched existing data for {table_name}")

        # Append new data to the existing data
        updated_data = pd.concat([existing_data, data]).drop_duplicates()

        # Update the table with the updated data
        db_manager.update_data(table_name, updated_data)
        print(f"Updated data for {table_name}")
    else:
        # If the table does not exist, create a new table and insert the data
        db_manager.create_table(table_name)
        for index, row in data.iterrows():
            db_manager.insert_data(table_name, row)
        print(f"Created new table and inserted data for {table_name}")

if __name__ == "__main__":
    # Database credentials
    db_name = 'interactive_brokers_database'
    user = 'macman'
    password = 'My@oNtpd6v-WUzqBgjfA'

    # Create an instance of DatabaseManager
    db_manager = DatabaseManager(db_name, user, password)
    print("DatabaseManager initialized")

    tickers = ["RTX"]
    start_date = '20230101'
    end_date =   '20230825'
    time_frames = ['5 mins', '15 mins', '1 hour', '4 hours', '1 day', '1W']
    download_data(tickers, start_date, end_date, time_frames)
    
    # Alter the table to drop the 'volume' column
    for ticker in tickers:
        db_manager.alter_table(ticker)
        print(f"Altered table for {ticker}")
    
    print("data downloaded")