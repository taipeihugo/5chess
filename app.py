from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# 限定聊天室只允許 2 位玩家
MAX_PLAYERS = 2
ROOM = 'game_room'

# 玩家記錄：key 為 socket id，value 為字典 {username, color}
players = {}

# 遊戲狀態變數
game_started = False
current_turn = None  # "B" 或 "W"
board = None  # 8x8 棋盤

# 初始化 8x8 棋盤，預設所有格子為空白
def init_board():
    b = [["" for _ in range(8)] for _ in range(8)]
    # 設定初始四枚棋子 (採用 0-based 索引)
    b[3][3] = "W"
    b[3][4] = "B"
    b[4][3] = "B"
    b[4][4] = "W"
    return b

# 定義 8 個方向：[dx,dy]
directions = [(-1,-1), (-1,0), (-1,1),
              (0,-1),          (0,1),
              (1,-1),  (1,0),  (1,1)]

# 檢查在 (row, col) 下棋對於 color 是否合法，並傳回所有要翻轉的棋子位置，否則傳回空列表
def check_move(color, b, row, col):
    if b[row][col] != "":
        return []
    # 設定對手顏色
    opponent = "B" if color == "W" else "W"
    flips_total = []
    for dx, dy in directions:
        flips = []
        x, y = row + dx, col + dy
        # 檢查第一格必須為對手棋子
        if x < 0 or x >= 8 or y < 0 or y >= 8:
            continue
        if b[x][y] != opponent:
            continue
        flips.append((x,y))
        # 沿此方向延伸
        while True:
            x += dx
            y += dy
            if x < 0 or x >= 8 or y < 0 or y >= 8:
                flips = []
                break
            if b[x][y] == "":
                flips = []
                break
            if b[x][y] == color:
                # 找到同色棋子，回傳該方向所有對手棋子位置
                break
            # 若是對手棋子則加入翻轉清單
            flips.append((x,y))
        flips_total.extend(flips)
    return flips_total

# 下棋動作
@socketio.on('make_move')
def on_make_move(data):
    global board, current_turn
    sid = request.sid
    # 只有遊戲已開始才能動作
    if not game_started:
        return
    # 檢查目前是否輪到此玩家
    player = players.get(sid)
    if not player or player.get("color") != current_turn:
        emit("error", {"msg": "目前不是你的回合。"})
        return
    try:
        row = int(data.get("row"))
        col = int(data.get("col"))
    except (ValueError, TypeError):
        emit("error", {"msg": "無效的下棋位置。"})
        return

    flips = check_move(current_turn, board, row, col)
    if not flips:
        emit("error", {"msg": "此步無法翻轉對方棋子，請換其他位置。"})
        return
    # 合法，下棋並翻轉棋子
    board[row][col] = current_turn
    for x, y in flips:
        board[x][y] = current_turn
    # 切換回合
    current_turn = "B" if current_turn == "W" else "W"
    # 廣播更新後棋盤與目前回合狀態
    emit("board_update", {"board": board, "turn": current_turn}, room=ROOM)

# 玩家加入動作
@socketio.on('join')
def on_join(data):
    global game_started, current_turn, board
    username = data.get("username", "Anonymous")
    sid = request.sid
    if len(players) >= MAX_PLAYERS:
        emit("full", {"msg": "聊天室已滿，僅限兩位玩家進入。"})
        return
    join_room(ROOM)
    # 分配顏色：第一位為黑(B)，第二位為白(W)
    color = "B" if len(players) == 0 else "W"
    players[sid] = {"username": username, "color": color}
    # 廣播目前加入狀態
    human_color = "黑" if color == "B" else "白"
    emit("status", {"msg": f"{username} ({human_color}) 加入遊戲。"}, room=ROOM)
    # 當兩位玩家都已加入後，啟動遊戲
    if len(players) == MAX_PLAYERS:
        game_started = True
        board = init_board()
        current_turn = "B"  # 黑棋先手
        emit("start_game", {"board": board, "turn": current_turn, 
                              "players": [players[s]["username"] + " (" + players[s]["color"] + ")" for s in players]},
             room=ROOM)

# 玩家離線時清除狀態
@socketio.on('disconnect')
def on_disconnect():
    global game_started
    sid = request.sid
    if sid in players:
        username = players[sid]["username"]
        del players[sid]
        emit("status", {"msg": f"{username} 離開遊戲。"}, room=ROOM)
        # 若有人離線則結束遊戲（可根據需求擴充，例如等待重連）
        game_started = False

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
