import pygame
import sys
import socket
import threading
import chess
import chess.engine
import time

# --- KHỞI ĐỘNG TRỌNG TÀI STOCKFISH ---
try:
    engine_path = "stockfish.exe"
    sf_engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    print("Đã triệu hồi trọng tài Stockfish thành công!")
except Exception as e:
    print("CẢNH BÁO: Không tìm thấy stockfish.exe. Game sẽ chơi bình thường nhưng mất tính năng Meme và AI.")
    sf_engine = None

# --- MENU KHỞI ĐỘNG BẰNG GIAO DIỆN TKINTER ---
import tkinter as tk
from tkinter import messagebox, ttk

# Biến lưu lựa chọn sau khi đóng cửa sổ
is_offline = False
is_host = False
is_ai = False
ai_color = None
my_color = "both"
connection = None
PORT = 5555
_server_ip_result = "127.0.0.1"
_game_started = False  # Cờ kiểm tra người dùng có bấm Start không

def center_window(win, w, h):
    """Căn cửa sổ ra giữa màn hình"""
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")

def build_menu():
    global is_offline, is_host, is_ai, ai_color, my_color
    global connection, _server_ip_result, _game_started

    root = tk.Tk()
    root.title("♟ Meme Chess Championship")
    root.resizable(False, False)
    root.configure(bg="#1e1e2e")

    # ---------- Style ----------
    DARK_BG   = "#1e1e2e"
    PANEL_BG  = "#2a2a3e"
    ACCENT    = "#c0a060"
    FG_WHITE  = "#f0ece0"
    FG_GRAY   = "#888899"
    BTN_BG    = "#3a3a50"
    BTN_ACT   = "#4a4a65"
    ENTRY_BG  = "#14141f"

    font_title  = ("Georgia", 20, "bold")
    font_sub    = ("Verdana", 9)
    font_label  = ("Verdana", 10, "bold")
    font_normal = ("Verdana", 10)
    font_btn    = ("Verdana", 11, "bold")

    # ---------- Tiêu đề ----------
    tk.Label(root, text="♟  MEME CHESS", font=font_title,
             bg=DARK_BG, fg=ACCENT).pack(pady=(18, 2))
    tk.Label(root, text="DSA Championship Edition", font=font_sub,
             bg=DARK_BG, fg=FG_GRAY).pack(pady=(0, 14))

    # ---------- Frame chọn chế độ ----------
    mode_frame = tk.LabelFrame(root, text="  Chế độ chơi  ", font=font_label,
                                bg=PANEL_BG, fg=ACCENT, bd=2, relief="groove",
                                padx=14, pady=10)
    mode_frame.pack(fill="x", padx=20, pady=(0, 10))

    mode_var = tk.StringVar(value="offline")

    modes = [
        ("offline", "⚔  Offline  —  2 người cùng máy"),
        ("ai",      "🤖  vs AI   —  Đấu với Stockfish"),
        ("online",  "🌐  Online  —  Đấu qua mạng LAN"),
    ]
    for val, label in modes:
        tk.Radiobutton(mode_frame, text=label, variable=mode_var, value=val,
                       font=font_normal, bg=PANEL_BG, fg=FG_WHITE,
                       selectcolor=DARK_BG, activebackground=PANEL_BG,
                       activeforeground=ACCENT).pack(anchor="w", pady=2)

    # ---------- Frame tùy chọn con (thay đổi theo mode) ----------
    sub_frame = tk.LabelFrame(root, text="  Tùy chọn  ", font=font_label,
                               bg=PANEL_BG, fg=ACCENT, bd=2, relief="groove",
                               padx=14, pady=10)
    sub_frame.pack(fill="x", padx=20, pady=(0, 10))

    # Widgets bên trong sub_frame (ẩn/hiện theo mode)
    color_var  = tk.StringVar(value="white")
    role_var   = tk.StringVar(value="host")
    ip_var     = tk.StringVar(value="127.0.0.1")

    # -- AI color --
    ai_frame = tk.Frame(sub_frame, bg=PANEL_BG)
    tk.Label(ai_frame, text="Bạn cầm quân:", font=font_normal,
             bg=PANEL_BG, fg=FG_WHITE).pack(side="left")
    for val, txt in [("white", "♔ Trắng (đi trước)"), ("black", "♚ Đen (đi sau)")]:
        tk.Radiobutton(ai_frame, text=txt, variable=color_var, value=val,
                       font=font_normal, bg=PANEL_BG, fg=FG_WHITE,
                       selectcolor=DARK_BG, activebackground=PANEL_BG).pack(side="left", padx=6)

    # -- Online role + IP --
    online_frame = tk.Frame(sub_frame, bg=PANEL_BG)
    tk.Label(online_frame, text="Vai trò:", font=font_normal,
             bg=PANEL_BG, fg=FG_WHITE).grid(row=0, column=0, sticky="w")
    for col_idx, (val, txt) in enumerate([("host", "🏠 Tạo phòng (Trắng)"), ("client", "🔌 Vào phòng (Đen)")]):
        tk.Radiobutton(online_frame, text=txt, variable=role_var, value=val,
                       font=font_normal, bg=PANEL_BG, fg=FG_WHITE,
                       selectcolor=DARK_BG, activebackground=PANEL_BG).grid(
                           row=0, column=col_idx+1, padx=8, sticky="w")
    tk.Label(online_frame, text="IP Host:", font=font_normal,
             bg=PANEL_BG, fg=FG_WHITE).grid(row=1, column=0, sticky="w", pady=(6,0))
    ip_entry = tk.Entry(online_frame, textvariable=ip_var, font=font_normal,
                        bg=ENTRY_BG, fg=FG_WHITE, insertbackground=FG_WHITE,
                        relief="flat", width=18, bd=4)
    ip_entry.grid(row=1, column=1, columnspan=2, sticky="w", pady=(6,0))

    # -- Offline placeholder --
    offline_frame = tk.Frame(sub_frame, bg=PANEL_BG)
    tk.Label(offline_frame, text="Hai người cùng ngồi một máy.\nLần lượt di chuyển quân cờ.",
             font=font_normal, bg=PANEL_BG, fg=FG_GRAY, justify="left").pack(anchor="w")

    # Hàm cập nhật sub_frame khi đổi mode
    current_sub = [None]
    def update_sub(*_):
        if current_sub[0]:
            current_sub[0].pack_forget()
        m = mode_var.get()
        if m == "offline":
            offline_frame.pack(fill="x")
            current_sub[0] = offline_frame
        elif m == "ai":
            ai_frame.pack(fill="x")
            current_sub[0] = ai_frame
        else:
            online_frame.pack(fill="x")
            current_sub[0] = online_frame

    mode_var.trace_add("write", update_sub)
    update_sub()  # khởi tạo lần đầu

    # ---------- Tên người chơi ----------
    name_frame = tk.LabelFrame(root, text="  Tên người chơi  ", font=font_label,
                                bg=PANEL_BG, fg=ACCENT, bd=2, relief="groove",
                                padx=14, pady=10)
    name_frame.pack(fill="x", padx=20, pady=(0, 14))

    name_white_var = tk.StringVar(value="")
    name_black_var = tk.StringVar(value="")

    row0 = tk.Frame(name_frame, bg=PANEL_BG)
    row0.pack(fill="x", pady=2)
    tk.Label(row0, text="♔ Quân Trắng:", font=font_normal, bg=PANEL_BG,
             fg=FG_WHITE, width=14, anchor="w").pack(side="left")
    tk.Entry(row0, textvariable=name_white_var, font=font_normal,
             bg=ENTRY_BG, fg=FG_WHITE, insertbackground=FG_WHITE,
             relief="flat", width=20, bd=4).pack(side="left")

    row1 = tk.Frame(name_frame, bg=PANEL_BG)
    row1.pack(fill="x", pady=2)
    tk.Label(row1, text="♚ Quân Đen:", font=font_normal, bg=PANEL_BG,
             fg=FG_WHITE, width=14, anchor="w").pack(side="left")
    tk.Entry(row1, textvariable=name_black_var, font=font_normal,
             bg=ENTRY_BG, fg=FG_WHITE, insertbackground=FG_WHITE,
             relief="flat", width=20, bd=4).pack(side="left")

    # ---------- Nút Start ----------
    def on_start():
        global is_offline, is_host, is_ai, ai_color, my_color
        global connection, _server_ip_result, _game_started

        w_name = name_white_var.get().strip()
        b_name = name_black_var.get().strip()
        if not w_name or not b_name:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tên cả hai người chơi!", parent=root)
            return

        m = mode_var.get()
        if m == "offline":
            is_offline = True
            my_color = "both"
            print(f"Offline: {w_name} vs {b_name}")

        elif m == "ai":
            is_offline = True
            is_ai = True
            my_color = color_var.get()
            ai_color = "black" if my_color == "white" else "white"
            print(f"vs AI — Bạn ({w_name}) cầm quân {my_color}")

        elif m == "online":
            is_offline = False
            is_host = (role_var.get() == "host")
            my_color = "white" if is_host else "black"
            _server_ip_result = ip_var.get().strip() or "127.0.0.1"
            print(f"Online — {'Host' if is_host else 'Client'}, IP={_server_ip_result}")

        _game_started = True
        root.destroy()

    tk.Button(root, text="🎮  BẮT ĐẦU TRẬN ĐẤU", command=on_start,
              font=font_btn, bg=ACCENT, fg="#1e1e2e",
              activebackground="#d4b070", activeforeground="#1e1e2e",
              relief="flat", padx=20, pady=10, cursor="hand2",
              bd=0).pack(pady=(0, 18))

    center_window(root, 460, 560)
    root.mainloop()

