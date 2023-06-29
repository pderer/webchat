import pickle
import logging

import redis.asyncio as redis
import aiohttp
import aiohttp_jinja2
from aiohttp import web
from faker import Faker

log = logging.getLogger(__name__)


def get_random_name():
    fake = Faker()
    return fake.name()


async def index(request):
    ws_current = web.WebSocketResponse()
    ws_ready = ws_current.can_prepare(request)
    if not ws_ready.ok:
        return aiohttp_jinja2.render_template('index.html', request, {})

    await ws_current.prepare(request)

    name = get_random_name()
    log.info('%s joined.', name)

    await ws_current.send_json({'action': 'connect', 'name': name})

    # Pickle
    pickled_ws_current = pickle.dumps(ws_current)
    connection = redis.from_url("redis://localhost:6379")
    keys = await redis.keys('*')
    for key in keys:
        temp = await redis.get(key)
        unpickled_temp = pickle.loads(temp)
        await unpickled_temp.send_json({'action': 'join', 'name': name})
    await connection.set(name, pickled_ws_current)

    while True:
        msg = await ws_current.receive()

        if msg.type == aiohttp.WSMsgType.text:
            keys = await redis.keys('*')
            for key in keys:
                if key is not name:
                    temp = await redis.get(key)
                    unpickled_temp = pickle.loads(temp)
                    await unpickled_temp.send_json({'action': 'join', 'name': name})
        else:
            break

    # Pickle
    connection.delete(name)
    log.info('%s disconnected.', name)
    keys = await redis.keys('*')
    for key in keys:
        temp = await redis.get(key)
        unpickled_temp = pickle.loads(temp)
        await unpickled_temp.send_json({'action': 'disconnect', 'name': name})

    return ws_current
