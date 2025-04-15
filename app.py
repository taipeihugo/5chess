from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_socketio import SocketIO, join_room, emit
import copy

app = Flask(__name__)
app.config['SECRET_KEY'] = '123'
socketio = SocketIO(app, cors_allowed_origins="*")  # 注意：生產環境請依需求設定 CORS

# 遊戲參數設定
BOARD_SIZE = 8
EMPTY = ""
BLACK = "B"
WHITE = "W"

def init_board():
    board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    # 初始化中間四格
    board[3][3] = WHITE
    board[3][4] = BLACK
    board[4][3] = BLACK
    board[4][4] = WHITE
    return board

def is_on_board(row, col):
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

def get_flippable(board, row, col, color):
    if board[row][col] != EMPTY or not is_on_board(row, col):
        return []
    opponent = WHITE if color == BLACK else BLACK
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    to_flip = []
    for dr, dc in directions:
        r, c = row + dr, col + dc
        tiles = []
        while is_on_board(r, c) and board[r][c] == opponent:
            tiles.append([r, c])
            r += dr
            c += dc
        if tiles and is_on_board(r, c) and board[r][c] == color:
            to_flip.extend(tiles)
    return to_flip

def make_move(board, row, col, color):
    flips = get_flippable(board, row, col, color)
    if not flips:
        return False
    board[row][col] = color
    for r, c in flips:
        board[r][c] = color
    return True

# 全域遊戲狀態，單一遊戲房間（room "game"）共用同一盤棋與回合
GAME_STATE = {
    "board": init_board(),
    "current": BLACK  # 黑先手
}

# 儲存已登入玩家
PLAYERS = {}

@app.route("/")
def index():
    # 如果玩家未登入，轉到登入頁面
    if 'username' not in session:
        return redirect(url_for("login"))
    return render_template("game.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        if username:
            session['username'] = username
            return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/init_game", methods=["GET"])
def init_game():
    # 重置遊戲狀態，僅限房間創建者或管理者使用
    GAME_STATE["board"] = init_board()
    GAME_STATE["current"] = BLACK
    return jsonify({
        "board": GAME_STATE["board"],
        "current": GAME_STATE["current"]
    })

# SocketIO 連線事件：加入房間 "game" 後將玩家資訊記錄
@socketio.on('join')
def on_join(data):
    username = session.get("username")
    if not username:
        return
    room = "game"
    join_room(room)
    PLAY
