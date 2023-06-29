import logging
import pathlib

import jinja2
import redis.asyncio as redis

import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import setup, SimpleCookieStorage
from views import index

BASE_DIR = pathlib.Path(__file__).parent.parent


async def init_app():
    app = web.Application()
    app['websockets'] = {}
    # TODO
    app['redis'] = redis.from_url("redis://localhost:6379")
    app.on_shutdown.append(shutdown)
    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(
            str(BASE_DIR / 'webchats' / 'templates'))
    )
    setup(app, SimpleCookieStorage())

    app.router.add_get('/', index)

    return app


async def shutdown(app):
    # TODO
    for ws in app['websockets'].values():
        await ws.close()
    app['websockets'].clear()


async def get_app():
    import aiohttp_debugtoolbar
    app = await init_app()
    aiohttp_debugtoolbar.setup(app)
    return app


def main():
    logging.basicConfig(level=logging.DEBUG)

    app = init_app()
    web.run_app(app)


if __name__ == '__main__':
    main()
