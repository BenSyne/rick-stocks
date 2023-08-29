
import psycopg2
from psycopg2 import sql
import pandas as pd
from logger import Logger

class AuditTrail:
    def __init__(self, db_manager, logger):
        self.db_manager = db_manager
        self.logger = logger

    def record_trade(self, trade):
        """
        Record a trade in the database.
        trade: dict with keys ['timestamp', 'ticker', 'price', 'quantity', 'trade_type', 'strategy']
        """
        try:
            query = sql.SQL(
                "INSERT INTO trades (timestamp, ticker, price, quantity, trade_type, strategy) "
                "VALUES (%s, %s, %s, %s, %s, %s);"
            )
            self.db_manager.cursor.execute(query, (
                trade['timestamp'],
                trade['ticker'],
                trade['price'],
                trade['quantity'],
                trade['trade_type'],
                trade['strategy']
            ))
            self.db_manager.conn.commit()
            self.logger.log(f"Recorded trade: {trade}")
        except Exception as e:
            self.logger.log(f"Failed to record trade: {trade}. Error: {str(e)}", level='error')

    def retrieve_trades(self, start_date=None, end_date=None, ticker=None):
        """
        Retrieve trades from the database.
        start_date, end_date: datetime.date objects specifying the date range.
        ticker: string specifying the stock ticker.
        Returns a DataFrame.
        """
        try:
            query = "SELECT * FROM trades"
            conditions = []
            if start_date is not None:
                conditions.append(f"timestamp >= '{start_date}'")
            if end_date is not None:
                conditions.append(f"timestamp <= '{end_date}'")
            if ticker is not None:
                conditions.append(f"ticker = '{ticker}'")
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += ";"
            df = pd.read_sql_query(query, self.db_manager.conn)
            self.logger.log(f"Retrieved trades: {df}")
            return df
        except Exception as e:
            self.logger.log(f"Failed to retrieve trades. Error: {str(e)}", level='error')
            return pd.DataFrame()

