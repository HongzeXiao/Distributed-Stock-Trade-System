[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-c66648af7eb3fe8bc4f294546bfd86ef473780cde1dea487d3c4ff354943c9ae.svg)](https://classroom.github.com/online_ide?assignment_repo_id=10482538&assignment_repo_type=AssignmentRepo)
Compsci 677: Distributed and Operating Systems

Spring 2023

# Lab 2: Asterix and the Microservice Stock Bazaar


## Goals and Learning Outcomes

This lab has the following learning outcomes with regards to concepts covered in class.

1. Design distributed server applications using a multi-tier architecture and microservices.
2. Design virtualized applications.
3. Design interfaces for web applications.

The lab also has the following learning outcomes with regards to practice and modern technologies.

1. Learn how to implement a REST API server.
2. Learn to measure the performance of a distributed application.
3. Learn how to use Docker to containerize your micro-service, and learn to manage an application
   consisting of multiple containers using Docker Compose.
4. Learn how to test a distributed application.

## Information about your submission
1. Name and email: add your name and email here. 
2. Team member name and email: add team member info. say none if this is a solo submission
3. Number of late days used for this lab: say zero if none used
4. Number of late days used so far including this lab: say zero if none used.


## Instructions

1. You may work in groups of two for this lab. If you decide to work in groups, you should briefly
    describe how the work is divided between the two team members in your README file. Be sure to
    list the names of all team members at the top of this README file.

2. You can use either python or Java for this assignment. You may optionally use C++ but TA support
    for C++ issues will be limited. For this lab you may use different languages for different
    microservices if you want.

3. Do's and don'ts:
   - discuss lab with other students: allowed
   - use of AI tools: allowed with attribution (be sure to read policy in course syllabus)
   - use code from others/Internet/friends/coders for hire: disallowed
   - ask TAs for clarifications/help: always allowed

## Lab Description

At the very beginning the bazaar served the Gauls well. However, with the growing popularity of meme
stock trading, there were soon too many trades to be handled by Obelix's Single Server. After a town
meeting, Vitalstatistix, the village chief, decreed that the stock bazaar will adopt a microservices
architecture so that the stock bazaar can be scaled up/down dynamically according to trading
activity.

You are tasked with rewriting the stock bazaar application that we implemented in the first lab.
Instead of using a monolithic server, we will now employ a two-tier design (a front-end tier and a
back-end tier)  for the stock bazaar using microservices at each tier. The front-end is implemented
as a single microservice, while the back-end is implemented as two separate services: a stock catalog
service and an stock order service.

Note: You are not required to use any code from Lab 1, but please feel free to use any parts of lab
1 for lab 2 if it is useful to you.

## Part 1: Implement Your Two-Tiered Stock Bazaar as Microservices

### Front-end Service

The clients can communicate with the front-end service using the following two HTTP-based REST APIs.
In a HTTP-based REST API, a client sends its request as an HTTP request and receives a reply as a
HTTP response. We will use HTTP GET and POST requests to send requests to the server. The server
supports Lookup and Trade requests, like in Lab 1, but these are sent as HTTP REST requests as
follows:

1. `GET /stocks/<stock_name>`

    This API is used to look up the details of a stock. If the lookup request is successful, the
    server should return a JSON reply with a top-level `data` object. Similar to lab 1 the `data`
    object has three fields: `name`, `price`, and `quantity`. For instance,

    ```json
    {
        "data": {
            "name": "GameStart",
            "price": 15.99,
            "quantity": 100
        }
    }
    ```

    If things go wrong, for example if the stock name provided by the client does not exist, the
    front-end service should return a JSON reply with a top-level `error` object. The `error` object
    should contain two fields: `code` (for identifying the type of the error) and `message` (human
    readable explanation of what went wrong). For instance,

    ```json
    {
        "error": {
            "code": 404,
            "message": "stock not found"
        }
    }
    ```

2. `POST /orders`

    This API will try to place an order for a certain stock. The client should attach a JSON body to
    the POST request to provide the information needed for the order (`name` and `quantity`).

    ```json
    {
        "name": "GameStart",
        "quantity": 1,
        "type": "sell"
    }
    ```

    If the order is placed successfully, the front-end service returns a JSON object with a
    top-level `data` object, which only has one field named `transaction_number`.

    ```json
    {
        "data": {
            "transaction_number": 10
        }
    }
    ```

    In case of error, the front-end service returns a JSON reply with a top-level `error` object,
    which has two fields, `code` and `message`, similar to the stock lookup API.

The server should listen to HTTP requests on a socket port  (normally, this would be port 80 for
HTTP, but we suggest using a higher-numbered port since your machine may need admin/root privileges
to listen on port 80). Like before, the server should listen for incoming requests over HTTP and
assign them to a thread pool. You can use any builtin thread pool for servicing client requests.
Alternatively, you can also use a simple thread-per-request model (or more precisely,
thread-per-session)  to create a thread for each new client. The thread should first parse the HTTP
request to extract the GET/POST command. Depending on whether it is a Lookup request or a Trade
request, it should make a request to the Catalog or Order service as discussed below. The response
from this back-end service should be used to construct a json response as shown in the above API and
sent back to the client as a HTTP reply.

**Note that when implementing the front-end service you can NOT use existing web frameworks such as
[`Django`](https://github.com/perwendel/spark), [`Flask`](https://github.com/pallets/flask),
[`Spark`](https://github.com/perwendel/spark), etc.** Web frameworks already implement a lot of the
functionality of lab 2 and provide higher-level abstractions to developer. The goal here is to
understand the details, which is why you need to implement them yourself rather than using a web
framework.

You'll have to handle the HTTP requests directly in your application or you can implement your own
simple web framework (this is actually not as hard as you may think). Languages such as Python and
Java provide HTTP libraries to make this straightforward for you, and you should use them to
implement HTTP clients and the front-end service.

### Catalog Service

The stock catalog service maintains a list of all stocks traded in the stock market. It should also 
maintain the trading volume of each stock and the number of stocks available for sale. When the front-end service 
receives a Lookup request, it will forward the request to the catalog
service. The catalog service needs to maintain the catalog data, both in memory and in a CSV or text
file on disk ("database"). The disk file will persist the state of the catalog. When the service
starts up, it should initialize itself from the database disk file. In production applications, a
real database engine is used for this part, but here we will use a file to maintain the catalog.

While lookup requests will simply read the catalog, trade requests will be sent to the order
service, which will then contact the catalog service to update  the volume of stocks traded in
the catalog. It will also increment or decrement the number of stocks available for sale, depending 
on the type of trade request. These updates should be written out to the catalog on disk (immediately or
periodically, depending on your design). You can initialize the catalog service with a non-zero number of 
stocks of each company available for sale, say 100.

The catalog service is implemented as a server that listens to request from the front-end service or
the order service. The catalog service exposes an internal interface to these two components. As
part of this lab, you should first design the interface (i.e., list of exposed functions and their
inputs/outputs) for the catalog service and clearly describe it in your design doc. You can use  any
mechanism of choice to implement the interface for the catalog (e.g., sockets, RPC (e.g., pyro), RMI
(e.g., java RMI), gRPC, or HTTP REST). You should make a complete design of your API/interface of this service and 
describe how you implemented your interface in the inferfaces section of your design doc.

Like the front-end server, you should employ threads to service incoming request. Since the catalog
can be accessed concurrently by more than one thread, use synchronization to protect reads and
updates to the catalog. While simple locks are acceptable, we suggest using read-write locks for
higher performance.


### Order Service

When the front-end service receives an order request, it will forward the request to the order
service. Obviously the order service still need to interact with the catalog service to complete the
order. Specifically, a buy trade request should succeed only if the remaining quantity of the stock
is greater than the requested quantity, and the quantity should be decremented. A sell trade request
will simply increase the remaining quantity of the stock.

If the order was successful, the order service generates an transaction number and returns it to the
front-end service. The transaction number should be an unique, incremental number, starting from 0.
The order service also need to maintain the order log (including transaction number, stock name,
order type, and quantity) in a persistent manner. Similar to the catalog service, we will just use a
simple CSV or text file on disk as the persistent storage for the database.

Like in the catalog service, you need to first design the interface exposed by your order service
(i.e., list of functions and their input/outputs). You can use any method for front-end to invoke
this interface (e.g., socket, RPC, RMI, REST HTTP). Further, the order service should be threaded
and should use synchronization when writing to the order database file. 


### Client

The client in this lab works in the following way. First it opens a HTTP connection with the
front-end service, then it randomly looks up a stock. If the returned quantity is greater than zero,
with probability $p$ it will send another order request using the same connection. Make $p$ and
adjustable parameter in the range $[0, 1]$ so that you can test how your application performs when
the percentage of order requests changes. A client can make a sequence of lookup and (optional)
trade for each such lookup based on probability $p$. This sequence of requests is called a session.
Your front-end server should use a single thread to handle all requests from the session until the
client closes the HTTP socket connection.  Make sure that the thread pool at the server is large
enough to handle all active client and their sessions without starving.

### Communication

We have specified that the front-end service should provide a REST interface to the client, but have
asked you to design the interfaces exposed by the two backend micro-services.  As noted above, you
can use REST API, RPC, RMI, gRPC, raw sockets, etc.

### Concurrency

It's important that all your microservices can handle requests concurrently. You can use any of the
concurrency models taught in class: thread-per-request, threadpool, async, etc.

## Part 2: Containerize Your Application

In this part, you will first containerize your application code and then learn to deploy all
components as a distributed application  using Docker. If you are not familiar with Docker, be sure
to look at lablet 3, which provides a hands-on tutorial. Also review the references at the end of
this file.

First, create a dockerfile for each of the three microservices that you implemented in part 1.
Verify that they build and run without issue.

After that write a Docker compose file that can bring up (or tear down) all three services using one
`docker-compose up` (or `docker-compose down`) command.

Note that files you write in a Docker container are not directly accessible from the host, and they
will be erased when the container is removed. Therefore, you should mount a directory on the host as
a volume to the **catalog** and **order** services, so that files and output can be persisted after
the containers are removed.

Another thing to notice is that when you use Docker compose to bring up containers it will set up a
new network for all the containers, the containers will have a different IP address in this network
than your host IP address. Therefore, you need to consider how to pass the IP/hostnames to the
services so that they know how to locate other services regardless of whether they are running on
"bare metal" or inside containers. (HINT: you can set environment variables when building a Docker
image or in a Docker compose file).

## Part 3: Testing and Performance Evaluation

In this part, you wil be testing the functionality and performance of your code.

First, write some simple testcases to verify that your code works as expected. Be sure to test the
code and error handling (e.g., by looking up stocks that do not exist or buying stocks that with
quantity greater than the remaining supply). Testing distributed applications is different from
testing a single program. So you should try to test the full application as well as the
micro-services. Write a few different test cases and attach output to show that it worked as
expected. Submit your testcases and the outputs in a test directory.

Second, write some performance/load test to evaluate the performance of your application. Deploy
more than one more client process and have each one make concurrent requests to the server. The
clients should be running on a different machine than the server (use the EdLab, if needed). Measure
the latency seen by the client for different types of requests, such as lookup and trade. You can also
make the request rate from each client configurable by introducing a wait (e.g., sleep) between successive 
requests from a client.

Vary the number of clients from 1 to 5 and measure the latency as the load goes up. Make simple
plots showing number of clients on the X-axis and response time/latency on the Y-axis.

Using these measurements, answer the following questions:

1. Does the latency of the application change with and without Docker containers? Did virtualization
   add any overheads?
2. How does the latency of the lookup requests compare to trade? Since trade requests involve all
   these microservices, while lookup requests only involve two microservices, does it impact the
   observed latency?
3. How does the latency change as the number of clients change? Does it change for different types
   of requests?



## What to Submit

At the top of this README file add the name(s) and UMass email address(es) of all the team members.
Also if you are working in a group, briefly describe how the work is divided.

You solution should contain source code for both parts separately. Inside the `src` directory, you
should have a separate folder for each component/microservice, e.g., a `client` folder for client
code, a `front-end` folder for the front-end service, etc.

The dockerfiles and Docker compose files should be placed under the root folder. Also include a
`build.sh` script that can build all your images. This script should be able to build your images on
Edlab machines.

A short README file on how to run your code. Include build/make files if you created any, otherwise
the README instructions on running the code  should provide details on how to do so.

Submit the following additional documents inside the docs directory. 1) A Brief design document (1
to 2 pages) that explains your design choices (include citations, if you used referred to Internet
sources), 2) An Output file (1 to 2 pages), showing sample output or screenshots to indicate your
program works, and 3) An Evaluation doc (2 to 3 pages), for part 3 showing plots and making
observations.

