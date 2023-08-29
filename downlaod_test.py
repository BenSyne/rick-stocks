from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from time import sleep

class TestIBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def historicalData(self, reqId, bar):
        print(f"Date: {bar.date}, Open: {bar.open}, High: {bar.high}, Low: {bar.low}, Close: {bar.close}")

    def error(self, reqId, errorCode, errorString):
        print(f"Error {errorCode}: {errorString}")

app = TestIBapi()
app.connect('127.0.0.1', 7496, 0)  # Adjust port number (7497 or 7496) and client ID (123) as necessary

# Start the socket in a separate thread
import threading
api_thread = threading.Thread(target=app.run)
api_thread.start()

sleep(1)  # Sleep interval to allow time for connection to server

# Create contract object for AAPL stock
contract = Contract()
contract.symbol = 'SHOP'
contract.secType = 'STK'
contract.exchange = 'SMART'
contract.currency = 'USD'

# Request historical bars for testing
app.reqHistoricalData(1, contract, '', '1 D', '1 hour', 'MIDPOINT', 0, 1, False, [])

sleep(5)  # Allow some time for data to be fetched
app.disconnect()
