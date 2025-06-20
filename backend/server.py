# server.py
import asyncio
import json
import cv2
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription

pcs = set()

async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("track")
    def on_track(track):
        print(f"Track {track.kind} received")

        if track.kind == "video":
            async def display():
                while True:
                    frame = await track.recv()
                    img = frame.to_ndarray(format="bgr24")
                    cv2.imshow("Received Video", img)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

            asyncio.ensure_future(display())

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })

async def on_shutdown(app):
    for pc in pcs:
        await pc.close()
    pcs.clear()

app = web.Application()
app.router.add_post("/offer", offer)
app.on_shutdown.append(on_shutdown)

web.run_app(app, port=8080)