build_menu()

# Nếu người dùng đóng cửa sổ mà không bấm Start thì thoát
if not _game_started:
    sys.exit()

# --- XỬ LÝ KẾT NỐI ONLINE SAU KHI TKINTER ĐÓNG ---
if not is_offline:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if is_host:
        sock.bind(("0.0.0.0", PORT))
        sock.listen(1)
        print(f"Đang chờ đối thủ kết nối tại cổng {PORT}...")
        connection, addr = sock.accept()
        print(f"Đối thủ đã kết nối từ {addr}!")
    else:
        print(f"Đang kết nối tới {_server_ip_result}...")
        sock.connect((_server_ip_result, PORT))
        connection = sock
        print("Kết nối thành công!")

# --- CẤU HÌNH TRÒ CHƠI & ĐỒ HỌA ---
pygame.init()
pygame.font.init()
pygame.mixer.init()

BOARD_SIZE = 640
UI_WIDTH = 250
MARGIN = 20

WIDTH = BOARD_SIZE + UI_WIDTH + (MARGIN * 2)
HEIGHT = BOARD_SIZE + (MARGIN * 2)
ROWS, COLS = 8, 8
SQUARE_SIZE = BOARD_SIZE // COLS

COLOR_LIGHT = (240, 217, 181)
COLOR_DARK = (181, 136, 99)
COLOR_BG = (35, 35, 35)
PIECE_WHITE = (255, 255, 255)

