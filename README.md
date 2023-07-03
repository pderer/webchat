# Multi-user Single-room Realtime Webchat
Realtime chat was implemented using WebSocket and asynchronous programming(asyncio). If you push connect button, you get random name to chat another user. Connected, disconnected, and chatting messages are displayed. Enjoy Realtime chatting!

<img width="385" alt="스크린샷 2023-07-03 11 16 27" src="https://github.com/pderer/webchat/assets/59244452/1e7e266e-bb12-46f4-8e5a-643fcec2d9a6">

* * *
## Table of Contents
* [How It Works](#how-it-works)
    * [aiohttp](#aiohttp)
    * [redis-py](#redis-py)
    * [asyncio](#asyncio)
* [Installation](#installation)
    * [docker-compose](#docker-compose)
* * *
## How It Works
Webchat is implemented by WebSocket protocol. If the server runs in one python process, we can share the state using the [aiohttp.webApplication object.](https://docs.aiohttp.org/en/stable/web_advanced.html#application-s-config) However, if we extend server, we need another data structure to share the state of all servers.
Redis is used to share the state when the server expands. And to implement real time request/response, we used asynchronous programming through asyncio.
### aiohttp
To implement asynchronous request, response and websocket protocol, I used [aiohttp](https://docs.aiohttp.org/en/stable/index.html) framework.
### redis-py
To share the state of all servers, I used [redis-py](https://redis-py.readthedocs.io/en/stable/). In particular, redis [pub/sub](https://redis-py.readthedocs.io/en/stable/examples/asyncio_examples.html#Pub/Sub-Mode) mode, which is specialized in message delivery, was used.
### asyncio
If redis message publishing/subscribing process (I/O) is implemented synchronously, performance is low. Realtime chatting was implemented by setting redis pub/sub as a task and using [asyncio.createtask](https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task) to improve the performance of the I/O process asynchronously using eventloop.
## Installation
Built a self-contained [Docker](https://www.docker.com) image that runs webchat app.
### docker-compose
Used [docker-compose](https://docs.docker.com/compose/) to run python and redis together.

1. clone this project.
```
$ git clone https://github.com/pderer/webchat.git
```
2. docker compose.
```
$ docker-compose up --build
```
3. connect URL and enjoy realtime chat. \
http://localhost:8080