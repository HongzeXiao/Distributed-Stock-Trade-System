import threading
import os
from ip import *
import time
import requests
import csv

class FrontendState:
    def __init__(self) -> None:
        self.elect_lock=threading.Lock()
        self.tran_lock=threading.Lock()

        self.leader_id=-1
        self.alive_order_replicas=[]
        self.path = os.path.dirname(__file__) + "/frontend.csv"
        self.transaction_number=0

    def update_transaction_number(self, new_transaction_number):
        with self.tran_lock:
            self.transaction_number=max(self.transaction_number,new_transaction_number)

    def get_leader_id(self):
        assert self.leader_id!=-1
        return self.leader_id

    def get_leader_addr(self):
        return order_ips[self.get_leader_id()]
    
    def elect(self):
        with self.elect_lock:
            while self.leader_id==-1:
                self.do_elect()
                if self.leader_id==-1:
                    time.sleep(0.1)

            elect_addr=self.get_leader_addr()+"/elect"
            # send the current transaction number to the order service to perform rollback if needed
            requests.post(elect_addr, json={"transaction_number": self.transaction_number})

    def do_elect(self):
        self.alive_order_replicas=[]
        for id,ip in enumerate(order_ips):
            try:
                ping_addr=f"{ip}/ping"
                reply=requests.get(ping_addr).json()
                self.alive_order_replicas.append(reply)
            except Exception as e:
                print(e)

        # select the replica with the highest transaction number as the new leader
        new_leader_id=-1
        new_leader_trannum=-1
        print("election alive replicas: ", self.alive_order_replicas)
        
        for r in self.alive_order_replicas:
            if new_leader_id==-1 or new_leader_trannum < r["transaction_number"] or (new_leader_id < r["replica_id"] and new_leader_trannum == r["transaction_number"]):
                new_leader_id=r["replica_id"]
                new_leader_trannum=r["transaction_number"]

        self.leader_id=new_leader_id

    def save_to_disk(self):
        print("Save frontend state to disk: ", self.path)
        with open(self.path, "w+") as csvfile:
            fields=["transaction_number"]
            writer=csv.DictWriter(csvfile,fields)
            writer.writeheader()
            writer.writerow({"transaction_number": self.transaction_number})

    def load_from_disk(self):
        print("Load frontend state from disk: ", self.path)
        try:
            with open(self.path, "r") as csvfile:
                reader=csv.DictReader(csvfile)
                for row in reader:
                    self.transaction_number=row["transaction_number"]
        except Exception as e:
            print(e)
           

            
