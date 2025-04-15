from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, emit
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# 儲存房間資料（簡單示範，正式版請考慮狀態同步與錯誤處理）
rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create_or_join')
def on_create_or_join(data):
    room = data.get('room')
    if room not in rooms:
        rooms[room] = {'players': []}
    if len(rooms[room]['players']) < 2:
        join_room(room)
        rooms[room]['players'].append(request.sid)
        emit('status', {'msg': f'玩家已加入房間 {room}.'}, room=room)
        if len(rooms[room]['players']) == 2:
            # 當房間有兩位玩家時，隨機決定先手玩家
            first_player = random.choice(rooms[room]['players'])
            emit('start_game', {'first': first_player}, room=room)
    else:
        emit('status', {'msg': '房間已滿。'})

@socketio.on('move')
def on_move(data):
    room = data.get('room')
    cell = data.get('cell')
    # 將移動廣播到房間內所有用戶
    emit('move', {'cell': cell, 'player': request.sid}, room=room)

if __name__ == '__main__':
    # 當部署到 Render 時，可能需設定埠號與 debug 模式
    socketio.run(app, host='0.0.0.0', port=5000)
