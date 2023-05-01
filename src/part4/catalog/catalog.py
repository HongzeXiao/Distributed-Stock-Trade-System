import os, csv, threading

# Catalog Service
# if path is specified it will save the changes to
# a csv file when the server terminates
class Catalog:
    def __init__(self, path: str) -> None:
        self.lock = threading.Lock()
        self.path: str = path
        self.stocks: dict = dict()
        if path != None:
            self.loadFromDisk()
        else:
            self.init()
            
    # initialize stocks their quantity and price
    def init(self):
        GameStart = {
            "name": "GameStart",
            "price" : 15.99,
            "quantity": 100,
        }
        
        FishCo = {
            "name": "FishCo",
            "price": 9.99,
            "quantity": 100,
        }
        
        BoarCo = {
            "name": "BoarCo",
            "price": 5.99,
            "quantity": 100,
        }
        
        MenhirCo = {
            "name": "MenhirCo",
            "price": 20.99,
            "quantity": 100,
        }
        
        Cici = {
            "name": "Cici",
            "price": 10.99,
            "quantity": 100,
        }
        
        GameStart2 = {
            "name": "GameStart2",
            "price" : 15.99,
            "quantity": 100,
        }
        
        FishCo2 = {
            "name": "FishCo2",
            "price": 9.99,
            "quantity": 100,
        }
        
        BoarCo2 = {
            "name": "BoarCo2",
            "price": 5.99,
            "quantity": 100,
        }
        
        MenhirCo2 = {
            "name": "MenhirCo2",
            "price": 20.99,
            "quantity": 100,
        }
        
        Cici2 = {
            "name": "Cici2",
            "price": 10.99,
            "quantity": 100,
        }
        self.stocks["GameStart"] = GameStart
        self.stocks["FishCo"] = FishCo
        self.stocks["BoarCo"] = BoarCo
        self.stocks["MenhirCo"] = MenhirCo
        self.stocks["Cici"] = Cici
        self.stocks["GameStart2"] = GameStart2
        self.stocks["FishCo2"] = FishCo2
        self.stocks["BoarCo2"] = BoarCo2
        self.stocks["MenhirCo2"] = MenhirCo2
        self.stocks["Cici2"] = Cici2
        
    # return the remaining quantity and current price of the stock
    def lookUp(self, stockName: str) -> dict | None:
        if stockName in self.stocks:
            with self.lock:
                return self.stocks[stockName]
        else:
            return None
    
    # read data from csv file on disk
    def loadFromDisk(self)->None:
        self.init()
        print("Load Catalog from disk: ", self.path)
        try:
            with open(self.path, 'r+') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    stockName = row["name"]
                    price = row["price"]
                    quantity = row["quantity"]
                    self.stocks[stockName] = {
                        "name": stockName,
                        "price" : price,
                        "quantity": int(quantity),
                    }
            print("loaded stocks", self.stocks)
        except Exception as e:
            print(e)
    # save stock infos to a csv file 
    def saveToDisk(self) -> None:
        print("Saving stocks to disk: ", self.path)
        with open(self.path, 'w+') as csvfile:
            fields = ["name", "price", "quantity"]
            writer = csv.DictWriter(csvfile, fields)
            writer.writeheader()
            for stockName, stockInfo in self.stocks.items():
                price = stockInfo["price"]
                quantity = stockInfo["quantity"]
                writer.writerow({
                    "name": stockName,
                    "price": price,
                    "quantity": quantity,
                })
            
        
    # return the stockInfo of the transaction
    def trade(self, stockName:str, tobuy:bool, trade_quantity: int) -> dict | None:
        if tobuy == True:
            with self.lock:
                exist_vol = self.stocks[stockName]["quantity"]
                if trade_quantity > exist_vol:
                    return None
                else:
                    new_vol = exist_vol - trade_quantity
                    self.stocks[stockName]["quantity"] = new_vol
                    return self.stocks[stockName]
        else:
            # trade is to sell
            with self.lock:
                exist_vol = self.stocks[stockName]["quantity"]
                new_vol = exist_vol + trade_quantity
                self.stocks[stockName]["quantity"] = new_vol
                return self.stocks[stockName]
    
    def exist(self, stockName)->bool:
        return stockName in self.stocks

    def rollback(self, transaction_number, transactions) -> None:
        with self.lock:
            for transaction in reversed(transactions):
                stockName = transaction["name"]
                trade_quantity = int(transaction["trade_quantity"])
                i = int(transaction["transaction_number"])
                if (i <= transaction_number):
                    if transaction["type"] == "sell":
                        # trade is to sell so to rollback it we need to perform buy operation
                        exist_vol = self.stocks[stockName]["quantity"]
                        new_vol = exist_vol - trade_quantity
                        self.stocks[stockName]["quantity"] = new_vol
                        assert(new_vol >= 0)
                    else:
                        # trade is to buy so to rollback it we need to perform sell operation
                        exist_vol = self.stocks[stockName]["quantity"]
                        new_vol = exist_vol + trade_quantity
                        self.stocks[stockName]["quantity"] = new_vol
                        assert(new_vol >= 0)
        