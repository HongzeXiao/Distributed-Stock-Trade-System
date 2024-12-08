from flask import Flask, jsonify, request
import requests
from cache import MemCache
from frontend_state import FrontendState
from ip import *


app=Flask(__name__)
mem_cache=MemCache()
frontend_state=FrontendState()

@app.route("/stocks/<stock_name>",methods=["GET", "DELETE"])
def get_stock(stock_name):
    if request.method=="GET":
        cached_item=mem_cache.get(stock_name)
        if cached_item:
            return jsonify({
                "data":cached_item
            })
        else:
            catelog_get_stock_url=f"{catalog_ip}/stocks/{stock_name}"
            reply=requests.get(catelog_get_stock_url).json()
            if "data" in reply:
                mem_cache.add(stock_name,reply["data"])
            return jsonify(reply)
        
    elif request.method=="DELETE":
        if stock_name=="all":
            mem_cache.mem_cache={}
        else:
            mem_cache.rm(stock_name)
        return jsonify({
            "data":"ok",
            "code":300
        })


@app.route("/orders", methods=["POST"])
def order_stock():
    content=request.get_json()
    sent=False
    transaction={}
    if frontend_state.leader_id==-1:
        frontend_state.elect()
    while sent is False:
        try:
            order_url=f"{frontend_state.get_leader_addr()}/orders"
            reply=requests.post(order_url,json=content).json()
            transaction=reply
            sent=True
        except Exception as e:
            print(e)
            # assume the original leader is down
            # needs to update the leader
            frontend_state.elect()
    
    if "data" in transaction:
        # update transaction number
        frontend_state.update_transaction_number(transaction["data"]["transaction_number"])
            
    
    return jsonify(reply)

@app.route("/orders/<order_number>", methods=["GET"])
def get_order(order_number):
    order_url=f"{order_ip_1}/orders/{order_number}"
    reply=requests.get(order_url).json()
    return jsonify(reply)



if __name__=="__main__":
    try:
        app.run(host='0.0.0.0', port=8080, debug=True)
    except Exception as e:
        print(e)
    finally:
        frontend_state.save_to_disk()