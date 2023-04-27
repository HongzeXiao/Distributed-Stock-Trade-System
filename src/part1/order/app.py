from flask import request, jsonify, Flask
import os
from order import Order
from ip import *
import requests

app = Flask(__name__)

csvpath = os.path.dirname(__file__) + "/order.csv"
MyOrder = Order(csvpath)

@app.route("/orders", methods=["POST"])
def orders():
    content = request.get_json()
    catalog_addr = f"{catalog_ip}/orders"
    reply = requests.post(catalog_addr, json=content).json()
    if ("error" in reply):
        print("Order Service: transaction failed:", content)
        return jsonify(reply)
    else:
        tradeInfo = reply["data"]
        tradeInfo["type"] = content["type"]
        tradeInfo["trade_quantity"] = content["quantity"]
        transaction_number = MyOrder.trade(tradeInfo)
        # invalidate the cached data on the frontend
        if int(content["quantity"] > 0):
            name = content["name"]
            frontend_addr = f"{frontend_ip}/stockName/{name}"
            _ = requests.delete(frontend_addr)
        return jsonify({
            "data": {
                "transaction_number": transaction_number
            }
        })
    
if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=8081)
    except Exception as e:
        print(e)
    finally:
        MyOrder.saveToDisk()