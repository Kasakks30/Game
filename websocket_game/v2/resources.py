import random
import string
import requests
import json
from flask import request, jsonify
from flask_restful import Resource
from flask_socketio import Namespace, join_room, leave_room, send, emit
from websocket_game import *


class register(Resource):
    def post(self):
        data = request.json
        user_nme = data['user_nme']
        user_email = data['user_email']
        user_pswd = data['user_pswd']
        data = {user_nme: 'user_nme', user_email: 'user_email', user_pswd: 'user_pswd'}
        try:
            cursor = mysql.connection.cursor()
            cursor.callproc('check_email', [user_email])
            acc = cursor.fetchone()
            cursor.close()
            if data:
                if acc is None:
                    add_cursor = mysql.connection.cursor()
                    add_cursor.callproc('add_details', [user_nme, user_email, user_pswd])
                    mysql.connection.commit()
                    add_cursor.close()
                    msg = {"message": "registered success!"}
                    return msg, 200
                else:
                    return {'message': "email already exist"}, 400
        except Exception as e:
            print(e)
            return {"msg": "connection error"}, 404


class login(Resource):
    def post(self):
        data = request.json
        user_email = data['user_email']
        user_pswd = data['user_pswd']
        cursor = mysql.connection.cursor()
        cursor.callproc('check_user', [user_email, user_pswd])
        account = cursor.fetchone()
        cursor.close()
        if account:
            return {"msg": "login successful"}, 200
        else:
            return {"message": "error!"}, 400


rooms = {}
players = {}
current_player = 'O'
second_player = 'X'
board = [''] * 9


def check_winner(board):
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6],
        [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
    for combo in winning_combinations:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] and board[combo[0]] != "":
            return board[combo[0]]
    return None


