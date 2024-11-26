from websocket_game import *
from flask import Blueprint
from websocket_game.v2 import resources

bp=Blueprint('websocket_game',__name__)
api.blueprint_setup=bp
api.blueprint=bp

from websocket_game.v2 import endpoints

app.register_blueprint(bp)
socketio.on_namespace(resources.Home("/test"))