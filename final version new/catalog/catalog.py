import os, csv, threading

class Catalog:
    def __init__(self, path:str) -> None:
        self.lock=threading.Lock()
        self.stocks=dict()
        self.path=path
        if path and os.path.exists(path):
            self.load_from_disk()
        else:
            self.init_stocks()
        
    # init the stocks
    def init_stocks(self) -> None:
        GameStart = {
            "name": "GameStart",
            "price" : 15.99,
            "quantity": 100,
            "trading_volume":0
        }
        
        FishCo = {
            "name": "FishCo",
            "price": 9.99,
            "quantity": 100,
            "trading_volume":0
        }
        
        BoarCo = {
            "name": "BoarCo",
            "price": 5.99,
            "quantity": 100,
            "trading_volume":0
        }
        
        MenhirCo = {
            "name": "MenhirCo",
            "price": 20.99,
            "quantity": 100,
            "trading_volume":0
        }
        
        Cici = {
            "name": "Cici",
            "price": 10.99,
            "quantity": 100,
            "trading_volume":0
        }
        
        GameStart2 = {
            "name": "GameStart2",
            "price" : 15.99,
            "quantity": 100,
            "trading_volume":0
        }
        
        FishCo2 = {
            "name": "FishCo2",
            "price": 9.99,
            "quantity": 100,
            "trading_volume":0
        }
        
        BoarCo2 = {
            "name": "BoarCo2",
            "price": 5.99,
            "quantity": 100,
            "trading_volume":0
        }
        
        MenhirCo2 = {
            "name": "MenhirCo2",
            "price": 20.99,
            "quantity": 100,
            "trading_volume":0
        }
        
        Cici2 = {
            "name": "Cici2",
            "price": 10.99,
            "quantity": 100,
            "trading_volume":0
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

    # read data from csv file on disk
    def load_from_disk(self) -> None:
        self.init_stocks()
        print("Load Catalog from disk: ", self.path)
        try:
            with open(self.path, "r+") as csvfile:
                reader=csv.DictReader(csvfile)
                for row in reader:
                    stock_name = row["name"]
                    price = row["price"]
                    quantity = row["quantity"]
                    trading_volume=row["trading_volume"]

                self.stocks[stock_name]={
                    "name":stock_name,
                    "price":price,
                    "quantity":int(quantity),
                    "trading_volume":int(trading_volume)
                }            
        except Exception as e:
            print(e)
        
    # save stock infos to a csv file 
    def save_to_disk(self) -> None:
        print("Saving stocks to disk: ", self.path)
        with open(self.path, "w+") as csvfile:
            fields=["name", "price", "quantity", "trading_volume"]
            writer=csv.DictWriter(csvfile, fields)
            writer.writeheader()
            for stock_name, stock_info in self.stocks.items():
                price=stock_info["price"]
                quantity=stock_info["quantity"]
                trading_volume=stock_info["trading_volume"]
                writer.writerow({
                    "name":stock_name,
                    "price":price,
                    "quantity":quantity,
                    "trading_volume":trading_volume
                })
    # return the remaining quantity and current price of the stock
    def look_up(self, stock_name:str) -> dict | None:
        if stock_name in self.stocks:
            with self.lock:
                return self.stocks[stock_name]
        else:
            return None
        
    def trade(self, stock_name:str, to_but:bool, trade_quantity: int) -> dict | None:
        if to_but==True:
            with self.lock:
                exist_vol = self.stocks[stock_name]["quantity"]
                if trade_quantity>exist_vol:
                    return None
                else:
                    new_vol=exist_vol-trade_quantity
                    self.stocks[stock_name]["quantity"]=new_vol
                    self.stocks[stock_name]["trading_volume"]+=trade_quantity
                    return self.stocks[stock_name]
        else:
            with self.lock:
                exist_vol = self.stocks[stock_name]["quantity"]
                new_vol=exist_vol+trade_quantity
                self.stocks[stock_name]["quantity"]=new_vol
                self.stocks[stock_name]["trading_volume"]+=trade_quantity
                return self.stocks[stock_name]
    
    def exist(self, stock_name) -> bool:
        return stock_name in self.stocks
    

    def rollback(self, transaction_number, transactions) -> None:
        with self.lock:
            for transaction in reversed(transactions):
                stock_name=transaction["name"]
                trade_quantity=int(transaction["quantity"])
                i = int(transaction_number["transaction_number"])
                if i>transaction_number:
                    if transaction["type"] == "sell":
                        # trade is to sell so to rollback it we need to perform buy operation
                        exist_vol = self.stocks[stock_name]["quantity"]
                        new_vol = exist_vol - trade_quantity
                        self.stocks[stock_name]["quantity"] = new_vol
                        self.stocks[stock_name]["trading_volume"]-=trade_quantity
                        assert(new_vol >= 0)
                    else:
                        # trade is to buy so to rollback it we need to perform sell operation
                        exist_vol = self.stocks[stock_name]["quantity"]
                        new_vol = exist_vol + trade_quantity
                        self.stocks[stock_name]["quantity"] = new_vol
                        self.stocks[stock_name]["trading_volume"]-=trade_quantity
                        assert(new_vol >= 0)




