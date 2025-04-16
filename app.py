from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# 允許跨來源請求
socketio = SocketIO(app, cors_allowed_origins="*")

chat_room = 'chat_room'
# 使用字典紀錄使用者：key 為 request.sid，value 為 username
users = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    username = data.get("username", "Anonymous")
    join_room(chat_room)
    # 將使用者加入字典
    users[request.sid] = username
    # 廣播狀態訊息和目前聊天室成員名單
    emit("status", {"msg": f"{username} 已加入聊天。", "users": list(users.values())}, room=chat_room)
    # 同步更新聊天室人員清單
    emit("user_list", {"users": list(users.values())}, room=chat_room)
    print(f"User {username} (sid: {request.sid}) joined. Users: {users}")

@socketio.on('message')
def handle_message(data):
    username = data.get("username", "Anonymous")
    msg = data.get("msg", "")
    emit("message", {"msg": f"{username}: {msg}"}, room=chat_room)

@socketio.on('disconnect')
def handle_disconnect():
    username = users.get(request.sid, "Someone")
    if request.sid in users:
        del users[request.sid]
    emit("status", {"msg": f"{username} 已離開聊天。", "users": list(users.values())}, room=chat_room)
    emit("user_list", {"users": list(users.values())}, room=chat_room)
    print(f"User {username} (sid: {request.sid}) disconnected. Users: {users}")

if __name__ == '__main__':
    # 取用環境變數 PORT 作為服務埠，Render 平台會設定此變數
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
