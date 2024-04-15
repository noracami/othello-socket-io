import os
from random import random
import socketio
from flask import Flask
from gevent import monkey

monkey.patch_all()


app = Flask(__name__)

REDIS_URI = os.environ.get("REDIS_URI", "redis://localhost:6379/0")

redis_manager = socketio.RedisManager(REDIS_URI)
sio = socketio.Server(client_manager=redis_manager, cors_allowed_origins="*")
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)


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
    random_char = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    random_room = [
        random_char[random.randint(0, len(random_char) - 1)] for _i in range(20)
    ].join("")
    sio.emit("message", f"{sid} created room {random_room}", skip_sid=sid)
    return f"{sid} created room {random_room} success"


@app.route("/health")
def health():
    return "OK"


if __name__ == "__main__":
    socketio.run(app, debug=True)
