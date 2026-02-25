#!/usr/bin/env python3
"""
Console Tetris using blessed.
Run with: python3 tetris.py
Requires: pip install blessed
"""

import random
import time
from blessed import Terminal

# ----------------------------------------------------------------------
# Game configuration
# ----------------------------------------------------------------------
BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# Tetromino definitions – each piece has four rotation states.
# Each state is a list of (x, y) offsets within a 4×4 grid.
TETROMINOS = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

# Map piece name → 256‑color index (approximate). 0 = black.
PIECE_COLORS = {
    "I": 6,   # cyan
    "O": 3,   # yellow
    "T": 5,   # magenta
    "S": 2,   # green
    "Z": 1,   # red
    "J": 4,   # blue
    "L": 208, # orange (bright)
}


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def create_board():
    """Return a fresh empty board (list of rows)."""
    return [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]


def can_place(board, shape, pos):
    """True iff shape can sit at pos without colliding or leaving the board."""
    ox, oy = pos
    for x, y in shape:
        ax, ay = x + ox, y + oy
        if not (0 <= ax < BOARD_WIDTH and 0 <= ay < BOARD_HEIGHT):
            return False
        if board[ay][ax] is not None:
            return False
    return True


def lock_piece(board, shape, pos, piece):
    """Write the piece into the board permanently."""
    ox, oy = pos
    for x, y in shape:
        board[y + oy][x + ox] = piece


def clear_full_lines(board):
    """Remove completed rows, return (new_board, cleared_count)."""
    new_board = [row for row in board if any(cell is None for cell in row)]
    cleared = BOARD_HEIGHT - len(new_board)
    for _ in range(cleared):
        new_board.insert(0, [None] * BOARD_WIDTH)
    return new_board, cleared


def draw_board(term, board, shape, pos, piece):
    """Render the board + the falling piece."""
    # Clear screen once per frame
    print(term.home + term.clear)

    left = 2   # left margin (in characters)
    top = 1    # top margin (in lines)

    for y in range(BOARD_HEIGHT):
        line = ""
        for x in range(BOARD_WIDTH):
            cell = board[y][x]
            # Overlay the active piece if it occupies this cell
            if shape and (x - pos[0], y - pos[1]) in shape:
                cell = piece
            if cell is None:
                line += term.on_black + "  " + term.normal
            else:
                color = PIECE_COLORS[cell]
                line += term.on_color(color) + "  " + term.normal
        print(term.move_xy(left, top + y) + line)

    # Footer with controls
    print(
        term.move_xy(left, top + BOARD_HEIGHT + 1)
        + term.bold("Controls: ← → ↓ ↑ rotate, space drop, q quit")
    )


# ----------------------------------------------------------------------
# Main game loop
# ----------------------------------------------------------------------
def main():
    term = Terminal()
    board = create_board()
    score = 0
    level = 1
    total_cleared = 0
    fall_interval = 0.5  # seconds per automatic drop

    # Current piece state
    piece = None
    rotation = 0
    shape = None
    pos = (0, 0)

    def spawn():
        """Pick a new tetromino and place it at the top."""
        nonlocal piece, rotation, shape, pos
        piece = random.choice(list(TETROMINOS.keys()))
        rotation = 0
        shape = TETROMINOS[piece][rotation]
        # Center horizontally; the 4×4 grid is anchored at (0,0)
        pos = (BOARD_WIDTH // 2 - 2, 0)
        return can_place(board, shape, pos)

    if not spawn():
        print(term.clear + term.move_xy(0, 0) + "Game Over! (board too small)")
        return

    last_fall = time.time()

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        while True:
            # ------------------- Input -------------------
            key = term.inkey(timeout=0.05)

            if key.name == "KEY_LEFT":
                new_pos = (pos[0] - 1, pos[1])
                if can_place(board, shape, new_pos):
                    pos = new_pos
            elif key.name == "KEY_RIGHT":
                new_pos = (pos[0] + 1, pos[1])
                if can_place(board, shape, new_pos):
                    pos = new_pos
            elif key.name == "KEY_DOWN":
                new_pos = (pos[0], pos[1] + 1)
                if can_place(board, shape, new_pos):
                    pos = new_pos
                else:
                    # lock and spawn next
                    lock_piece(board, shape, pos, piece)
                    board, cleared = clear_full_lines(board)
                    if cleared:
                        total_cleared += cleared
                        score += (cleared ** 2) * 100
                        level = total_cleared // 10 + 1
                        fall_interval = max(0.1, 0.5 - (level - 1) * 0.04)
                    if not spawn():
                        draw_board(term, board, None, None, None)
                        print(
                            term.move_xy(2, BOARD_HEIGHT + 3)
                            + term.bold_red(f"Game Over! Final Score: {score}")
                        )
                        term.inkey()
                        break
            elif key.name == "KEY_UP" or key == "w":
                # rotate clockwise
                next_rot = (rotation + 1) % len(TETROMINOS[piece])
                next_shape = TETROMINOS[piece][next_rot]
                if can_place(board, next_shape, pos):
                    rotation = next_rot
                    shape = next_shape
            elif key == " ":
                # hard drop
                while can_place(board, shape, (pos[0], pos[1] + 1)):
                    pos = (pos[0], pos[1] + 1)
                lock_piece(board, shape, pos, piece)
                board, cleared = clear_full_lines(board)
                if cleared:
                    total_cleared += cleared
                    score += (cleared ** 2) * 100
                    level = total_cleared // 10 + 1
                    fall_interval = max(0.1, 0.5 - (level - 1) * 0.04)
                if not spawn():
                    draw_board(term, board, None, None, None)
                    print(
                        term.move_xy(2, BOARD_HEIGHT + 3)
                        + term.bold_red(f"Game Over! Final Score: {score}")
                    )
                    term.inkey()
                    break
            elif key == "q":
                break

            # ------------------- Automatic fall -------------------
            now = time.time()
            if now - last_fall >= fall_interval:
                new_pos = (pos[0], pos[1] + 1)
                if can_place(board, shape, new_pos):
                    pos = new_pos
                else:
                    lock_piece(board, shape, pos, piece)
                    board, cleared = clear_full_lines(board)
                    if cleared:
                        total_cleared += cleared
                        score += (cleared ** 2) * 100
                        level = total_cleared // 10 + 1
                        fall_interval = max(0.1, 0.5 - (level - 1) * 0.04)
                    if not spawn():
                        draw_board(term, board, None, None, None)
                        print(
                            term.move_xy(2, BOARD_HEIGHT + 3)
                            + term.bold_red(f"Game Over! Final Score: {score}")
                        )
                        term.inkey()
                        break
                last_fall = now

            # ------------------- Render -------------------
            draw_board(term, board, shape, pos, piece)
            print(
                term.move_xy(2, BOARD_HEIGHT + 2)
                + term.bold(f"Score: {score}  Level: {level}")
            )


if __name__ == "__main__":
    main()

