[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-24ddc0f5d75046c5622901739e7c5dd533143b0c8e959d652212380cedb1ea36.svg)](https://classroom.github.com/a/9leuiy3v)
Compsci 677: Distributed and Operating Systems

Spring 2023

# Lab 3: Asterix and Double Trouble  --  Replication, Caching, and Fault Tolerance

## Goals and Learning Outcomes

The lab has the following learning outcomes with regard to concepts covered in class.

* Learn about caching, replication, and consistency.
* Learn about the concepts of fault tolerance and high availability.
* Learn about how to deploy your application on the cloud.

## Information about your submission

1. Name and email: add your name and email here.
2. Team member name and email: add team member info. say none if this is a solo submission
3. Number of late days used for this lab: say zero if none used
4. Number of late days used so far including this lab: say zero if none used.

## Instructions

1. You may work in groups of two for this lab. If you decide to work in groups, you should briefly
   describe how the work is divided between the two team members in your README file. Be sure to
   list the names of all team members at the top of this README file.
2. You can use either Python or Java for this assignment. You may optionally use C++, but TA support
   for C++ issues will be limited. For this lab you may use different languages for different
   microservices if you want.
3. Do's and don'ts:
   * discuss lab with other students: allowed
   * use of AI tools: allowed with attribution (be sure to read the policy in course syllabus)
   * use code from others/Internet/friends/coders for hire: disallowed
   * ask TAs for clarifications/help: always allowed

## Lab Description

The Gauls have really taken to stock trading and trading has become their village pass time. To ensure 
high performance and tolerance to failures, they have decided to adopt modern design practices. 

This project is based on lab 2. You can reuse some of the code you wrote in lab 2 if you want. Your goal 
is to help the Gauls by adding caching, replication, and fault tolerance to the stock bazaar application that were
implemented in the previous labs. Here are some basic requirements:

1.  The stock bazaar application consists of three microservices: a front-end service, a catalog
    service, and an order service.

2.  The front-end service exposes the following REST APIs as they were defined in lab2:

    *   `GET /stocks/<stock_name>`
    *   `POST /orders`

    In addition, the front-end service will provide a new REST API that allows clients to query
    existing orders:

    *   `GET /orders/<order_number>`

        This API returns a JSON reply with a top-level `data` object with the four fields: `number`,
        `name`, `type`, and `quantity`. If the order number doesn't exist, a JSON reply with a
        top-level `error` object should be returned. The `error` object should contain two fields:
        `code` and `message`

    Since in this lab we will focus on higher level concepts, you can use a web framework like
    [`Django`](https://github.com/django/django), [`Flask`](https://github.com/pallets/flask),
    [`Spark`](https://github.com/perwendel/spark) to implement your front-end service. You can also
    reuse the code you wrote in lab 2 if you prefer.

3.  Like in lab 2, you can decide the interfaces used between the microservices. Each microservice
    still need to be able to handle requests concurrently. You can use any concurrency models
    covered in class.

4.  Add some variety to the stock offering by initializing your catalog with at least 10 different
    stocks. Each stock should have an initial volume of 100.

5.  The client first queries the front-end service with a random stock, then it will make a
    follow-up trade request with probability `p` (make `p` an adjustable variable). You can
    decide whether the stock query request and the trade request use the same connection. The
    client will repeat the aforementioned steps for a number of iterations, and record the order
    number and order information if a trade request was successful. Before exiting, the client will
    retrieve the order information of each order that was made using the order query request, and
    check whether the server reply matches the locally stored order information.

## Part 1: Caching

In this part we will add caching to the front-end service to reduce the latency of the stock query
requests. The front-end server starts with an empty in-memory cache. Upon receiving a stock query
request, it first checks the in-memory cache to see whether it can be served from the cache. If not,
the request will then be forwarded to the catalog service, and the result returned by the catalog
service will be stored in the cache.

Cache consistency needs to be addressed whenever a stock is bought or sold. You should implement a
server-push technique: the catalog server sends invalidation requests to the front-end server after each
trade. The invalidation requests cause the front-end service to remove the corresponding stock from
the cache.

## Part 2: Replication

To make sure that our stock bazaar doesn't lose any order information due to crash failures, we want
to replicate the order service. When you start the stock bazaar application, you should first start
the catalog service. Then you start three replicas of the order service, each with a unique id
number and its own database file. There should always be 1 leader node and the rest are follower
nodes. You do **NOT** need to implement a leader election algorithm. Instead the front-end service
will always try to pick the node with the highest id number as the leader.

When the front-end service starts, it will read the id number and address of each replica of the
order service (this can be done using configuration files/environment variables/command line
parameters). It will ping (here ping means sending a health check request rather than the `ping`
command) the replica with the highest id number to see if it's responsive. If so it will notify all
the replicas that a leader has been selected with the id number, otherwise it will try the replica
with the second highest id number. The process repeats until a leader has been found.

When a trade request or an order query request arrives, the front-end service only forwards the
request to the leader. In case of a successful trade (a new order number is generated), the leader
node will propagate the information of the new order to the follower nodes to maintain data
consistency.

## Part 3: Fault Tolerance

In this part you will handle failures of the order service. In this lab you only need to deal with
crash failure tolerance rather than Byzantine failure tolerance.

First We want to make sure that when any replica crashes (including the leader), trade requests and
order query requests can still be handled and return the correct result. To achieve this, when the
front-end service finds that the leader node is unresponsive, it will redo the leader selection
algorithm as described in [Part2](#part-2-replication).

We also want to make sure that when a crashed replica is back online, it can synchronize with the
other replicas to retrieve the order information that it has missed during the offline time. When a
replica comes back online from a crash, it will look at its database file and get the latest order
number that it has and ask the other replicas what orders it has missed since that order number.

## Part 4: Testing and Evaluation with Deployment on AWS

First, write some simple test cases to verify that your code works as expected. You should test both
each individual microservice as well as the whole application. Submit your test cases and test
output in a test directory.

Next, deploy your application on an `m5a.xlarge` instance in the `us-east-1` region on AWS. We will
provide instructions on how to do this in lablet 5. Run 5 clients on your local machine. Measure
the latency seen by each client for different types of requests. Change the probability p of a
follow up trade request from 0 to 80%, with an increment of 20%, and record the result for each p
setting. Make simple plots showing the values of p on the X-axis and the latency of different types
of request on the y-axis. Also do the same experiments but with caching turned off, estimate how
much benefits does caching provide by comparing the results.

Finally, simulate crash failures by killing a random order service replica while the client is
running, and then bring it back online after some time. Repeat this experiment several times and
make sure that you test the case when the leader is killed. Can the clients notice the failures?
(either during order requests or the final order checking phase) or are they transparent to the
clients? Do all the order service replicas end up with the same database file?

## What to submit

Your solution should contain source code for both parts separately inside the `src` directory. Then
under the directory for each part, you should have a separate folder for each
component/microservice, e.g., a `client` folder for client code, a `front-end` folder for the
front-end service, etc.

A short README file on how to run your code. Include build/make files if you created any, otherwise
the README instructions on running the code should provide details on how to do so.

Submit the following additional documents inside the docs directory. 1) A Brief design document (1
to 2 pages) that explains your design choices (include citations, if you used Internet
sources), 2) An Output file (1 to 2 pages), showing sample output or screenshots to indicate that your
program works, and 3) An Evaluation doc (2 to 3 pages), for part 4 showing plots and making
observations.

## Grading Rubric

Parts 1-3 accounts for 70% of the total lab grade:

* Code should have inline comments (5%).
* GitHub repo should have adequate commits and meaningful commit messages (5%).
* Source code should build and work correctly (40%).
* A descriptive design doc should be submitted (15%).
* An output file should be included (5%).

Part 4 accounts for 30% of the total lab grade:

* Should provide steps in your eval docs about how you deployed your application on AWS. Include
  scripts in your repo if needed (5%).
* An eval doc with measurement results and plots (15%).
* Analysis of the results and answers to the questions in part 3 (10%).

## References

1. Learn about Gaul (the region) https://en.wikipedia.org/wiki/Gaul and the Gauls (the people) https://en.wikipedia.org/wiki/Gauls
2. Learn about the comics that these labs are based on https://en.wikipedia.org/wiki/Asterix
3. Learn about Web framework such as Flask (python) https://flask.palletsprojects.com/en/2.2.x/  There are many python and java web frameworks - choose carefully if you decide to use one.
4. Learn about model-view-controller (MVC) paradigm of writing web apps using frameworks https://en.wikipedia.org/wiki/Model–view–controller
