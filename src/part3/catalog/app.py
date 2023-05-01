from flask import request, jsonify, Flask
from catalog import Catalog
import os

csvpath = os.path.dirname(__file__) + "/catalog.csv"
MyCatalog = Catalog(csvpath)

app = Flask(__name__)

@app.route("/stockName/<name>", methods=["GET"])
def stockName(name):
    stockInfo = MyCatalog.lookUp(name)
    if (stockInfo == None):
        return jsonify({
            "error": f"stock {name} does not exits",
            "code": 400
        })
    
    else:
        return jsonify({
            "data": stockInfo
        })
        
@app.route("/orders/", methods=["POST"])
def orders():
    content = request.get_json()
    tobuy = content["type"] == "buy"
    name = content["name"]
    quantity = int(content["quantity"])
    stockInfo = MyCatalog.trade(name, tobuy, quantity)
    if stockInfo != None:
        stockInfo["trade_quantity"] = quantity
        return jsonify({
            "data": stockInfo
        })
    else:
        return jsonify({
            "error": f"trade failed",
            "code": 400
        })
        
@app.route("/rollback/", methods=["POST"])
def rollback():
    content = request.get_json()
    transaction_number = int(content["transaction_number"])
    transactions = content["transactions"]
    MyCatalog.rollback(transaction_number, transactions)
    return jsonify({
        "data": "success"
    })
        
if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=8085)
    except Exception as e:
        pass
    finally:
        MyCatalog.saveToDisk()