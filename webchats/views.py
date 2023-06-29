import asyncio
import logging

import aiohttp
import aiohttp_jinja2
from aiohttp import web
from faker import Faker
import redis.asyncio as redis

log = logging.getLogger(__name__)


def get_random_name():
    fake = Faker()
    return fake.name()


async def reader(channel, name, ws_current):
    while True:
        msg = await channel.get_message(ignore_subscribe_messages=True)

        if msg is not None:
            # TODO : if statement
            if msg["type"] == "sent":
                # TODO
                await ws_current.send_json(
                    {'action': 'sent', 'name': name,
                        'text': msg["data"].decode()}
                )
            elif msg["type"] == "join":
                await ws_current.send_json(
                    {'action': 'join', 'name': msg["data"].decode()}
                )
            elif msg["type"] == "disconnect":
                await ws_current.seng_json(
                    {'action': 'disconnect', 'name': msg["data"].decode()}
                )
                break


async def index(request):
    ws_current = web.WebSocketResponse()
    ws_ready = ws_current.can_prepare(request)
    if not ws_ready.ok:
        return aiohttp_jinja2.render_template('index.html', request, {})

    await ws_current.prepare(request)

    name = get_random_name()
    log.info('%s joined.', name)

    await ws_current.send_json({'action': 'connect', 'name': name})

    # Pub/Sub
    connection = redis.from_url("redis://localhost:6379")
    await connection.publish("channel:join", name)
    async with connection.pubsub() as pubsub:
        await asyncio.create_task(reader(pubsub, name, ws_current))

    async with connection.pubsub() as pubsub:
        await pubsub.subscribe("channel:join", "channel:sent", "channel:disconnect")
        future = asyncio.create_task(reader(pubsub, name, ws_current))

        await connection.publish("channel:sent", ws_current.receive().data)
        await future

        future_disconnect = asyncio.create_task(
            reader(pubsub, name, ws_current))
        await connection.publish("channel:disconnect", name)
        await future_disconnect

    log.info('%s disconnected.', name)

    for ws in request.app['websockets'].values():
        await ws.send_json({'action': 'join', 'name': name})
    request.app['websockets'][name] = ws_current

    while True:
        msg = await ws_current.receive()

        if msg.type == aiohttp.WSMsgType.text:
            for ws in request.app['websockets'].values():
                if ws is not ws_current:
                    await ws.send_json(
                        {'action': 'sent', 'name': name, 'text': msg.data}
                    )
        else:
            break

    del request.app['websockets'][name]
    log.info('%s disconnected.', name)
    for ws in request.app['websockets'].values():
        await ws.send_json({'action': 'disconnect', 'name': name})

    return ws_current