Submit your testcases in the test directory. Attach sample output of test cases on the docs
directory.

Your GitHub repo is expected to contain many commits with proper commit messages (which is good
programming practice). Use GitHub to develop your lab and not just to submit the final version. We
expect a reasonable number of commits and meaningful commit messages from both members of the group
(there is no "target" number of commits that is expected, just enough to show you are using GitHub
as one should).

## Grading Rubric

1) Part 1 is 50% of the lab grade.

    For full credit:

    * Source code should build and work correctly (25%),
    * Code should have in-line comments (5%),
    * A descriptive design doc should be submitted with full design details (5%),
    * Clear and full descrption of interfaces/API, including inputs and outputs, of each service (5%)
    * An output file should be included (5%),
    * GitHub repo should have adequate commits and meaningful commit messages (5%).

2) Part 2 is 30% of the lab grade.

    For full credit:

    * The dockerfiles should build each microservice successfully (15%),
    * The docker compose file should be able to bring up/tear down the whole application using one
        command (10%),
    * The catalog file and order log file should be persisted after container removal (5%).

3) Part 3 is 20% of the grade.

    For full credit:

    * Eval document should be turned in with measurements for Part 1 and 2 (shown as plots where
      possible and tables otherwise) (10%),
    * Explaining the plots by addressing answers to the 4 questions listed in Part 3 (5%)
    * Test cases and test case output (5%)

As the late policy, will we deduct 10% per day. Medical or COVID exceptions require advanced notice,
and should be submitted through Piazza (use the exceptionRequests folder in Piazza). Three free late
days per group are available for the entire semester. Use them wisely and do not use them up for one
lab by managing your time well.

## References

1. HTTP protocol: https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol
2. Dockerfile reference: https://docs.docker.com/engine/reference/builder/
3. Compose file reference: https://docs.docker.com/compose/compose-file/
4. Docker volumes: https://docs.docker.com/storage/volumes/