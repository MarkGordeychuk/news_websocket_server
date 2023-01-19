import asyncio
import weakref
import base64
import uuid

import aiohttp
from aiohttp import web
from aiohttp_session import setup, get_session, new_session, SimpleCookieStorage


def file_handler_factory(file, **kwargs):
    kwargs.setdefault('content_type', 'text/html')
    kwargs.setdefault('headers', {}).setdefault('Cache-Control', 'max-age=3600')

    async def file_handler(request: web.Request) -> web.Response:
        with open(file, 'rb') as fp:
            return web.Response(body=fp.read(), **kwargs)

    return file_handler


index_handler = file_handler_factory('index.html')


async def websocket_handler(request):
    ws = web.WebSocketResponse()

    if not ws.can_prepare(request):
        session = await new_session(request)
        session['id'] = str(uuid.uuid4())
        return await index_handler(request)

    session = await get_session(request)

    await ws.prepare(request)
    request.app['websockets'][session['id']] = ws

    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                      ws.exception())
    finally:
        del request.app['websockets'][session['id']]

    print('websocket connection closed')

    return ws


async def post_handler(request: web.Request) -> web.Response:
    obj = dict(await request.post())

    await asyncio.gather(
        *[ws.send_json(obj) for ws in request.app['websockets'].values()]
    )

    return web.json_response(obj, status=202)


async def check_connection_handler(request: web.Request) -> web.Response:
    session = await get_session(request)
    return web.json_response({'connection': session['id'] in request.app['websockets']})


async def on_shutdown(app):
    await asyncio.gather(
        *[
            ws.close(code=aiohttp.WSCloseCode.GOING_AWAY, message='Server shutdown')
            for ws in app['websockets'].values()
        ]
    )


def init():
    app = web.Application()

    setup(app, SimpleCookieStorage())

    app['websockets'] = weakref.WeakValueDictionary()

    app.add_routes([
        web.get('/', websocket_handler),
        web.get('/script.js', file_handler_factory('script.js', content_type='application/javascript')),
        web.get('/style.css', file_handler_factory('style.css', content_type='text/css')),
        web.post('/news', post_handler),
        web.get('/check', check_connection_handler),
    ])

    app.on_shutdown.append(on_shutdown)

    return app


web.run_app(init())
