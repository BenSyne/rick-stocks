import psycopg2
from psycopg2 import sql
import pandas as pd


db_name = 'interactive_brokers_database'
user = 'macman'
password = 'My@oNtpd6v-WUzqBgjfA'

class DatabaseManager:
    def __init__(self, db_name, user, password, host="localhost", port="5432"):
        self.conn = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.cursor = self.conn.cursor()
        
    def get_all_tickers(self, table_name):
        query = sql.SQL("SELECT DISTINCT ticker FROM {};").format(sql.Identifier(table_name))
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        # Extract tickers from the returned rows
        tickers = [row[0] for row in rows]
        return tickers
    
    def create_table_if_not_exists(self, table_name):
        query = sql.SQL(
            "CREATE TABLE IF NOT EXISTS {} ("
            "timestamp TIMESTAMP UNIQUE, "
            "open_price DECIMAL, "
            "close_price DECIMAL, "
            "high_price DECIMAL, "
            "low_price DECIMAL, "
            "ticker VARCHAR(10)"
            ");"
        ).format(sql.Identifier(table_name))
        self.cursor.execute(query)
        self.conn.commit()

    def insert_ticker(self, table_name, ticker):
        query = sql.SQL(
            "INSERT INTO {} (ticker) VALUES (%s);"
        ).format(sql.Identifier(table_name))
        self.cursor.execute(query, (ticker,))
        self.conn.commit()
        
    def create_table(self, table_name):
        query = sql.SQL(
            "CREATE TABLE IF NOT EXISTS {} ("
            "timestamp TIMESTAMP UNIQUE, "
            "open_price DECIMAL, "
            "close_price DECIMAL, "
            "high_price DECIMAL, "
            "low_price DECIMAL"
            ");"
        ).format(sql.Identifier(table_name))
        self.cursor.execute(query)
        self.conn.commit()
    def insert_data(self, table_name, data):
        # Check if the columns exist in the table
        self.cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
        colnames = [desc[0] for desc in self.cursor.description]
        for column in ['atr', 'atr_trailing_stop', 'signal']:
            if column not in colnames:
                # Add the column if it does not exist
                self.cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column} FLOAT")

        # Insert data into the table
        for index, row in data.iterrows():
            query = f"""INSERT INTO "{table_name}" (open_price, close_price, high_price, low_price, atr, atr_trailing_stop, signal, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (timestamp) DO UPDATE 
                        SET open_price = %s, close_price = %s, high_price = %s, low_price = %s, atr = %s, atr_trailing_stop = %s, signal = %s"""
            self.cursor.execute(query, (row['open_price'], row['close_price'], row['high_price'], row['low_price'], row['atr'], row['atr_trailing_stop'], row['signal'], index, row['open_price'], row['close_price'], row['high_price'], row['low_price'], row['atr'], row['atr_trailing_stop'], row['signal']))
        self.conn.commit()
        
    def fetch_data(self, table_name, start_date, end_date):
        query = sql.SQL(
            "SELECT * FROM {} "
            "WHERE timestamp >= %s AND timestamp <= %s "
            "ORDER BY timestamp ASC;"
        ).format(sql.Identifier(table_name))
        self.cursor.execute(query, (start_date, end_date))
        rows = self.cursor.fetchall()
        # Fetch column names from information_schema.columns
        self.cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table_name,))
        columns = [column[0] for column in self.cursor.fetchall()]
        return pd.DataFrame(rows, columns=columns)
    
    def alter_table(self, table_name):
        query = sql.SQL(
            "SELECT column_name FROM information_schema.columns WHERE table_name = %s"
        )
        self.cursor.execute(query, (table_name,))
        columns = [column[0] for column in self.cursor.fetchall()]
        if 'volume' in columns:
            query = sql.SQL(
                "ALTER TABLE {} DROP COLUMN volume;"
            ).format(sql.Identifier(table_name))
            self.cursor.execute(query)
            self.conn.commit()
            
    def get_data(self, table_name):
        query = sql.SQL("SELECT * FROM {};").format(sql.Identifier(table_name))
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        # Fetch column names from information_schema.columns
        self.cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table_name,))
        columns = [column[0] for column in self.cursor.fetchall()]
        return pd.DataFrame(rows, columns=columns)

    def close_connection(self):
        self.cursor.close()
        self.conn.close()
        
    def timestamp_exists(self, table_name, timestamp):
        query = f"SELECT EXISTS(SELECT 1 FROM {table_name} WHERE timestamp = %s)"
        self.cursor.execute(query, (timestamp,))
        return self.cursor.fetchone()[0]
    
    def get_first_date(self, table_name):
        query = sql.SQL("SELECT MIN(timestamp) FROM {};").format(sql.Identifier(table_name))
        self.cursor.execute(query)
        return self.cursor.fetchone()[0]

    def get_last_date(self, table_name):
        query = sql.SQL("SELECT MAX(timestamp) FROM {};").format(sql.Identifier(table_name))
        self.cursor.execute(query)
        return self.cursor.fetchone()[0]


