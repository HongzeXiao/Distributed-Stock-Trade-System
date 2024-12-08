from flask import request, jsonify, Flask
import os, json
from order import Order
from ip import *
import requests
from dataclasses import dataclass

@dataclass
class OrderState:
    replica_id = int(os.getenv("ORDER_REPLICA_ID", 0))
    leader_id=-1

app = Flask(__name__)
csv_path=os.path.dirname(__file__)+"/orders.csv"
order_server=Order(csv_path)
order_state=OrderState()

def get_leader_transactions(leader_addr):
    data = requests.get(leader_addr).json()
    if "error" not in data:
        order_server.transaction_number = int(data["transaction_number"])
        order_server.transactions=data["transactions"]
        order_server.save_to_disk()

def try_sync():
    # try to synchronize with the leader node
    for id, ip in enumerate(order_ips):
        if id != order_state.replica_id:
            addr=ip+"/synchronize"
            get_leader_transactions(addr)




@app.route("/orders", methods=["POST"])
def orders():
    assert order_state.leader_id==order_state.replica_id

    content=request.get_json()

    catalog_url=f"{catalog_ip}/orders"
    reply=requests.post(catalog_url, json=content).json()
    if "error" in reply:
        print("Order Service: transaction failed:", content)
        return jsonify(reply)
    else:
        with order_server.lock:
            transaction_number=order_server.trade_nolock(content)
            content["transaction_number"]=transaction_number

            # send transaction to the replicas
            num_success = 0
            for id, ip in enumerate(order_ips):
                if id != order_state.replica_id:
                    replica_addr = ip +"/replica_orders"
                    try:
                        reply=requests.post(replica_addr, json={
                            "transaction": content,
                            "leader_id": order_state.replica_id,
                        }).json()
                        if "error" in reply:
                            synchronize_addr = ip +"/synchronize"
                            reponse = requests.post(synchronize_addr, json={
                                "transactions" : order_server.transactions,
                                "transaction_number": order_server.transaction_number,
                                "leader_id": order_state.replica_id
                            }).json()
                            num_success+=1
                        else:
                            num_success+=1
                    except Exception as e:
                        print(e)
            
            # only reply to the frontend when at least half of the replicas success
            if num_success>=len(order_ips)//2:
                name=content["name"]
                frontend_url=f"{frontend_ip}/stocks/{name}"
                requests.delete(frontend_url)
                return jsonify({
                    "data":{
                        "transaction_number":transaction_number
                    }
                })
            else:
                # rollback
                if content["type"] == "buy":
                    content["type"]=="sell"
                else:
                    content["type"]=="buy"
                reponse = requests.post(catalog_url, json=content).json()

                return jsonify({
                    "error": "failed to contact replicas"
                })
            
@app.route("/replica_orders", methods=["POST"])
def replica_orders():
    content = request.get_json()
    # replica nodes use this route to receive transaction order

    if "error" in content:
        print("Order Service: transaction failed:", content)
        return jsonify({"error": "transaction failed, should be ignored instead of sending to replica"})
    else:
        print("replica_orders reveived: ", content)
        trade_info=content["transaction"]
        leader_id=int(content["leader_id"])
        order_state.leader_id=leader_id
        assert order_state.replica_id != leader_id

    # Here, we assume the replica might be just restarted from a crush
    # So the current replica needs to be synchronized with the leader.
    # If the transaction number does not match with the leader's transaction number
    transaction_number=order_server.trade(trade_info)
    if transaction_number != trade_info["transaction_number"]:
        return jsonify({"error": "transaction number miss match, needs to handle synchronization"})
    else:
        return jsonify({
                "data": {
                    "transaction_number": transaction_number
                }
            })
    

# Only leader will respond to this url
# The leader node sends orders to other replica nodes
@app.route("/synchronize", methods=["GET", "POST"])
def synchronize():
    if request.method=="GET":
        if order_state.replica_id == order_state.leader_id:
            with order_state.lock:
                return jsonify({
                    "transacton_number": order_server.transaction_number,
                    "transactions": order_server.transactions
                })
        else:
            return jsonify({
                "error": "Only leader node can respond to this request"
            })
    
    elif request.method=="POST":
        content = request.get_json()
        transactions = content["transactions"]
        transaction_number = int(content["transaction_number"])
        with order_state.lock:
            order_state.transaction_number=transaction_number
            order_state.transactions=transactions
    
    return jsonify({"data": "success"})

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({
        "data": "success",
        "transaction_number": order_server.transaction_number,
        "replica_id": order_state.replica_id

    })

@app.route("/elect", methods = ["POST"])
def elect():
    data = request.get_json()
    frontend_tran_num = data["transaction_number"]
    assert frontend_tran_num <= order_server.transaction_number
    if frontend_tran_num < order_server.transaction_number:
        # in case the previous leader failed when it has altered the state in catalog service
        # we roll back the state on the catalog service to be in sync with the current leader's log
        # this is done by sending all the logs to catalog service to allow it roll back the transactions
        
        # 1. rollback catalog
        catalog_url=f"{catalog_ip}/rollbcak"
        requests.post(catalog_url, json={"transaction_number": frontend_tran_num,
                                          "transactions": order_server.transactions[frontend_tran_num:]})


        # 2. invalidate cached results on frontend
        frontend_url = f"{frontend_ip}/stocks/all"
        requests.delete(frontend_url)

    # Here, we assume the orginal leader is crushed so a new leader has to be elected
    print(f"new leader {order_state.replica_id} | old leader {order_state.leader_id}")
    order_state.leader_id = order_state.replica_id
    return jsonify({"data":"success"})
    




"""
# Part 1 code:
        transaction_number=order_server.trade(content)
        # invalidate the cached data on the frontend
        if int(content["quantity"] > 0):
            name=content["name"]
            frontend_url=f"{frontend_ip}/stocks/{name}"
            requests.delete(frontend_url)

        return jsonify({
            "data":{
                "transaction_number":transaction_number
            }
        })
"""
    
@app.route("/orders/<order_number>", methods=["GET"])
def get_order(order_number):
    order_info=order_server.get_order(order_number)
    if order_info:
        return jsonify({
            "data":order_info
        })
    else:
        return jsonify({
            "error": f"order {order_number} does not exits",
            "code": 404
        })

    
if __name__=="__main__":
    try:
        app.run(host="0.0.0.0",port=8081 + order_state.replica_id, debug=True)
    except Exception as e:
        print(e)
    finally:
        order_server.save_to_disk()


