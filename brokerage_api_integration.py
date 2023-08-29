from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.order import Order
from ibapi.contract import Contract
from ibapi.common import OrderId
from ibapi.utils import iswrapper

import threading
import time

class BrokerageAPIIntegration(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.order_id = None

    @iswrapper
    def nextValidId(self, orderId: OrderId):
        super().nextValidId(orderId)
        self.order_id = orderId
        print("Setting nextValidOrderId: ", orderId)

    def error(self, reqId, errorCode, errorString):
        print("Error: ", reqId, " ", errorCode, " ", errorString)

    def create_contract(self, symbol, sec_type="STK", exchange="SMART", currency="USD"):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = sec_type
        contract.exchange = exchange
        contract.currency = currency
        return contract

    def create_order(self, action, quantity, order_type="MKT"):
        order = Order()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = order_type
        return order

    def place_order(self, contract, order):
        if self.order_id is not None:
            self.placeOrder(self.order_id, contract, order)
            self.order_id += 1
        else:
            print("Order ID not set. Cannot place order.")

    def connect_and_run(self):
        self.connect("127.0.0.1", 7497, 0)
        thread = threading.Thread(target=self.run)
        thread.start()
        time.sleep(1)  # Allow some time to connect to the server

    def disconnect_and_stop(self):
        self.disconnect()
        time.sleep(1)  # Allow some time to disconnect from the server

if __name__ == "__main__":
    api = BrokerageAPIIntegration()
    api.connect_and_run()

    contract = api.create_contract("AAPL")
    order = api.create_order("BUY", 100)

    api.place_order(contract, order)

    time.sleep(3)  # Allow some time for the order to be processed

    api.disconnect_and_stop()

