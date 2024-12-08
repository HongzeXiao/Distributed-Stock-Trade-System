from flask import request, jsonify, Flask
from catalog import Catalog
import os


csv_path= os.path.dirname(__file__)+"/catalog.csv"
stocks_catalog=Catalog(csv_path)

app=Flask(__name__)

@app.route("/stocks/<name>", methods=["GET"])
def get_stock(name):
    stock_info=stocks_catalog.look_up(name)
    if stock_info:
        return jsonify({
            "data":stock_info
        })
    else:
        return jsonify({
            "error": f"stock {name} does not exits",
            "code": 404
        })

@app.route("/orders", methods=["POST"])
def orders():
    content=request.get_json()
    to_buy=content["type"]=="buy"
    name=content["name"]
    quantity=int(content["quantity"])
    stock_info=stocks_catalog.trade(name,to_buy,quantity)
    if stock_info:
        stock_info["trade_quantity"]=quantity
        return jsonify({
            "data":stock_info
        })
    else:
        return jsonify({
            "error": f"trade failed",
            "code": 400
        })
    
@app.route("/rollback", methods=["POST"])
def rollback():
    content=request.get_json()
    transaction_number=int(content["transaction_number"])
    transactions=content["transactions"]
    stocks_catalog.rollback(transaction_number,transactions)
    return jsonify({
        "data": "success"
    })
    
if __name__=="__main__":
    try:
        app.run(host="0.0.0.0",port=8085,debug=True)
    except Exception as e:
        print(e)
    finally:
        stocks_catalog.save_to_disk()
