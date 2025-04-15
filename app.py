from flask import Flask, request, jsonify, render_template
import copy

app = Flask(__name__)

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

# 全域遊戲狀態
GAME_STATE = {
    "board": init_board(),
    "current": BLACK  # 黑先手
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/init", methods=["GET"])
def init_game():
    GAME_STATE["board"] = init_board()
    GAME_STATE["current"] = BLACK
    return jsonify({
        "board": GAME_STATE["board"],
        "current": GAME_STATE["current"]
    })

@app.route("/move", methods=["POST"])
def move():
    data = request.get_json()
    row = data.get("row")
    col = data.get("col")
    color = GAME_STATE["current"]
    board = GAME_STATE["board"]
    if not is_on_board(row, col):
        return jsonify({"valid": False})
    flips = get_flippable(board, row, col, color)
    if not flips:
        return jsonify({"valid": False})
    make_move(board, row, col, color)
    # 切換回合
    GAME_STATE["current"] = WHITE if color == BLACK else BLACK
    return jsonify({
        "valid": True,
        "board": board,
        "current": GAME_STATE["current"]
    })

if __name__ == "__main__":
    # 刪除 ngrok 相關程式碼，直接啟動 Flask 服務器
    app.run(debug=True)
