import os
from datetime import datetime as DateTime
import random
import requests
import socketio
from flask import Flask
from gevent import monkey

monkey.patch_all()


app = Flask(__name__)

REDIS_URI = os.environ.get("REDIS_URI", "redis://localhost:6379/0")
print(f"REDIS_URI: {REDIS_URI}")

redis_manager = socketio.RedisManager(REDIS_URI)
sio = socketio.Server(client_manager=redis_manager, cors_allowed_origins="*")
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)

API_SERVER = os.environ.get("API_SERVER", "http://localhost:3000")
print(f"API_SERVER: {API_SERVER}")


@sio.event
def connect(sid, environ):
    print(f"connect {sid}")
    sio.emit("message", "Hello, World!", room=sid)


@sio.event
def disconnect(sid):
    print(f"disconnect {sid}")


# handle if client send message, broadcast to all clients
@sio.event
def chat_to_lobby(sid, data):
    print(f"message from {sid}: {data}")
    sio.emit("message", data, skip_sid=sid)


@sio.on("room:create")
def create_room(sid):
    # send request to external service to create room
    url = f"{API_SERVER}/rooms"
    print(f"create_room: {url}")
    headers = {"Content-Type": "application/json"}
    random_char = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    random_room = "".join(
        [random_char[random.randint(0, len(random_char) - 1)] for _i in range(20)]
    )
    data = {"name": f"room_{DateTime.now().isoformat()}", "channel_id": random_room}
    response = requests.post(url, timeout=3, json=data, headers=headers)
    print(response.status_code)

    if response.status_code != 201:
        return f"{sid} created room failed"

    sid.join(random_room)

    # broadcast json to all clients
    broadcast_message = response.json()

    sio.emit("message", broadcast_message, skip_sid=sid)
    return f"{sid} created room {random_room} success"


@sio.on("room:chat")
def chat_to_room(sid, data):
    print(f"chat_to_room: {data}")
    room_id = data.get("room_id")
    message = data.get("message")
    if not room_id or not message:
        return f"invalid data: {data}"

    sio.emit("message", message, room=room_id, skip_sid=sid)
    return f"send message to room {room_id} success"


@app.route("/health")
def health():
    return "OK"


# @app.route("/rooms")
# def rooms():
#     url = f"{API_SERVER}/rooms"
#     headers = {"Content-Type": "application/json"}
#     random_char = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
#     random_room = "".join(
#         [random_char[random.randint(0, len(random_char) - 1)] for _i in range(20)]
#     )
#     data = {"name": f"room_{DateTime.now().isoformat()}", "channel_id": random_room}
#     response = requests.post(url, timeout=3, json=data, headers=headers)
#     print(response.status_code)
#     if response.status_code != 201:
#         sid = "unknown"
#         return f"{sid} created room failed"

#     return response.json()


if __name__ == "__main__":
    socketio.run(app, debug=True)
