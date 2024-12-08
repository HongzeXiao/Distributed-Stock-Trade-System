import requests, json, random, time, threading
from ip import *
from concurrent.futures import ProcessPoolExecutor

stock_names = ["GameStart", "FishCo", "BearCo", "MenhirCo", "Cici", "GameStart2", "FishCo2", "BearCo2", "MenhirCo2", "Cici2"]

threshold = 0.5
num_order=0
max_tran=0

lock=threading.Lock()

# return transaction number on success 
# -1 otherwise

def order(session: requests.Session, stock_name:str, max_vol: int)->int:
    frontend_url=f"{frontend_ip}/orders"
    type="buy"
    quantity=random.randrange(0,min(max_vol-1,100))
    if random.random()<0.5:
        type="sell"
        quantity=100
    
    message={
        "name": stock_name,
        "type": type,
        "quantity": quantity
    }

    reply = session.post(frontend_url, json=message).json()
    transaction_num = 0
    if "error" in reply:
        transaction_num=-1
    else:
        transaction_num=reply["data"]["transaction_number"]
    return transaction_num

# return remaining volume of the stockName
# -1 on failure
def lookup(session: requests.Session, stock_name:str)->int:
    vol=0
    frontend_url = f"{frontend_ip}/stocks/{stock_name}"
    reply=session.get(frontend_url).json()
    if "error" in reply:
        vol=-1
    else:
        vol=reply["data"]["quantity"]
    return vol

def random_req():
    stock_name=random.choice(stock_names)
    session=requests.Session()
    vol=lookup(session, stock_name)
    global threshold
    if vol>=0 and random.random() < threshold:
        transaction=order(session, stock_name,vol)
        with lock:
            global num_order, max_tran
            max_tran = max(max_tran, transaction)
            num_order+=1
            print("num_order:", num_order)
            


def req(num_req):
    for i in range(num_req):
        random_req()
    return num_order, max_tran

def get_num_order():
    return num_order

if __name__=="__main__":
    number_req=200
    start_time=time.time()
    max_worker=5
    tasks=[]
    number_orders=0
    with ProcessPoolExecutor(max_worker) as executor:
        for i in range(max_worker):
            tasks.append(executor.submit(req, number_req))


    for task in tasks:
        number_orders+=task.result()[0]
    


    end_time=time.time()
    total_req= number_req * max_worker + number_orders
    print(f"Threshold: {threshold} | Number of Worker {max_worker}")
    print(f"Send {total_req} requests ({number_req * max_worker} lookup and {number_orders} orders) in {end_time - start_time} sec")
    print(f"Throughput: {total_req / (end_time - start_time)} req/sec | Latency: {(end_time - start_time) / total_req }")
