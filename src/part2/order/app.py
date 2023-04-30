from flask import request, jsonify, Flask
import os, json
from order import Order
from ip import *
import requests
from dataclasses import dataclass

@dataclass
class OrderState:
    replica_id = int(os.getenv("ORDER_REPLICA_ID", 0)) # id of the current instance
    leader_id = -1
    
app = Flask(__name__)
csvpath = os.path.dirname(__file__) + "/order.csv"
MyOrder = Order(csvpath)
MyState = OrderState()

def get_leader_transactions(leader_addr):
    data = requests.get(leader_addr).json()
    if ("error" not in data):
        MyOrder.transaction_number = data["transaction_number"]
        MyOrder.transactions = data["transactions"]
        MyOrder.saveToDisk()
        
def try_sync():
    # try to synchronize with the leader node
    for id, ip in enumerate(order_ips):
        if id != MyState.replica_id:
            addr = ip + "/synchronize"
            get_leader_transactions(addr)


@app.route("/orders", methods=["POST"])
def orders():
    assert(MyState.leader_id == MyState.replica_id)
    
    content = request.get_json()
    catalog_addr = f"{catalog_ip}/orders"
    reply = requests.post(catalog_addr, json=content).json()
    if ("error" in reply):
        print("Order Service: transaction failed:", content)
        return jsonify(reply)
    else:
        with MyOrder.lock:
            tradeInfo = reply["data"]
            tradeInfo["type"] = content["type"]
            tradeInfo["trade_quantity"] = content["quantity"]
            transaction_number = MyOrder.trade_nolock(tradeInfo)

            # send transaction to the replicas
            num_success = 0
            for id, ip in enumerate(order_ips):
                if (id != MyState.replica_id):
                    replica_addr = ip + "/replica_orders"
                    try:
                        reply = requests.post(replica_addr, json={
                            "transaction": tradeInfo,
                            "leader_id": MyState.replica_id
                        }).json()
                        if ("error" in reply):
                            synchronize_addr = ip + "/synchronize"
                            reply = requests.post(synchronize_addr, json={
                                "transactions": MyOrder.transactions,
                                "transaction_number": MyOrder.transaction_number,
                                "leader_id": MyState.replica_id
                            }).json()
                            num_success += 1 
                        else:
                            num_success += 1
                    except Exception as e:
                        # when the replica is not alive this might happen
                        print(e)
                        
            # only reply to the frontend when at least half of the replicas success
            if num_success >= 1:
                # invalidate the cached data on the frontend
                name = content["name"]
                frontend_addr = f"{frontend_ip}/stockName/{name}"
                _ = requests.delete(frontend_addr)
                return jsonify({
                    "data": {
                        "transaction_number": transaction_number
                    }
                })
            else:
                # rollback
                if content["type"] == "buy":
                    content["type"] = "sell"
                else:
                    content["type"] = "buy"
                reply = requests.post(catalog_addr, json=content).json()

                return jsonify({
                    "error": "failed to contact replicas"
                })
            

@app.route("/replica_orders", methods=["POST"])
def replica_orders():
    content = request.get_json()
    # replica nodes use this route to receive transaction order
    
    if ("error" in content):
        print("Order Service: transaction failed:", content)
        return jsonify({"error": "transaction failed, should be ignored instead of sending to replica"})
    else:
        print("replica_orders received:", content)
        tradeInfo = content["transaction"]
        leader_id = int(content["leader_id"])
        MyState.leader_id = leader_id
        assert(MyState.replica_id != leader_id)
        
        # Here, we assume the replica might be just restarted from a crush
        # So the current replica needs to be synchronized with the leader.
        # If the transaction number does not match with the leader's transaction number
        transaction_number = MyOrder.trade(tradeInfo)
        if (transaction_number != tradeInfo["transaction_number"]):
            return jsonify({"error": "transaction number miss match, needs to handle synchronization"})
        else:  
            return jsonify({
                "data": {
                    "transaction_number": transaction_number
                }
            })
        
# Only leader will respond to this url
# The leader node sends orders to other replica nodes
@app.route("/synchronize/", methods=["GET", "POST"])
def synchronize():
    if request.method == "GET":
        if MyState.replica_id == MyState.leader_id:
            with MyOrder.lock:
                return jsonify ({
                    "transaction_number": MyOrder.transaction_number,
                    "transactions" : MyOrder.transactions
                })
        else:
            return jsonify({
                "error": "only leader node can respond to this request"
            })
    elif request.method == "POST":
        content = request.get_json()
        transactions = content["transactions"]
        transaction_number = content["transaction_number"]
        with MyOrder.lock:
            MyOrder.transaction_number = transaction_number
            MyOrder.transactions = transactions
        
    return jsonify({"data" : "success"})
    
# This route updates the leader id to the specified integer
@app.route("/ping/", methods=["GET"])
def ping():
    return jsonify({"data": "success", 
                    "transaction_number": MyOrder.transaction_number,
                    "replica_id": MyState.replica_id})

# It serves to elect the current replica as the new leader
@app.route("/elect/", methods=["POST"])
def elect():
    data = request.get_json()
    frontend_tran_num = data["transaction_number"]
    assert(frontend_tran_num <= MyOrder.transaction_number)
    if frontend_tran_num < MyOrder.transaction_number:
        # in case the previous leader failed when it has altered the state in catalog service
        # we roll back the state on the catalog service to be in sync with the current leader's log
        # this is done by sending all the logs to catalog service to allow it roll back the transactions

        # 1. rollback catalog
        catalog_addr = f"{catalog_ip}/rollback"
        _ = requests.post(catalog_addr, json={"transaction_number": frontend_tran_num,
                                              "transactions": MyOrder.transactions[frontend_tran_num:]})
        # 2. invalidate cached results on frontend
        frontend_addr = f"{frontend_ip}/stockName/all"
        _ = requests.delete(frontend_addr)
        
    
    # Here, we assume the orginal leader is crushed so a new leader has to be elected
    print(f"new leader {MyState.replica_id} | old leader {MyState.leader_id}")
    MyState.leader_id = MyState.replica_id
    return jsonify({"data": "success"})

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=8081 + MyState.replica_id)
    except Exception as e:
        print(e)
    finally:
        MyOrder.saveToDisk()