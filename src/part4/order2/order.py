import csv, threading
# Order Service
# if path is specified it will save the changes to
# a csv file when the server terminates
class Order:
    def __init__(self, path) -> None:
        self.lock = threading.Lock()
        self.path: str = path
        self.transaction_number = 0
        self.transactions: list[dict]= []
        if path != None:
            self.loadFromDisk()
    
    # read data from csv file on disk
    def loadFromDisk(self)->None:
        print("Load order from disk: ", self.path)
        try:
            with open(self.path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    self.transactions.append(row)
                    self.transaction_number += 1
        except Exception as e:
            print(e)
            
    # save stock infos to a csv file 
    def saveToDisk(self) -> None:
        print("Saving stocks to disk")
        with open(self.path, 'w+') as csvfile:
            fields = ["transaction_number", "name", "price", "quantity", "type", "trade_quantity"]
            writer = csv.DictWriter(csvfile, fields)
            writer.writeheader()
            for transaction in self.transactions:
                writer.writerow(transaction)
    
    # return the stockInfo of the transaction
    def trade(self, transaction: dict) -> int:
        with self.lock:
            self.transaction_number += 1
            transaction["transaction_number"] = self.transaction_number
            self.transactions.append(transaction)
            if (self.transaction_number % 50 == 0):
                self.saveToDisk()
            return self.transaction_number
        
    # return the stockInfo of the transaction
    def trade_nolock(self, transaction: dict) -> int:
        self.transaction_number += 1
        transaction["transaction_number"] = self.transaction_number
        self.transactions.append(transaction)
        if (self.transaction_number % 50 == 0):
            self.saveToDisk()
        return self.transaction_number