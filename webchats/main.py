import logging
import pathlib

import jinja2

import aiohttp_jinja2
from aiohttp import web
from views import index

BASE_DIR = pathlib.Path(__file__).parent.parent

async def init_app():
    app = web.Application()
    app['websockets'] = {}
    app.on_shutdown.append(shutdown)
    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(str(BASE_DIR / 'webchats' / 'templates'))
    )

    app.router.add_get('/', index)

    return app

async def shutdown(app):
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