COLOR_SELECT = (130, 150, 100, 150)
COLOR_VALID_DOT = (100, 100, 100, 100)
COLOR_LAST_MOVE = (245, 245, 100, 120)

# --- NẠP ÂM THANH (Bao gồm cả âm thanh Meme) ---
try:
    sound_move = pygame.mixer.Sound("move.wav")
    sound_capture = pygame.mixer.Sound("capture.wav")
    sound_check = pygame.mixer.Sound("move-check.wav")
    sound_mate = pygame.mixer.Sound("checkmate.wav")
except:
    sound_move = sound_capture = sound_check = sound_mate = None

try:
    sound_blunder = pygame.mixer.Sound("bruh.wav")
    sound_brilliant = pygame.mixer.Sound("sigma.wav")
except:
    sound_blunder = sound_brilliant = None

IMAGE_MAP = {
    "white": {"K": "3.png", "Q": "13.png", "R": "9.png", "B": "5.png", "N": "7.png", "P": "11.png"},
    "black": {"K": "4.png", "Q": "14.png", "R": "10.png", "B": "6.png", "N": "8.png", "P": "12.png"}
}

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DSA Meme Chess Championship")

ui_font = pygame.font.SysFont("Verdana", 24)
status_font = pygame.font.SysFont("Verdana", 18, bold=True)
meme_font = pygame.font.SysFont("Impact", 48, bold=True) # Font to cho Meme

