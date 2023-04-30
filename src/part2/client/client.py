import requests, json, random, time
from ip import *
from concurrent.futures import ProcessPoolExecutor
stockNames = ["GameStart", "FishCo", "BearCo", "MenhirCo", "Cici", "GameStart2", "FishCo2", "BearCo2", "MenhirCo2", "Cici2"]
threshold = 0.5

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
        order(session, stockName, vol)

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
    print(f"Send {number_req} requests in {end_time - start_time} sec with")
    print(f"Threshold: {threshold} | Throughput: {number_req / (end_time - start_time)} req/sec | Latency: {(end_time - start_time) / number_req }")