import os
frontend_ip = os.getenv("FRONTEND_IP", "http://localhost:8080")
order_ip_1 = os.getenv("ORDER_IP_1", "http://localhost:8081")
order_ip_2 = os.getenv("ORDER_IP_2", "http://localhost:8082")
order_ip_3 = os.getenv("ORDER_IP_3", "http://localhost:8083")
catalog_ip = os.getenv("CATALOG_IP", "http://localhost:8085")

order_ips = [order_ip_1, order_ip_2, order_ip_3]