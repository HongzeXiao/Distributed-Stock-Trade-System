import os, csv, threading

class Order:
    def __init__(self,path) -> None:
        self.lock=threading.Lock()
        self.path:str = path
        self.transaction_number=0
        self.transactions: list[dict] = []
        if path and os.path.exists(path):
            self.load_from_disk()
    
    # read data from csv file on disk
    def load_from_disk(self)->None:
        print("Load order from disk: ", self.path)
        try:
            with open(self.path,'r') as csvfile:
                reader=csv.DictReader(csvfile)
                for row in reader:
                    self.transactions.append(row)
                    self.transaction_number+=1
        except Exception as e:
            print(e)

     # save stock infos to a csv file 
    def save_to_disk(self)->None:
        print("Saving stocks to disk")
        with open(self.path,'w+') as csvfile:
            fields = ["transaction_number", "name", "type", "quantity"]
            writer=csv.DictWriter(csvfile,fields)
            writer.writeheader()
            for transnsaction in self.transactions:
                writer.writerow(transnsaction)

    # return the stockInfo of the transaction
    def trade(self, transaction: dict) -> int:
        with self.lock:
            self.transaction_number+=1
            transaction["transaction_number"]=self.transaction_number
            self.transactions.append(transaction)
            if (self.transaction_number%50==0):
                self.save_to_disk()
            return self.transaction_number
        
    def get_order(self, order_number)->dict | None:
        order_number=int(order_number)
        if order_number <=self.transaction_number and order_number>0:
            with self.lock:
                return self.transactions[order_number-1]
        else:
            return None

        
    def trade_nolock(self, transaction: dict) -> int:
        self.transaction_number += 1
        transaction["transaction_number"] = self.transaction_number
        self.transactions.append(transaction)
        if (self.transaction_number % 50 == 0):
            self.saveToDisk()
        return self.transaction_number
        

    

