import os
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

API_SERVER = os.environ.get("API_SERVER", "http://localhost:5000")
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
    response = requests.post(url)
    print(response.status_code)
    if response.status_code != 200:
        return f"{sid} created room failed"

    response_data = response.json()
    print(response_data)
    random_room = response_data.get("room")

    # random_char = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    # random_room = "".join(
    #     [random_char[random.randint(0, len(random_char) - 1)] for _i in range(20)]
    # )
    # sio.emit("message", f"{sid} created room {random_room}", skip_sid=sid)
    return f"{sid} created room {random_room} success"


@app.route("/health")
def health():
    return "OK"


if __name__ == "__main__":
    socketio.run(app, debug=True)
