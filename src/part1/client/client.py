import requests, json, random, time, threading
from ip import *
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
stockNames = ["GameStart", "FishCo", "BearCo", "MenhirCo", "Cici", "GameStart2", "FishCo2", "BearCo2", "MenhirCo2", "Cici2"]
threshold = 0.6

class ClientState:
    def __init__(self) -> None:
        self.num_order = 0
        self.max_tran = 0
        self.lock = threading.Lock()

    def increment_order(self):
        with self.lock:
            self.num_order += 1
    def update_maxtran(self, max_tran):
        with self.lock:
            self.max_tran = max(max_tran, self.max_tran)
    def get_order(self):
        with self.lock:
            return self.num_order

    def get_tran(self):
        with self.lock:
            return self.max_tran
    
MyState = ClientState()

# return transaction number on success 
# -1 otherwise
def order(session: requests.Session, stockName: str, max_vol: int)->int:

    frontend_url = f"{frontend_ip}/orders"
    type = "buy"
    quantity = random.randrange(0, min(max_vol - 1, 100))
    if (random.random() < 0.5):
        type = "sell"
        quantity = 100
        
    message = {
        "name": stockName,
        "type": type,
        "quantity": quantity
    }
    try:
        reply = session.post(frontend_url, json=message).json()
    except Exception as e:
        print(e)

    transaction_num = 0
    if ("error" in reply):
        transaction_num = 0
    else:
        transaction_num = int(reply["data"]["transaction_number"])
    global MyState
    MyState.increment_order()
    MyState.update_maxtran(transaction_num)
    return int(transaction_num)

# return remaining volume of the stockName
# -1 on failure
def lookup(session: requests.Session, stockName: str)->int:
    vol = 0
    frontend_url = f"{frontend_ip}/stockName/{stockName}"
    reply = session.get(frontend_url).json()
    if ("error" in reply):
        vol = -1
    else:
        vol = reply["data"]["quantity"] 
    return int(vol)

def randomReq():
    stockName = random.choice(stockNames)
    session = requests.Session()
    vol = lookup(session, stockName)
    if (vol > 10 and random.random() < threshold):
        _ = order(session, stockName, vol)

            
def req(num_req):
    for i in range(num_req):
        randomReq()
        
if __name__ == "__main__":
    number_req = 20
    start_time = time.time()
    max_worker = 5
    tasks = []
    with ThreadPoolExecutor(max_worker) as executor:
        for i in range(max_worker):
            tasks.append(executor.submit(req, number_req))
    
    for task in tasks:
        try:
            task.result()
        except Exception as e:
            pass
        
    end_time = time.time()
    # global max_tran, num_order
    num_order = MyState.get_order()
    max_tran = MyState.get_tran()
    print(max_tran, num_order)
    total_req = number_req * max_worker + num_order

    print(f"Threshold: {threshold} | Number of Worker {max_worker}")
    print(f"Send {total_req} requests ({number_req * max_worker} lookup; {num_order} orders; {max_tran} transactions) in {end_time - start_time} sec")
    print(f"Throughput: {total_req / (end_time - start_time)} req/sec | Latency: {(end_time - start_time) / total_req }")
