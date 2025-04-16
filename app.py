from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# 允許跨來源請求
socketio = SocketIO(app, cors_allowed_origins="*")

# 使用一個固定聊天室名稱，限制聊天室僅允許 2 位使用者
chat_room = 'chat_room'
users = []  # 儲存已加入聊天室的使用者 (以 socket.id 為識別)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    username = data.get("username", "Anonymous")
    # 超過兩個使用者時，拒絕加入
    if len(users) >= 2:
        emit("full", {"msg": "聊天室已滿，請稍後再試。"})
    else:
        join_room(chat_room)
        users.append(request.sid)
        # 廣播狀態訊息給聊天室內所有使用者
        emit("status", {"msg": f"{username} 已加入聊天。"}, room=chat_room)
        print(f"User {username} (sid: {request.sid}) joined. Users: {users}")

@socketio.on('message')
def handle_message(data):
    username = data.get("username", "Anonymous")
    msg = data.get("msg", "")
    # 廣播訊息給聊天室內所有使用者
    emit("message", {"msg": f"{username}: {msg}"}, room=chat_room)

@socketio.on('disconnect')
def handle_disconnect():
    # 移除離線使用者
    if request.sid in users:
        users.remove(request.sid)
        # 廣播通知使用者離線
        emit("status", {"msg": "一位使用者已離開聊天。"}, room=chat_room)
        print(f"User (sid: {request.sid}) disconnected. Users: {users}")

if __name__ == '__main__':
    # 部署時可利用環境變數 PORT 指定埠號，Render 平台常會設定此環境變數
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
