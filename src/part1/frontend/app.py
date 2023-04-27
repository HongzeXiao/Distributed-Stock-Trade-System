from flask import Flask, request, jsonify
import threading
import requests

from ip import * 
app = Flask(__name__)

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

# return the item info or invalidate an item's cache results
@app.route("/stockName/<name>", methods=["GET", "DELETE"])
def stockName(name):
    if request.method == "GET":
        cached_item = MyCache.get(name)
        if cached_item is None:
            catelog_url = f"{catalog_ip}/stockName/{name}"
            response = requests.get(catelog_url).json()
            if "data" in response:
                MyCache.add(name, response["data"])
            
            return jsonify(response)
        else:
            return jsonify({
                "data": cached_item
            })

    
    elif request.method == "DELETE":
        # invalidate cached results
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
    order_server_addr = f"{order_ip_1}/orders"
    transaction = requests.post(order_server_addr, json=content).json()
    return jsonify(transaction)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)