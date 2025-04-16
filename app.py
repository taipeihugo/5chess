from flask import Flask, render_template, send_from_directory, request
from flask_socketio import SocketIO, join_room, emit
import random

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # 啟用跨來源請求

# 房間資料結構
rooms = {}  # {room_name: {"players": [sid1, sid2]}}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def send_file(path):
    return send_from_directory('.', path)

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    for room, data in rooms.items():
        if request.sid in data['players']:
            data['players'].remove(request.sid)
            emit('status', {'msg': '有玩家離開房間。'}, room=room)
            # 如果房間內沒有玩家了就移除房間
            if not data['players']:
                del rooms[room]
            break

@socketio.on('create_or_join')
def on_create_or_join(data):
    room = data.get('room')
    print(f"Client {request.sid} wants to join room: {room}")
    if room not in rooms:
        rooms[room] = {'players': []}
    if len(rooms[room]['players']) < 2:
        join_room(room)
        rooms[room]['players'].append(request.sid)
        print(f"Room {room} players: {rooms[room]['players']}")
        emit('status', {'msg': f'玩家已加入房間 {room}。'}, room=room)
        if len(rooms[room]['players']) == 2:
            first_player = random.choice(rooms[room]['players'])
            print(f"開始遊戲，first player: {first_player}")
            emit('start_game', {'first': first_player}, room=room)
    else:
        emit('status', {'msg': '房間已滿。'})

@socketio.on('make_move')
def on_make_move(data):
    room = data.get('room')
    index = data.get('index')
    symbol = data.get('symbol')
    emit('move_made', {'index': index, 'symbol': symbol}, room=room)

if __name__ == '__main__':
    # 使用 eventlet 啟動以支援 WebSocket
    import eventlet
    import eventlet.wsgi
    eventlet.monkey_patch()
    socketio.run(app, host='0.0.0.0', port=5000)