class Home(Namespace):

    def on_move(self, data):
        global current_player, board, players, cache_data, redis_data
        room_code = data.get('room_code')
        user_email = data.get('user_email')
        index = int(data.get('index'))
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT user_nme FROM game_table WHERE user_email = %s', (user_email,))
        db_data = cursor.fetchone()
        name = db_data[0]

        if room_code not in players:
            players[room_code] = [None, None]

        if players[room_code][0] is None:
            players[room_code][0] = user_email
            current_player = 'O'

        elif players[room_code][1] is None:
            players[room_code][1] = user_email
            current_player = 'X'
        else:
            if user_email == players[room_code][0]:
                current_player = 'O'
            elif user_email == players[room_code][1]:
                current_player = 'X'
            else:
                emit('move_response', {'board': board, 'message': "You are not in this game room."})
                return

        # if (current_player == 'O' and user_email != players[room_code][0]) or \
        #         (current_player == 'X' and user_email != players[room_code][1]):
        #     emit('move_response', {'board': board, 'message': "It's not your turn."})
        #     return

        if board[index] == "":
            board[index] = current_player
            winner = check_winner(board)
            # redis_data_json = redis_client.get(user_email)
            # if redis_data_json:
            #     redis_data = json.loads(redis_data_json)

            redis_key = f"game_board:{room_code}"
            redis_data = redis_client.get(redis_key)
            if redis_data:
                redis_data = json.loads(redis_data)
            else:
                redis_data = {"positions": []}

            redis_data['positions'].append(board)
            redis_json_data = json.dumps(redis_data)
            redis_client.set(redis_key, redis_json_data)
            load_data = redis_data['positions'][-1]
            # redis_data = {"positions": []}
            # redis_json_data= json.dumps(redis_data)
            # redis_client.set("data_positions",redis_json_data)
            # redis_data['positions'].append(board)
            # redis_data = redis_client['data_positions']
            # cache_data = redis_client.set(user_email, json.dumps(redis_data))
            # print("redis data is: ", redis_data['position'])
            # emit('load_data',{'position':redis_data['position']})
            # emit('load_data',cache_data['position'],room=room_code,broadcast=True)
            emit('move_response', {'board': board}, room=room_code, broadcast=True)
            emit("load_data", {"redis_key": load_data}, room=room_code, broadcast=True)

            if winner:
                message = f"Player {name} wins!"
                board = [''] * 9
                redis_client.delete(redis_key)
                # redis_client['data_positions'] = []
                # redis_client.set('data_positions',[])
                # emit('move_response', {'board': board, 'message': message,'position':[]}, room=room_code, broadcast=True)
                emit('game_over', {'message': message}, room=room_code, broadcast=True)

            elif "" not in board:
                message = "It's a draw!"
                board = [''] * 9
                redis_client.delete(redis_key)
                # redis_client['data_positions'] = []
                # redis_client.set('data_positions',[])
                # emit('move_response', {'board': board, 'message': message,'position':[]}, room=room_code, broadcast=True)
                emit('game_over', {'message': message}, room=room_code, broadcast=True)
            else:
                message = None
            # redis_data_json = redis_client.get(user_email)
            # if redis_data_json:
            #     redis_data = json.loads(redis_data_json)
            # emit('load_data', redis_data['position'], room=room_code)
            # emit('move_response', {'board': board}, room=room_code, broadcast=True)

    def on_load_page(self, data):
        # global board
        room_code = data.get("room_code")
        redis_key = f"game_board:{room_code}"
        redis_data = redis_client.get(redis_key)
        if redis_data:
            redis_load = json.loads(redis_data)['positions'][-1]
            # winner = check_winner(board)
            # if winner:
            #     board=[' ']*9
            #     redis_client.delete(redis_key)
            # elif "" not in board:
            #     board = [''] * 9
            #     redis_client.delete(redis_key)
            emit("load_data", {"redis_key": redis_load}, broadcast=True)
        # else:
        #     pass

    def on_connect(self, auth):
        # redis_client.delete(redis_key)
        global players, rooms, redis_data
        room_code = request.args.get("room_code")
        user_email = request.args.get("user_email")
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT user_nme FROM game_table WHERE user_email = %s', (user_email,))
        db_data = cursor.fetchone()
        # if room_code not in rooms:
        #     rooms[room_code] = {"members": []}

        # if len(rooms[room_code]["members"]) > 4:
        #     emit('game_over', {'message': 'Room is full.'})
        #     return
        # if room_code not in rooms:
        # redis_data_json = redis_client.get(user_email)
        # if redis_data_json:
        #     redis_data = json.loads(redis_data_json)
        #     print("your positions are: ", redis_data['position'])
        #     print("your value is: ", redis_data['value'])
        #     emit('load_data', {'position': redis_data['position']})
        # else:
        #     try:
        #         if len(rooms[room_code]['members'])<=2:
        #             print(rooms)
        #             player_mark = 'O' if len(rooms[room_code]["members"]) == 0 else 'X'
        #             redis_data = {"positions":[]}
        #             redis_json_data= json.dumps(redis_data)
        #             redis_client.set("data_positions",redis_json_data)
        # emit("load_data",{"redis_data":redis_client})
        # redis_data = {
        #     "value": player_mark,
        #     "position": []
        # }
        # redis_data_json = json.dumps(redis_data)
        # redis_client.set(user_email, redis_data_json)
        # print("redis json data is: ",redis_data_json)
        # redis_list=[]
        # redis_list.append(user_email)
        # print("redis listt isss:::",redis_list)
        # redis_client.set("user_data",redis_list)
        # else:
        #     redis_data_json = redis_client.get(user_email)
        #     if redis_data_json:
        #         redis_data = json.loads(redis_data_json)
        #     print("your alllllllllllll positions are: ", redis_data['position'])
        #     emit('load_data',{'position':redis_data['position']},room=room_code,broadcast=True)
        try:
            name = db_data[0]
            join_room(room_code)
            rooms[room_code]["members"].append(user_email)
            print(f"{name} joined the room {room_code}")
            send({"user_email": user_email, "message": f"{name} has joined the room"}, to=room_code)
            send({"message": f"{name} joined the room"}, to=room_code)
        except Exception as e:
            return str(e)

            # except Exception as e:
            #     print(e)


# jwt = JWTManager(app)
#
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         data = eval(request.data)
#         username = data['username']
#         password = data['password']
#
#         cur = mysql.connection.cursor()
#         cur.execute('SELECT * FROM users WHERE name = %s', (username,))
#         user = cur.fetchone()
#         cur.close()
#
#         if user and user[3] == password:
#             access_token = create_access_token(identity=username)
#             # return jsonify(access_token=access_token)
#             return {'msg': 'success', 'access_token': access_token}, 200
#         else:
#             return jsonify({"msg": "Invalid credentials"}), 401
#
#     return render_template('login.html')


class Disconnect(Resource):
    def post(self):
        try:
            data = str(request.data, 'utf-8')
            redis_key = f"game_board:{data}"
            redis_client.delete(redis_key)
            print(redis_key)
            return {'msg': "success"}, 200
        except Exception as e:
            return e, 400
