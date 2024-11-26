from websocket_game import app,api
from websocket_game.v2.resources import *

api.add_resource(register,'/add-user')
api.add_resource(login,'/check-user')
api.add_resource(Disconnect,'/disconnect')

# api.add_resource(Code_Home,'/get-room')

