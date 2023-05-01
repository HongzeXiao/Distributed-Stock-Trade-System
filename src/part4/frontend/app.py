from flask import Flask, request, jsonify
import threading
import requests
import time
import csv

from ip import * 
app = Flask(__name__)
class FrontendState:
    def __init__(self):
        self.elect_lock = threading.Lock()
        self.tran_lock = threading.Lock()
        
        self.leader_id = -1
        self.alive_order_replicas = []
        self.path = os.path.dirname(__file__) + "/frontend.csv"
        self.transaction_number = 0
    
    def update_transaction_number(self, new_transaction_number):
        with self.tran_lock:
            self.transaction_number = max(self.transaction_number, new_transaction_number)
            
    def get_leader_id(self):
        assert(self.leader_id != -1)
        return self.leader_id
    
    def get_leader_addr(self):
        return order_ips[self.get_leader_id()]
    
    def elect(self):
        with self.elect_lock:
            while self.leader_id == -1:
                self.do_elect()
                if (self.leader_id == -1):
                    time.sleep(0.1)
            
            elect_addr = self.get_leader_addr() + "/elect"
            # send the current transaction number to the order service to perform rollback if needed
            _ = requests.post(elect_addr, json={"transaction_number": self.transaction_number})
            
        
    def do_elect(self):
        self.alive_order_replicas = []
        for id, ip in enumerate(order_ips):
            try:
                ping_addr = f"{ip}/ping"
                reply = requests.get(ping_addr).json()
                self.alive_order_replicas.append(reply)
            except Exception as e:
                print(e)
        
        # select the replica with the highest transaction number as the new leader
        new_leader_id = -1
        new_leader_trannum = -1
        print("election alive replicas: ", self.alive_order_replicas)
        for r in self.alive_order_replicas:
            if (new_leader_id == -1):
                new_leader_id = r["replica_id"]
                new_leader_trannum = r["transaction_number"]
            elif (new_leader_trannum < r["transaction_number"]):
                new_leader_id = r["replica_id"]
                new_leader_trannum = r["transaction_number"]
            elif (new_leader_id < r["replica_id"] and new_leader_trannum == r["transaction_number"]):
                new_leader_id = r["replica_id"]
                new_leader_trannum = r["transaction_number"]
        self.leader_id = new_leader_id
    
    def saveToDisk(self):
        print("Save frontend state to disk: ", self.path)
        with open(self.path, 'w+') as csvfile:
            fields = ["transaction_number"]
            writer = csv.DictWriter(csvfile, fields)
            writer.writeheader()
            writer.writerow({"transaction_number": self.transaction_number})

    def loadFromDisk(self):
        print("Load frontend state from disk: ", self.path)
        try:
            with open(self.path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    self.transaction_number = row["transaction_number"]
        except Exception as e:
            print(e)
                
class MemCache:
    def __init__(self):
        self.mem_cache = {}
        self.lock = threading.Lock()
        
    # add a key value pair into the cache
    def add(self, k, v):
        with self.lock:
            self.mem_cache[k] = v
    # remove a key from the cache
    def rm(self, k):
        with self.lock:
            self.mem_cache.pop(k, None)
            
    # read from the dict
    def get(self, k):
        # with self.lock:
        #     return self.mem_cache.get(k, None)
        return self.mem_cache.get(k, None)

MyCache = MemCache() # caching the item data in memory
MyState = FrontendState() 

# return the item info or invalidate an item's cache results
@app.route("/stockName/<name>", methods=["GET", "DELETE"])
def stockName(name):
    if request.method == "GET":
        catelog_url = f"{catalog_ip}/stockName/{name}"
        response = requests.get(catelog_url).json()
        return jsonify(response)

        # cached_item = MyCache.get(name)
        # if cached_item is None:
        #     catelog_url = f"{catalog_ip}/stockName/{name}"
        #     response = requests.get(catelog_url).json()
        #     if "data" in response:
        #         MyCache.add(name, response["data"])
            
        #     return jsonify(response)
        # else:
        #     return jsonify({
        #         "data": cached_item
        #     })

    
    elif request.method == "DELETE":
        # invalidate cached results
        if (name == "all"):
            MyCache.mem_cache = {}
        else:
            MyCache.rm(name)
        return jsonify({
            "data": "ok",
            "code": 300
        })
    
    else:
        return jsonify({
            "error": "logic error, should not reach here"
        })
        
@app.route("/orders/", methods=["POST"])
def order():
    content = request.get_json()
    send = False
    transaction = {}
    if MyState.leader_id==-1:
        MyState.elect()
    while send is False:
        try:
            order_server_addr = f"{MyState.get_leader_addr()}/orders"
            transaction = requests.post(order_server_addr, json=content).json()
            send = True
        except Exception as e:
            print(e)
            # assume the original leader is down
            # needs to update the leader
            MyState.elect()
        
    if ("data" in transaction):
        # update transaction number
        MyState.update_transaction_number(transaction["data"]["transaction_number"])
        # error otherwise
    
    return jsonify(transaction)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=8080)
    except Exception as e:
        print(e)
    finally:
        MyState.saveToDisk()