# --- BIẾN TOÀN CỤC CHO MEME POPUP ---
current_meme_text = ""
current_meme_color = (255, 255, 255)
meme_timer = 0

class Piece:
    def __init__(self, color, name):
        self.color = color
        self.name = name
        self.has_moved = False
        try:
            filename = IMAGE_MAP[color][name]
            img = pygame.image.load(filename).convert_alpha()
            self.surf = pygame.transform.smoothscale(img, (int(SQUARE_SIZE * 0.9), int(SQUARE_SIZE * 0.9)))
        except:
            self.surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(self.surf, (200, 0, 0), (SQUARE_SIZE//2, SQUARE_SIZE//2), 20)
        self.rect = self.surf.get_rect()

    def draw(self, screen, center_pos):
        self.rect.center = center_pos
        screen.blit(self.surf, self.rect)

class Chess:
    def __init__(self):
        self.board = self.create_board()
        self.turn = "white"
        self.selected = None
        self.valid_moves = []
        self.last_move = None
        self.move_50 = 0
        self.game_over = False
        self.status_msg = ""
        self.en_passant_target = None
        self.logic_board = chess.Board()

    def create_board(self):
        board = [[None for _ in range(8)] for _ in range(8)]
        for i in range(8):
            board[1][i] = Piece("black", "P")
            board[6][i] = Piece("white", "P")
        order = ["R", "N", "B", "Q", "K", "B", "N", "R"]
        for i in range(8):
            board[0][i] = Piece("black", order[i])
            board[7][i] = Piece("white", order[i])
        return board

    def get_uci(self, r1, c1, r2, c2):
        files = "abcdefgh"
        ranks = "87654321"
        return files[c1] + ranks[r1] + files[c2] + ranks[r2]

    def find_king(self, color):
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.name == "K" and piece.color == color: return (r, c)
        return None

    def is_square_attacked(self, row, col, color_attacker):
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.color == color_attacker:
                    if self._can_attack(r, c, row, col): return True
        return False

    def is_in_check(self, color):
        king_pos = self.find_king(color)
        if not king_pos: return False
        opponent = "black" if color == "white" else "white"
        return self.is_square_attacked(king_pos[0], king_pos[1], opponent)

    def _can_attack(self, x1, y1, x2, y2):
        piece = self.board[x1][y1]
        if not piece: return False
        target = self.board[x2][y2]
        if target and target.color == piece.color: return False
        dx, dy = x2 - x1, y2 - y1
        if piece.name == "P":
            direction = 1 if piece.color == "black" else -1
            if dx == direction and abs(dy) == 1: return True
        elif piece.name == "N":
            if (abs(dx), abs(dy)) in [(2, 1), (1, 2)]: return True
        elif piece.name == "K":
            if max(abs(dx), abs(dy)) == 1: return True
        elif piece.name == "R":
            if dx == 0 or dy == 0: return self._path_clear(x1, y1, x2, y2)
        elif piece.name == "B":
            if abs(dx) == abs(dy): return self._path_clear(x1, y1, x2, y2)
        elif piece.name == "Q":
            if dx == 0 or dy == 0 or abs(dx) == abs(dy): return self._path_clear(x1, y1, x2, y2)
        return False

    def _path_clear(self, x1, y1, x2, y2):
        dx = 0 if x2 == x1 else (1 if x2 > x1 else -1)
        dy = 0 if y2 == y1 else (1 if y2 > y1 else -1)
        r, c = x1 + dx, y1 + dy
        while (r, c) != (x2, y2):
            if self.board[r][c] is not None: return False
            r += dx; c += dy
        return True

    def get_all_valid_moves(self, row, col):
        valid_moves = []
        piece = self.board[row][col]
        if not piece or piece.color != self.turn: return []
        for r in range(ROWS):
            for c in range(COLS):
                if self._is_pseudo_legal(row, col, r, c):
                    if self._try_move_safe(row, col, r, c):
                        valid_moves.append((r, c))
        return valid_moves

    def _is_pseudo_legal(self, x1, y1, x2, y2):
        piece = self.board[x1][y1]
        if not piece: return False
        target = self.board[x2][y2]
        if target and target.color == piece.color: return False
        dx, dy = x2 - x1, y2 - y1
        if piece.name == "P":
            direction = -1 if piece.color == "white" else 1
            start_row = 6 if piece.color == "white" else 1
            if dy == 0 and dx == direction and not target: return True
            if (dy == 0 and dx == direction * 2 and x1 == start_row and not target and not self.board[x1 + direction][y1]): return True
            if abs(dy) == 1 and dx == direction and target: return True
            if (abs(dy) == 1 and dx == direction and self.en_passant_target == (x2, y2)): return True
        elif piece.name == "N":
            if (abs(dx), abs(dy)) in [(2, 1), (1, 2)]: return True
        elif piece.name == "K":
            if max(abs(dx), abs(dy)) == 1: return True
            if dx == 0 and abs(dy) == 2: return self._can_castle(piece, x1, y1, y2)
        elif piece.name == "R":
            if (dx == 0 or dy == 0) and self._path_clear(x1, y1, x2, y2): return True
        elif piece.name == "B":
            if abs(dx) == abs(dy) and self._path_clear(x1, y1, x2, y2): return True
        elif piece.name == "Q":
            if (dx == 0 or dy == 0 or abs(dx) == abs(dy)) and self._path_clear(x1, y1, x2, y2): return True
        return False

    def _can_castle(self, king, row, y1, y2):
        if king.has_moved or self.is_in_check(king.color): return False
        opponent = "black" if king.color == "white" else "white"
        if y2 > y1:
            rook = self.board[row][7]
            if not rook or rook.name != "R" or rook.has_moved: return False
            for c in range(y1 + 1, 7):
                if self.board[row][c]: return False
            for c in range(y1, y1 + 3):
                if self.is_square_attacked(row, c, opponent): return False
        else:
            rook = self.board[row][0]
            if not rook or rook.name != "R" or rook.has_moved: return False
            for c in range(1, y1):
                if self.board[row][c]: return False
            for c in range(y1 - 2, y1 + 1):
                if self.is_square_attacked(row, c, opponent): return False
        return True

    def _try_move_safe(self, x1, y1, x2, y2):
        piece = self.board[x1][y1]
        captured = self.board[x2][y2]
        ep_captured = None
        ep_pos = None
        if piece.name == "P" and self.en_passant_target == (x2, y2):
            direction = -1 if piece.color == "white" else 1
            ep_pos = (x2 - direction, y2)
            ep_captured = self.board[ep_pos[0]][ep_pos[1]]
            self.board[ep_pos[0]][ep_pos[1]] = None
        self.board[x2][y2] = piece
        self.board[x1][y1] = None
        safe = not self.is_in_check(self.turn)
        self.board[x1][y1] = piece
        self.board[x2][y2] = captured
        if ep_pos: self.board[ep_pos[0]][ep_pos[1]] = ep_captured
        return safe

    def has_any_moves(self, color):
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.color == color:
                    old_turn = self.turn
                    self.turn = color
                    moves = self.get_all_valid_moves(r, c)
                    self.turn = old_turn
                    if moves: return True
        return False

    def move(self, x1, y1, x2, y2):
        piece = self.board[x1][y1]
        is_capture = self.board[x2][y2] is not None or (piece.name == "P" and self.en_passant_target == (x2, y2))
        
        # --- ĐỒNG BỘ VỚI ENGINE ---
        uci_str = self.get_uci(x1, y1, x2, y2)
        if piece.name == "P" and (x2 == 0 or x2 == 7):
            uci_str += "q" 
            
        move_obj = chess.Move.from_uci(uci_str)
        if move_obj in self.logic_board.legal_moves:
            self.logic_board.push(move_obj)

        # --- LOGIC GIAO DIỆN ---
        prev_ep = self.en_passant_target
        self.en_passant_target = None
        if piece.name == "P" and prev_ep == (x2, y2):
            direction = -1 if piece.color == "white" else 1
            self.board[x2 - direction][y2] = None

        self.board[x2][y2] = piece
        self.board[x1][y1] = None
        self.last_move = ((x1, y1), (x2, y2))
        piece.has_moved = True

        if piece.name == "K" and abs(y2 - y1) == 2:
            if y2 > y1:
                rook = self.board[x2][7]
                self.board[x2][5] = rook
                self.board[x2][7] = None
                if rook: rook.has_moved = True
            else:
                rook = self.board[x2][0]
                self.board[x2][3] = rook
                self.board[x2][0] = None
                if rook: rook.has_moved = True

        if piece.name == "P" and abs(x2 - x1) == 2:
            direction = -1 if piece.color == "white" else 1
            self.en_passant_target = (x1 + direction, y1)

        if piece.name == "P":
            if (piece.color == "white" and x2 == 0) or (piece.color == "black" and x2 == 7):
                self.board[x2][y2] = Piece(piece.color, "Q") 

        if piece.name == "P" or is_capture: self.move_50 = 0
        else: self.move_50 += 1

        self.turn = "black" if self.turn == "white" else "white"

        in_check = self.is_in_check(self.turn)
        has_moves = self.has_any_moves(self.turn)

        # Tránh trùng lặp âm thanh nếu có meme
        play_default_sound = True 
        global current_meme_text
        if current_meme_text in ["BLUNDER!!", "BRILLIANT!!"]:
            play_default_sound = False

        if not has_moves:
            self.game_over = True
            if in_check:
                if sound_mate: sound_mate.play()
                winner = "Trắng" if self.turn == "black" else "Đen"
                self.status_msg = f"Chiếu hết! {winner} thắng!"
            else:
                if sound_move and play_default_sound: sound_move.play()
                self.status_msg = "Hòa (bí nước)!"
        elif in_check:
            if sound_check: sound_check.play()
        elif is_capture:
            if sound_capture and play_default_sound: sound_capture.play()
        else:
            if sound_move and play_default_sound: sound_move.play()

        if self.move_50 >= 100:
            self.status_msg = "Hòa do luật 50 nước!"
            self.game_over = True

        return True

    def draw_board(self, screen):
        screen.fill(COLOR_BG)
        board_rect = pygame.Rect(MARGIN, MARGIN, BOARD_SIZE, BOARD_SIZE)
        pygame.draw.rect(screen, COLOR_DARK, board_rect, 0, 8)

        for row in range(ROWS):
            for col in range(COLS):
                is_light = (row + col) % 2 == 0
                color = COLOR_LIGHT if is_light else COLOR_DARK
                rect = pygame.Rect(MARGIN + col * SQUARE_SIZE, MARGIN + row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)

                if row == 0 and col == 0: pygame.draw.rect(screen, color, rect, 0, border_top_left_radius=8)
                elif row == 0 and col == 7: pygame.draw.rect(screen, color, rect, 0, border_top_right_radius=8)
                elif row == 7 and col == 0: pygame.draw.rect(screen, color, rect, 0, border_bottom_left_radius=8)
                elif row == 7 and col == 7: pygame.draw.rect(screen, color, rect, 0, border_bottom_right_radius=8)
                else: pygame.draw.rect(screen, color, rect)

                if self.last_move and ((row, col) == self.last_move[0] or (row, col) == self.last_move[1]):
                    s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    s.fill(COLOR_LAST_MOVE)
                    screen.blit(s, rect.topleft)

                if self.selected == (row, col):
                    s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    s.fill(COLOR_SELECT)
                    screen.blit(s, rect.topleft)

                piece = self.board[row][col]
                if piece: piece.draw(screen, rect.center)

                if (row, col) in self.valid_moves:
                    s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    pygame.draw.circle(s, COLOR_VALID_DOT, (SQUARE_SIZE // 2, SQUARE_SIZE // 2), SQUARE_SIZE // 6)
                    screen.blit(s, rect.topleft)

    def draw_ui(self, screen):
        ui_x = MARGIN + BOARD_SIZE + 20
        ui_y = MARGIN + 10
        screen.blit(ui_font.render("Meme Chess", True, PIECE_WHITE), (ui_x, ui_y))

        if self.game_over:
            screen.blit(status_font.render(self.status_msg, True, (255, 200, 50)), (ui_x, ui_y + 50))
        else:
            turn_str = "Trắng đi" if self.turn == "white" else "Đen đi"
            turn_color = PIECE_WHITE if self.turn == "white" else (150, 150, 150)
            pygame.draw.rect(screen, turn_color, pygame.Rect(ui_x, ui_y + 40, 20, 20), 0, 10)
            screen.blit(status_font.render(turn_str, True, turn_color), (ui_x + 30, ui_y + 38))
            
            if is_ai:
                you_str = f"(Đấu AI - Bạn là {my_color.title()})"
            elif is_offline:
                you_str = "(Chế độ 2 người chơi)"
            else:
                you_str = f"(Bạn là: {'Trắng' if is_host else 'Đen'})"
                
            screen.blit(status_font.render(you_str, True, (100, 200, 100)), (ui_x, ui_y + 100))
            if self.is_in_check(self.turn):
                screen.blit(status_font.render("⚠ Chiếu!", True, (255, 80, 80)), (ui_x, ui_y + 70))
            
            global ai_thinking
            if is_ai and ai_thinking:
                screen.blit(status_font.render("Máy đang nhẩm cờ...", True, (200, 200, 255)), (ui_x, ui_y + 130))


# --- HÀM CHẤM ĐIỂM VÀ KÍCH HOẠT MEME ---
def evaluate_for_meme(logic_board, move_uci):
    global current_meme_text, current_meme_color, meme_timer
    
    if not sf_engine:
        return

    try:
        move_obj = chess.Move.from_uci(move_uci)
        if move_obj not in logic_board.legal_moves:
            return 
            
        turn_color = logic_board.turn 

        # Dùng time=0.1 theo ý bạn (Stockfish sẽ vắt chân lên cổ tính trong 100ms)
        info_before = sf_engine.analyse(logic_board, chess.engine.Limit(time=0.1))
        score_before = info_before["score"].pov(turn_color).score(mate_score=10000)

        logic_board.push(move_obj)

        info_after = sf_engine.analyse(logic_board, chess.engine.Limit(time=0.1))
        score_after = info_after["score"].pov(turn_color).score(mate_score=10000)

        logic_board.pop()

        # Tính Delta: Số Dương là nước đi khôn, số Âm là đi vào lòng đất
        delta = score_after - score_before 

        # KÍCH HOẠT HIỆU ỨNG MEME
        if delta <= -250: # BLUNDER (Tự dưng làm mất trắng ~2.5 điểm Tốt)
            current_meme_text = "BLUNDER!!"
            current_meme_color = (255, 50, 50) # Đỏ
            meme_timer = 120 # Hiển thị 2 giây
            if sound_blunder: sound_blunder.play()
            
        elif delta >= 200: # BRILLIANT (Pha xử lý xuất thần)
            current_meme_text = "BRILLIANT!!"
            current_meme_color = (50, 200, 200) # Xanh mòng két (Teal)
            meme_timer = 120
            if sound_brilliant: sound_brilliant.play()
            
        elif delta >= 100: # GREAT MOVE (Nước đi Tuyệt vời - Icon Xanh dương)
            current_meme_text = "GREAT MOVE!"
            current_meme_color = (120, 160, 200) # Xanh dương nhạt giống trong ảnh bạn gửi
            meme_timer = 90 # Hiển thị 1.5 giây
            # Có thể thêm dòng gọi âm thanh riêng cho nước đi này nếu bạn có file wav
            
    except Exception as e:
        print("Lỗi chấm điểm Meme:", e)


game = Chess()
clock = pygame.time.Clock()

# --- NETWORK THREAD ---
def receive_moves():
    global game
    while True:
        try:
            data = connection.recv(1024).decode()
            if not data: break
            if data.startswith("MOVE"):
                _, r1, c1, r2, c2 = data.split(",")
                game.move(int(r1), int(c1), int(r2), int(c2))
        except:
            print("Mất kết nối với đối thủ!")
            break

if not is_offline and connection:
    thread = threading.Thread(target=receive_moves, daemon=True)
    thread.start()

# --- AI THREAD ---
ai_thinking = False
ai_move_ready = None

def ai_worker():
    global ai_thinking, ai_move_ready
    try:
        if sf_engine:
            # Dùng Stockfish để AI đánh luôn cho mượt (Nghĩ 0.1s là đủ hủy diệt rồi)
            # Giới hạn độ sâu suy nghĩ ở mức 3 (depth=3)
            result = sf_engine.play(game.logic_board, chess.engine.Limit(depth=6))
            best_move = result.move
            
            if best_move:
                f_sq = best_move.from_square
                t_sq = best_move.to_square
                r1, c1 = 7 - (f_sq // 8), f_sq % 8
                r2, c2 = 7 - (t_sq // 8), t_sq % 8
                ai_move_ready = (r1, c1, r2, c2)
    finally:
        ai_thinking = False

# --- MAIN LOOP ---
while True:
    game.draw_board(screen)
    game.draw_ui(screen)

    # --- HIỂN THỊ TEXT MEME ---
    if meme_timer > 0:
        # Tính toán để hiện chữ to đùng ở giữa bàn cờ
        text_surf = meme_font.render(current_meme_text, True, current_meme_color)
        
        # Tạo viền đen cho chữ dễ đọc
        outline_surf = meme_font.render(current_meme_text, True, (0, 0, 0))
        text_x = MARGIN + (BOARD_SIZE // 2) - (text_surf.get_width() // 2)
        text_y = MARGIN + (BOARD_SIZE // 2) - (text_surf.get_height() // 2)
        
        # Vẽ viền
        screen.blit(outline_surf, (text_x-2, text_y-2))
        screen.blit(outline_surf, (text_x+2, text_y-2))
        screen.blit(outline_surf, (text_x-2, text_y+2))
        screen.blit(outline_surf, (text_x+2, text_y+2))
        # Vẽ chữ thật
        screen.blit(text_surf, (text_x, text_y))
        
        meme_timer -= 1

    # --- KIỂM TRA LƯỢT AI ---
    if is_ai and not game.game_over and game.turn == ai_color and not ai_thinking and ai_move_ready is None:
        ai_thinking = True
        threading.Thread(target=ai_worker, daemon=True).start()
        
    # --- THỰC HIỆN NƯỚC ĐI CỦA AI ---
    if ai_move_ready is not None:
        r1, c1, r2, c2 = ai_move_ready
        
        # Chấm điểm Meme cho cả nước đi của AI (Cho nó tự mỉa mai nó)
        uci_str = game.get_uci(r1, c1, r2, c2)
        piece = game.board[r1][c1]
        if piece and piece.name == "P" and (r2 == 0 or r2 == 7): uci_str += "q"
        evaluate_for_meme(game.logic_board, uci_str)

        game.move(r1, c1, r2, c2)
        ai_move_ready = None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if connection: connection.close()
            if sf_engine: sf_engine.quit() # Tắt Stockfish khi thoát
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and not game.game_over:
            if is_ai and game.turn == ai_color:
                continue
                
            if is_offline or game.turn == my_color:
                pos = pygame.mouse.get_pos()
                col = (pos[0] - MARGIN) // SQUARE_SIZE
                row = (pos[1] - MARGIN) // SQUARE_SIZE

                if not (0 <= row < 8 and 0 <= col < 8):
                    game.selected = None
                    game.valid_moves = []
                    continue

                if game.selected:
                    r1, c1 = game.selected
                    if (row, col) in game.valid_moves:
                        
                        # TÍNH TOÁN MEME TRƯỚC KHI ĐI THẬT
                        uci_str = game.get_uci(r1, c1, row, col)
                        piece = game.board[r1][c1]
                        if piece.name == "P" and (row == 0 or row == 7): uci_str += "q"
                        evaluate_for_meme(game.logic_board, uci_str)

                        # Thực hiện nước đi
                        game.move(r1, c1, row, col)
                        game.selected = None
                        game.valid_moves = []
                        
                        if not is_offline and connection:
                            try:
                                move_data = f"MOVE,{r1},{c1},{row},{col}"
                                connection.sendall(move_data.encode())
                            except:
                                print("Lỗi gửi dữ liệu qua mạng!")
                    else:
                        piece_clicked = game.board[row][col]
                        if piece_clicked and piece_clicked.color == game.turn:
                            game.selected = (row, col)
                            game.valid_moves = game.get_all_valid_moves(row, col)
                        else:
                            game.selected = None
                            game.valid_moves = []
                else:
                    piece_clicked = game.board[row][col]
                    if piece_clicked and piece_clicked.color == game.turn:
                        game.selected = (row, col)
                        game.valid_moves = game.get_all_valid_moves(row, col)

    pygame.display.update()
    clock.tick(60)