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
        try:
            message = await channel.get_message(ignore_subscribe_messages=True)
            if message is not None:
                json_data = json.loads(message["data"].decode())
                if json_data["action"] == "join":
                    await ws.send_json({'action': 'join', 'name': json_data["name"]})
                elif json_data["action"] == "sent":
                    if json_data["name"] != name:
                        await ws.send_json({'action': 'sent', 'name': json_data["name"], 'text': json_data["text"]})
                else:
                    await ws.send_json({'action': 'disconnect', 'name': json_data["name"]})
        except:
            break


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

    # 현재 ws가 connect 되었다는 메세지를 연결된 웹소켓에 뿌려줌
    join_json = {
        "action": "join",
        "name": name
    }
    await r.publish("channel:1", json.dumps(join_json))

    # 현재 웹소켓이 채널에 subscribe하고 채널에 메세지를 publish해야 함
    async with r.pubsub() as pubsub:
        await pubsub.subscribe("channel:1")
        asyncio.create_task(reader(pubsub, ws_current, name))

        while True:
            msg = await ws_current.receive()
            # print(msg)
            if msg.type == aiohttp.WSMsgType.text:
                sent_json = {
                    "action": "sent",
                    "name": name,
                    "text": msg.data
                }
                await r.publish("channel:1", json.dumps(sent_json))
                # TODO : need to know how to work
                # await future
            else:
                break

    # web socket diconnect할 때, 다른 연결된 웹소켓에 메세지 전달
    disconnect_json = {
        "action": "disconnect",
        "name": name
    }
    await r.pubsub().unsubscribe("channel:1")
    await r.publish("channel:1", json.dumps(disconnect_json))
    log.info('%s disconnected.', name)

    return ws_current
