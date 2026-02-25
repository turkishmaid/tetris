#!/usr/bin/env python3
"""
Console Snake (blessed) – Regenbogen‑Verlauf, flicker‑frei.
Steuerung:
  ← → ↑ ↓   oder  a d w s   – Richtung ändern
  q                – Beenden
"""

import sys
import time
from blessed import Terminal

term = Terminal()

# ----------------------------------------------------------------------
# Spielfeld‑Größe (ganzer Terminal‑Bereich, letzte Zeile für Status)
# ----------------------------------------------------------------------
BOARD_WIDTH = term.width
BOARD_HEIGHT = term.height - 1   # letzte Zeile für UI

# ----------------------------------------------------------------------
# Richtungsvektoren
# ----------------------------------------------------------------------
DIRS = {
    "LEFT":  (-1, 0),
    "RIGHT": ( 1, 0),
    "UP":    ( 0,-1),
    "DOWN":  ( 0, 1),
}
OPPOSITE = {"LEFT": "RIGHT", "RIGHT": "LEFT", "UP": "DOWN", "DOWN": "UP"}

# ----------------------------------------------------------------------
# Hilfsfunktionen
# ----------------------------------------------------------------------
def init_snake() -> list[tuple[int, int]]:
    """Erzeugt eine kurze Schlange, die mittig im Feld startet."""
    cx = BOARD_WIDTH // 2
    cy = BOARD_HEIGHT // 2
    # Startlänge 3, Richtung rechts
    return [(cx, cy), (cx - 1, cy), (cx - 2, cy)]

def hsv_to_256color(h: float, s: float = 1.0, v: float = 1.0) -> str:
    """Konvertiert HSV (Hue 0‑360) in einen 256‑Palette‑Index und gibt das Blessed‑Farb‑Objekt."""
    c = v * s
    h_mod = (h / 60) % 6
    x = c * (1 - abs(h_mod % 2 - 1))
    m = v - c

    if 0 <= h_mod < 1:
        rp, gp, bp = c, x, 0
    elif 1 <= h_mod < 2:
        rp, gp, bp = x, c, 0
    elif 2 <= h_mod < 3:
        rp, gp, bp = 0, c, x
    elif 3 <= h_mod < 4:
        rp, gp, bp = 0, x, c
    elif 4 <= h_mod < 5:
        rp, gp, bp = x, 0, c
    else:  # 5 ≤ h_mod < 6
        rp, gp, bp = c, 0, x

    r = int((rp + m) * 255)
    g = int((gp + m) * 255)
    b = int((bp + m) * 255)

    # 256‑Palette: 16‑231 ist ein 6×6×6 Farb‑Würfel
    r6 = int(r / 51)   # 0‑5
    g6 = int(g / 51)
    b6 = int(b / 51)
    idx = 16 + 36 * r6 + 6 * g6 + b6
    return term.color(idx)

def colour_for_segment(index: int, length: int) -> str:
    """
    Regenbogen‑Verlauf von Rot (Hue 0°) bis Violett (Hue 300°).
    Der Kopf ist immer helles Rot, der Schwanz fast Violett.
    """
    if length == 1:
        hue = 0
    else:
        hue = (index / (length - 1)) * 300   # linear von 0° → 300°
    return hsv_to_256color(hue)

def draw(snake: list[tuple[int, int]], direction: str, score: int) -> None:
    """Rendert das komplette Bild ohne das Terminal zu löschen."""
    # Cursor nach links oben setzen
    print(term.home, end="")

    # Mapping Position → Index, damit wir die richtige Farbe erhalten können
    pos_to_idx = {pos: i for i, pos in enumerate(snake)}
    snake_len = len(snake)

    for y in range(BOARD_HEIGHT):
        line = ""
        for x in range(BOARD_WIDTH):
            idx = pos_to_idx.get((x, y))
            if idx is not None:
                colour = colour_for_segment(idx, snake_len)
                line += colour + "█" + term.normal
            else:
                # Leere Zellen – ein schwarzer Hintergrund‑Space
                line += term.on_black + " " + term.normal
        # Zeile ausgeben (inkl. Zeilenumbruch)
        print(line)

    # Status‑Zeile (unterste Zeile) – ohne nachfolgenden Zeilenumbruch,
    # damit das Terminal nicht scrollt.
    status = f"Score: {score}   Dir: {direction}   q: quit"
    print(term.move_xy(0, BOARD_HEIGHT) + term.clear_eol + status, end="")

    # Sicherstellen, dass alles sofort auf dem Terminal erscheint
    sys.stdout.flush()

# ----------------------------------------------------------------------
# Haupt‑Game‑Loop
# ----------------------------------------------------------------------
def main() -> None:
    snake = init_snake()
    direction = "RIGHT"
    move_counter = 0
    score = 0
    speed = 0.12                    # Sekunden pro automatischen Schritt

    last_tick = time.time()

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        while True:
            # ------------------- Eingabe -------------------
            key = term.inkey(timeout=0.01)
            if key.name in ("KEY_LEFT", "KEY_A"):
                if direction != "RIGHT":
                    direction = "LEFT"
            elif key.name in ("KEY_RIGHT", "KEY_D"):
                if direction != "LEFT":
                    direction = "RIGHT"
            elif key.name in ("KEY_UP", "KEY_W"):
                if direction != "DOWN":
                    direction = "UP"
            elif key.name in ("KEY_DOWN", "KEY_S"):
                if direction != "UP":
                    direction = "DOWN"
            elif key == "q":
                break

            # ------------------- Automatischer Schritt -------------------
            now = time.time()
            if now - last_tick >= speed:
                last_tick = now
                move_counter += 1

                dx, dy = DIRS[direction]
                head_x, head_y = snake[0]
                new_head = (head_x + dx, head_y + dy)

                # Wand‑Kollision
                if not (0 <= new_head[0] < BOARD_WIDTH and 0 <= new_head[1] < BOARD_HEIGHT):
                    draw(snake, direction, score)
                    print(term.move_xy(0, BOARD_HEIGHT + 1) + term.bold_red("Game Over – Wand getroffen.") + term.normal)
                    term.inkey()
                    break

                # Selbst‑Kollision
                if new_head in snake:
                    draw(snake, direction, score)
                    print(term.move_xy(0, BOARD_HEIGHT + 1) + term.bold_red("Game Over – Selbstkollision.") + term.normal)
                    term.inkey()
                    break

                # Neuen Kopf einfügen
                snake.insert(0, new_head)

                # Wachstum: jede zweite Bewegung wird kein Schwanz entfernt → Schlange wird länger
                if move_counter % 2 == 0:
                    snake.pop()          # normaler Schritt
                else:
                    score += 1           # Wachstumsschritt

                # Bild aktualisieren
                draw(snake, direction, score)

if __name__ == "__main__":
    main()