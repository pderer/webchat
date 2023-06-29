import asyncio
import logging
import json

import aiohttp
import aiohttp_jinja2
from aiohttp import web
from faker import Faker

log = logging.getLogger(__name__)


def get_random_name():
    fake = Faker()
    return fake.name()


async def reader(channel, ws, name):
    while True:
        # print("wow")
        message = await channel.get_message(ignore_subscribe_messages=True)
        if message is not None:
            print("from reader:", message["data"].decode())
            print("ready to send")
            await ws.send_json({'action': 'sent', 'name': name, 'text': message["data"].decode()})


async def index(request):
    r = request.app['redis']
    ws_current = web.WebSocketResponse()
    ws_ready = ws_current.can_prepare(request)
    if not ws_ready.ok:
        return aiohttp_jinja2.render_template('index.html', request, {})

    await ws_current.prepare(request)

    name = get_random_name()
    log.info('%s joined.', name)

    await ws_current.send_json({'action': 'connect', 'name': name})

    # TODO : 현재 ws가 connect 되었다는 메세지를 연결된 웹소켓에 뿌려줘야 함,
    # join_json = {
    #     "action": "join",
    #     "name": name
    # }
    # async with r.pubsub() as pubsub:
    #     await r.publish("channel:1", json.dumps(join_json))
    #     await pubsub.subscribe("channel:1")

    # example
    # sub = await r.create_redis_pool("redis://localhost")
    # pub = await r.create_redis_pool("redis://localhost")

    # ch, *_ = await sub.subscribe("channel:1")

    # TODO : 현재 웹소켓이 채널에 subscribe하고 채널에 메세지를 publish해야 함
    async with r.pubsub() as pubsub:
        await pubsub.subscribe("channel:1")
        future = asyncio.create_task(reader(pubsub, ws_current, name))

        # await r.publish("channel:1", "hello")
        while True:
            msg = await ws_current.receive()
            print(msg)
            await r.publish("channel:1", msg.data)
            # await future
        # async for msg in ws_current:
        #     print(msg.data)
        #     await r.publish("channel:1", msg.data)
        # await future

    # for ws in request.app['websockets'].values():
    #     await ws.send_json({'action': 'join', 'name': name})
    # request.app['websockets'][name] = ws_current

    # while True:
    #     msg = await ws_current.receive()

    #     if msg.type == aiohttp.WSMsgType.text:
    #         for ws in request.app['websockets'].values():
    #             if ws is not ws_current:
    #                 await ws.send_json(
    #                     {'action': 'sent', 'name': name, 'text': msg.data}
    #                 )
    #     else:
    #         break

    # del request.app['websockets'][name]
    # log.info('%s disconnected.', name)
    # for ws in request.app['websockets'].values():
    #     await ws.send_json({'action': 'disconnect', 'name': name})

    return ws_current
