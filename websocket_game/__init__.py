from flask import Flask
from flask_restful import Api
import redis
from flask_socketio import SocketIO
import importlib
from flask_mysqldb import MySQL

app=Flask(__name__)
api=Api(app)
socketio=SocketIO(app,  logger=False, engineio_logger=False, ping_interval=5, always_connect=True, cors_allowed_origins="*")

app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_PASSWORD']='root'
app.config['MYSQL_USER']='root'
app.config['MYSQL_DB']='game_db'

app.config['REDIS_HOST']='localhost'
app.config['REDIS_PORT']= 6379
app.config['REDIS_DB']=0

redis_client=redis.Redis(
    host=app.config['REDIS_HOST'],
    port=app.config['REDIS_PORT'],
    db=app.config['REDIS_DB'],
    decode_responses=True)

mysql=MySQL(app)

importlib.import_module('websocket_game.v2')