# Design Document
## Part 1
### How To Run
We use docker-compose to run the service:
```cmd
cd src/part1 && docker-compose up
```
(On linux machine you might need to use `sudo docker-compose up` to run it)

### Overview
1. We use the Flask framework to implement the functions in lab2.
2. Caching is achieved through an in-memory cache in the front-end service. When a ("GET") stock query request arrives, the front-end service first checks its cache to see if it can serve the request from there. If the request is not in the cache, it forwards the request to the catalog service and caches the result returned by the catalog service.
3. To maintain cache consistency, the catalog service sends invalidation requests to the front-end service after each trade. These invalidation requests cause the front-end service to remove the corresponding stock from its cache, ensuring that the cache is always up-to-date.


### Components
#### FRONTEND

The app.py file contains a Flask web application that handles incoming requests and sends responses back to clients. It defines two endpoints: /stockName/<name> and /orders/.

The /stockName/<name> endpoint accepts either a "GET" or "DELETE" request with a stock name as a parameter. For "GET" requests, it returns information about the stock, including its remaining quantity and current price. For "DELETE" requests, it removes the cached data associated with the stock name in the requests.

The /orders/ endpoint accepts a "POST" request with a JSON payload that contains information about the order, including whether it is a buy or sell order, the name of the stock, and the quantity to trade. If the trade is successful, the endpoint stores the information about the updated stock, including its remaining quantity, current price, and the amount traded.

#### ORDER
The order service is identical to the one in Lab2. 

The /orders/ endpoint accepts a "POST" request with a JSON payload that contains information about the order, including whether it is a buy or sell order, the name of the stock, and the quantity to trade. If the trade is successful, the endpoint returns information about the updated stock, including its remaining quantity, current price, and the amount traded. It has a similar interface compared to frontend and it redirect the request to CATALOG service.

#### CATALOG
The app.py and Catalog.py, which together implement a basic stock market service.

The Catalog.py file contains a Catalog class that represents the stock market. It initializes a list of stocks with their respective names, prices, and quantities. It provides methods for looking up the stock information and for executing trades. The loadFromDisk and saveToDisk methods allow the class to read and write stock information to a CSV file on disk. The results are saved to disk periodically and on server exit.

## PART 2 and PART 3
### How To Run
We use docker-compose to run the service:
```cmd
cd src/part2 && docker-compose up
```
(On linux machine you might need to use `sudo docker-compose up` to run it)

You can use the script in `src/client/client.py` to benchmark the server on client machine.

### Overview
1. We use the Flask framework to implement the functions in lab2.
2. Caching is achieved through an in-memory cache in the front-end service. When a ("GET") stock query request arrives, the front-end service first checks its cache to see if it can serve the request from there. If the request is not in the cache, it forwards the request to the catalog service and caches the result returned by the catalog service.
3. To maintain cache consistency, the catalog service sends invalidation requests to the front-end service after each trade. These invalidation requests cause the front-end service to remove the corresponding stock from its cache, ensuring that the cache is always up-to-date.
4. Compared to Part1, we additionally implement replication logic in ORDER services. We replica the order service on three container instances. 
6. We use two step commits to ensure consistancy across the replicas. For every request, the leader node sends the order log to the other replicas.
The leader node checks if more than half of the replicas (>=2 in this case) have successfully received the order log. If not, the leader node roll back the transaction and report failure. Otherwise, the leader node reports the transaction number to the frontend.
7. The replicas check if the logs are consistent with the leader node when a new order request comes in, if not a synchronization opeartion will be performed.
8. The FRONTEND elects a leader node when there is no leader or the previous leader is not responding and sends the requests to the leader node. We elects the leader with the highest transaction number. If there is a tie, we elect the leader node with higher replica id.
9. The FRONTEND service also keeps track of the highest transaction number it has received from the ORDER service. We use this information to rollback CATALOG state if the leader node is crushed when some transaction has been commited in the catalog service without sending back to the frontend.

### Components
#### FRONTEND
The `frontend/app.py` file contains a Flask web application that handles incoming requests and sends responses back to clients. 

It defines two endpoints: /stockName/<name> and /orders/.

The /stockName/<name> endpoint accepts either a "GET" or "DELETE" request with a stock name as a parameter. For "GET" requests, it returns information about the stock, including its remaining quantity and current price. For "DELETE" requests, it removes the cached data associated with the stock name in the requests.

The /orders/ endpoint accepts a "POST" request with a JSON payload that contains information about the order, including whether it is a buy or sell order, the name of the stock, and the quantity to trade. If the trade is successful, the endpoint returns information about the updated stock, including its remaining quantity, current price, and the amount traded.

#### ORDER
It defines five endpoints: 
- /orders/
- /replica_orders/
- /synchonize/
- /ping/
- /elect/

The /orders/ endpoint accepts a "POST" request with a JSON payload that contains information about the order, including whether it is a buy or sell order, the name of the stock, and the quantity to trade. Only the leader node replies to the request through this URL. If the trade is successful, the endpoint stores the information about the updated stock, including its remaining quantity, current price, and the amount traded.

The /replica_orders/ endpoint accepts a "POST" request with a JSON payload that contains information about the transaction, including whether it is a buy or sell order, the name of the stock, the quantity to trade, and the remaining quantity. Only replicas receives through this URL. 
It checks if the order's local transaction number is in synchronize with the leader's transacion number, if not a synchronize operation will be triggered.

The /synchronize/ endpoint accepts a "POST" or a "GET" request. 
The leader node only receives "GET" request which allows it to send its local order log to other replicas.
The replica nodes only receives "POST" request, which allows them to synchronize with the leader node using the JSON payload sends alone the request. 

The /ping/ endpoint accepts a "GET" request and returns the transaction number. It is used by the frontend to identify nodes that are still alive.

The /elect/ endpoint accepts a "POST" request. The makes the replica who receive the request becomes the new leader node. 
The new leader will check if any rollback operation needs to be performed. 

#### CATALOG
The Catalog.py file contains a Catalog class that represents the stock market. It initializes a list of stocks with their respective names, prices, and quantities. It provides methods for looking up the stock information and for executing trades. The loadFromDisk and saveToDisk methods allow the class to read and write stock information to a CSV file on disk. The results are saved to disk periodically and on server exit.
It has three end points:
- /stockName/<name>
- /orders/
- /rollback/

The /stockName/<name> endpoint accepts either a "GET" request with a stock name as a parameter. It returns information about the stock, including its remaining quantity and current price. 

The /orders/ endpoint accepts a "POST" request with a JSON payload that contains information about the order, including whether it is a buy or sell order, the name of the stock, and the quantity to trade. Only the leader node replies to the request through this URL. If the trade is successful, the endpoint returns the information about the updated stock, including its remaining quantity, current price, and the amount traded.

The /rollback/ endpoints accepts a "POST" request with a JSON payload that contains the transactions that need to be rollback. The CATALOG service then redo these transactions. 

### PART4
We deployed our code to an m5a.large instance.

Deployment is straight forward on AWS since we use docker-compose to simply the process. 
The two step you need to take is:
1. open port "8080" for incoming requests. 
2. install "docker-compose" 
```cmd
cd src/part3 && sudo docker-compose up
```
