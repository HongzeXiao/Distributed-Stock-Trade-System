import requests, json, random, time, threading
from ip import *
from concurrent.futures import ProcessPoolExecutor
stockNames = ["GameStart", "FishCo", "BearCo", "MenhirCo", "Cici", "GameStart2", "FishCo2", "BearCo2", "MenhirCo2", "Cici2"]
threshold = 0.5
num_order = 0
max_tran = 0

lock = threading.Lock()
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
    reply = session.post(frontend_url, json=message).json()
    transaction_num = 0
    if ("error" in reply):
        transaction_num = -1
    else:
        transaction_num = reply["data"]["transaction_number"]
    return transaction_num

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
    return vol

def randomReq():
    stockName = random.choice(stockNames)
    session = requests.Session()
    vol = lookup(session, stockName)
    global threshold
    if (vol > 10 and random.random() < threshold):
        transaction = order(session, stockName, vol)
        with lock:
            global num_order, max_tran
            max_tran = max(max_tran, transaction)
            num_order += 1
            
def req(num_req):
    for i in range(num_req):
        randomReq()
        
if __name__ == "__main__":
    number_req = 200
    start_time = time.time()
    max_worker = 5
    tasks = []
    with ProcessPoolExecutor(max_worker) as executor:
        for i in range(max_worker):
            tasks.append(executor.submit(req, number_req))
    
    for task in tasks:
        task.result()
        
    end_time = time.time()
    total_req = number_req * max_worker + num_order
    print(f"Threshold: {threshold} | Number of Worker {max_worker}")
    print(f"Send {total_req} requests ({number_req * max_worker} lookup and {num_order} orders) in {end_time - start_time} sec")
    print(f"Throughput: {total_req / (end_time - start_time)} req/sec | Latency: {(end_time - start_time) / total_req }")