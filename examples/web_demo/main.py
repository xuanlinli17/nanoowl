import asyncio
from aiohttp import web, WSCloseCode
import logging
import weakref
import cv2
import time

CAMERA_DEVICE = 0
IMAGE_QUALITY = 50


async def handle_index_get(request: web.Request):
    logging.info("handle_index_get")
    return web.FileResponse("./index.html")


async def websocket_handler(request):

    ws = web.WebSocketResponse()

    await ws.prepare(request)

    logging.info("Websocket connected.")

    request.app['websockets'].add(ws)

    try:
        async for msg in ws:
            logging.info(f"Received message from websocket.")
    finally:
        request.app['websockets'].discard(ws)

    return ws


async def on_shutdown(app: web.Application):
    for ws in set(app['websockets']):
        await ws.close(code=WSCloseCode.GOING_AWAY,
                       message='Server shutdown')


async def detection_loop(app: web.Application):

    loop = asyncio.get_running_loop()

    camera = cv2.VideoCapture(CAMERA_DEVICE)

    def _read_and_encode_image():

        re, image = camera.read()

        if not re:
            return re, None

        image_jpeg = bytes(
            cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, IMAGE_QUALITY])[1]
        )

        return re, image_jpeg

    while True:

        re, image = await loop.run_in_executor(None, _read_and_encode_image)
        
        if not re:
            break
        
        for ws in app["websockets"]:
            await ws.send_bytes(image)

    camera.release()


async def run_detection_loop(app):
    try:
        task = asyncio.create_task(detection_loop(app))
        yield
        task.cancel()
    except asyncio.CancelledError:
        pass
    finally:
        await task


logging.basicConfig(level=logging.INFO)
app = web.Application()
app['websockets'] = weakref.WeakSet()
app.router.add_get("/", handle_index_get)
app.router.add_route("GET", "/ws", websocket_handler)
app.on_shutdown.append(on_shutdown)
app.cleanup_ctx.append(run_detection_loop)
web.run_app(app, host="0.0.0.0", port=7860)