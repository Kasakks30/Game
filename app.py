from websocket_game import app,socketio

if __name__=='__main__':
    socketio.run(app,debug=False,port=2500,allow_unsafe_werkzeug=True)