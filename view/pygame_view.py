"""
Visualización pygame de la intersección en cruz.
"""

import sys
import pygame

from model.agents import Car, TrafficLight, RIGHT, LEFT, UP, DOWN

# ── Layout ────────────────────────────────────────────────────────────────────
CELL       = 40
SIDE_W     = 230
GRID_CELLS = 17

GRID_PX = GRID_CELLS * CELL
WIN_W   = GRID_PX + SIDE_W
WIN_H   = GRID_PX

# ── Paleta ────────────────────────────────────────────────────────────────────
C = dict(
    grass      = ( 74, 124,  89),
    road       = ( 75,  75,  75),
    inter      = ( 58,  58,  58),
    lane       = (210, 210, 210),
    stop       = (210,  40,  40),
    panel_bg   = ( 22,  22,  22),
    panel_line = ( 55,  55,  55),
    btn        = ( 55,  55,  55),
    btn_hover  = ( 85,  85,  85),
    btn_active = ( 35, 120,  55),
    btn_danger = (130,  35,  35),
    btn_dh     = (160,  55,  55),
    white      = (255, 255, 255),
    gray       = (160, 160, 160),
    yellow     = (233, 196, 106),
    title      = (200, 200, 200),
    green_l    = (  0, 200,  70),
    red_l      = (210,  30,  30),
)

CAR_CLR  = {RIGHT: (230, 57, 70), LEFT: (69, 123, 157),
            UP: (42, 157, 143),   DOWN: (233, 196, 106)}
CAR_WAIT = (130, 130, 130)
ARROW_VEC = {RIGHT: (1, 0), LEFT: (-1, 0), UP: (0, -1), DOWN: (0, 1)}


# ══════════════════════════════════════════════════════════════════════════════
#  Widgets
# ══════════════════════════════════════════════════════════════════════════════
class Button:
    def __init__(self, rect, label, *, toggle=False, danger=False):
        self.rect   = pygame.Rect(rect)
        self.label  = label
        self.toggle = toggle
        self.danger = danger
        self.active = False
        self._hover = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.toggle:
                    self.active = not self.active
                return True
        return False

    def draw(self, surf, font):
        if self.toggle and self.active:
            bg = C["btn_active"]
        elif self._hover and self.danger:
            bg = C["btn_dh"]
        elif self._hover:
            bg = C["btn_hover"]
        elif self.danger:
            bg = C["btn_danger"]
        else:
            bg = C["btn"]
        pygame.draw.rect(surf, bg,        self.rect, border_radius=6)
        pygame.draw.rect(surf, C["gray"], self.rect, 1, border_radius=6)
        txt = font.render(self.label, True, C["white"])
        surf.blit(txt, txt.get_rect(center=self.rect.center))


class Stepper:
    """[ − ]  valor  [ + ] con etiqueta y límites."""

    def __init__(self, x, y, w, label, value, lo, hi, step, fmt=None):
        self.label = label
        self.value = value
        self.lo, self.hi, self.step = lo, hi, step
        self.fmt   = fmt or (lambda v: str(v))
        bw = 30
        self.btn_minus = Button((x,          y, bw, 28), "−")
        self.btn_plus  = Button((x + w - bw, y, bw, 28), "+")
        self.val_rect  = pygame.Rect(x + bw + 2, y, w - bw * 2 - 4, 28)
        self.lbl_rect  = (x, y - 18)

    def handle_event(self, event):
        changed = False
        if self.btn_minus.handle_event(event):
            self.value = max(self.lo, round(self.value - self.step, 6))
            changed = True
        if self.btn_plus.handle_event(event):
            self.value = min(self.hi, round(self.value + self.step, 6))
            changed = True
        return changed

    def draw(self, surf, font_lbl, font_val):
        surf.blit(font_lbl.render(self.label, True, C["gray"]), self.lbl_rect)
        self.btn_minus.draw(surf, font_val)
        self.btn_plus.draw(surf, font_val)
        pygame.draw.rect(surf, C["panel_line"], self.val_rect, border_radius=4)
        val = font_val.render(self.fmt(self.value), True, C["white"])
        surf.blit(val, val.get_rect(center=self.val_rect.center))


# ══════════════════════════════════════════════════════════════════════════════
#  Dibujo de la intersección
# ══════════════════════════════════════════════════════════════════════════════
def _cell_center(x, y):
    return (x * CELL + CELL // 2,
            (GRID_CELLS - 1 - y) * CELL + CELL // 2)


def draw_world(surf, model):
    cx, cy = model.cx, model.cy

    surf.fill(C["grass"], pygame.Rect(0, 0, GRID_PX, GRID_PX))

    h_road = pygame.Rect(0,          (GRID_CELLS - cy - 2) * CELL, GRID_PX,  3 * CELL)
    v_road = pygame.Rect((cx-1)*CELL, 0,                            3 * CELL, GRID_PX)
    pygame.draw.rect(surf, C["road"],  h_road)
    pygame.draw.rect(surf, C["road"],  v_road)
    pygame.draw.rect(surf, C["inter"],
                     pygame.Rect((cx-1)*CELL, (GRID_CELLS - cy - 2)*CELL, 3*CELL, 3*CELL))

    # Líneas discontinuas horizontales
    py_h = (GRID_CELLS - cy - 1) * CELL + CELL // 2
    for x in range(GRID_CELLS):
        if cx - 1 <= x <= cx + 1:
            continue
        px = x * CELL
        pygame.draw.line(surf, C["lane"], (px+6, py_h), (px+CELL-6, py_h), 1)

    # Líneas discontinuas verticales
    px_v = cx * CELL + CELL // 2
    for y in range(GRID_CELLS):
        if cy - 1 <= y <= cy + 1:
            continue
        py = (GRID_CELLS - y - 1) * CELL
        pygame.draw.line(surf, C["lane"], (px_v, py+6), (px_v, py+CELL-6), 1)

    # Líneas de parada
    lx  = (cx - 1) * CELL
    rx  = (cx + 2) * CELL
    ty  = (GRID_CELLS - cy - 2) * CELL
    by_ = (GRID_CELLS - cy + 1) * CELL
    pygame.draw.line(surf, C["stop"], (lx, ty), (lx, by_), 2)
    pygame.draw.line(surf, C["stop"], (rx, ty), (rx, by_), 2)
    pygame.draw.line(surf, C["stop"], (lx, ty), (rx, ty),  2)
    pygame.draw.line(surf, C["stop"], (lx, by_), (rx, by_), 2)

    # Coches
    PAD = 5
    for agent in model.agents:
        if not isinstance(agent, Car):
            continue
        px, py = _cell_center(*agent.pos)
        color  = CAR_WAIT if agent.waiting else CAR_CLR[agent.direction]

        if agent.direction in (UP, DOWN):
            cw, ch = CELL - PAD*2 - 4, CELL - PAD*2
        else:
            cw, ch = CELL - PAD*2, CELL - PAD*2 - 4

        rect = pygame.Rect(px - cw//2, py - ch//2, cw, ch)
        pygame.draw.rect(surf, color,   rect, border_radius=4)
        pygame.draw.rect(surf, (0,0,0), rect, 1, border_radius=4)

        dvx, dvy = ARROW_VEC[agent.direction]
        tip  = (px + dvx*(cw//2 - 2), py + dvy*(ch//2 - 2))
        base = (px - dvx*4,           py - dvy*4)
        pygame.draw.line(surf, C["white"], base, tip, 2)
        p2 = (tip[0] - dvx*5 + (-dvy)*3, tip[1] - dvy*5 + dvx*3)
        p3 = (tip[0] - dvx*5 - (-dvy)*3, tip[1] - dvy*5 - dvx*3)
        pygame.draw.polygon(surf, C["white"], [tip, p2, p3])

    # Semáforo
    light = model.traffic_light
    lx_s, ly_s = _cell_center(cx, cy)
    clr = C["green_l"] if light.green_h else C["red_l"]
    pygame.draw.circle(surf, (15, 15, 15), (lx_s, ly_s), CELL//2 - 2)
    pygame.draw.circle(surf, clr,          (lx_s, ly_s), CELL//2 - 6)


# ══════════════════════════════════════════════════════════════════════════════
#  Panel lateral
# ══════════════════════════════════════════════════════════════════════════════
def draw_panel(surf, model, ui, paused, font_title, font_lbl, font_val):
    pygame.draw.rect(surf, C["panel_bg"], pygame.Rect(GRID_PX, 0, SIDE_W, WIN_H))
    pygame.draw.line(surf, C["panel_line"], (GRID_PX, 0), (GRID_PX, WIN_H), 1)

    X  = GRID_PX + 14
    CX = GRID_PX + SIDE_W // 2

    # Título
    t = font_title.render("TRÁFICO", True, C["title"])
    surf.blit(t, (CX - t.get_width()//2, 12))

    # Semáforo mini
    light = model.traffic_light
    lx0 = CX - 26
    pygame.draw.rect(surf, (30,30,30), (lx0, 36, 52, 22), border_radius=4)
    pygame.draw.circle(surf, C["red_l"]   if not light.green_h else (50,50,50), (lx0+10, 47), 7)
    pygame.draw.circle(surf, C["green_l"] if light.green_h     else (50,50,50), (lx0+26, 47), 7)
    pygame.draw.circle(surf, C["green_l"] if light.green_v     else (50,50,50), (lx0+42, 47), 7)
    surf.blit(font_lbl.render("H", True, C["white"]), (lx0+7,  58))
    surf.blit(font_lbl.render("V", True, C["white"]), (lx0+39, 58))

    # Stats
    data = model.datacollector.get_model_vars_dataframe()
    last = data.iloc[-1]
    y = 80
    for lbl, val in [
        ("Paso",       str(model.steps)),
        ("Esperando",  str(int(last["Esperando"]))),
        ("Circulando", str(int(last["Circulando"]))),
        ("Cruzaron",   str(int(last["Cruzaron"]))),
        ("Velocidad",  f"{ui['fps']} fps"),
    ]:
        surf.blit(font_lbl.render(lbl, True, C["gray"]),  (X, y))
        vs = font_val.render(val, True, C["white"])
        surf.blit(vs, (GRID_PX + SIDE_W - vs.get_width() - 14, y))
        y += 20
    pygame.draw.line(surf, C["panel_line"], (X, y+2), (GRID_PX+SIDE_W-14, y+2), 1)

    # Steppers
    for stp in ui["steppers"]:
        stp.draw(surf, font_lbl, font_val)

    # Botones
    for btn in ui["buttons"]:
        btn.draw(surf, font_val)

    # Estado
    estado = "⏸ PAUSADO" if paused else "▶ Corriendo"
    ec = C["yellow"] if paused else C["green_l"]
    es = font_lbl.render(estado, True, ec)
    surf.blit(es, es.get_rect(centerx=CX, y=WIN_H - 20))


# ══════════════════════════════════════════════════════════════════════════════
#  Construcción de la UI
# ══════════════════════════════════════════════════════════════════════════════
def build_ui():
    X  = GRID_PX + 14
    SW = SIDE_W - 28

    steppers = [
        Stepper(X, 248, SW, "Coches iniciales",  8,   0,   40, 1),
        Stepper(X, 308, SW, "Duración semáforo", 6,   2,   20, 1),
        Stepper(X, 368, SW, "Aparición (prob)",  0.3, 0.0, 0.8, 0.05,
                fmt=lambda v: f"{v:.2f}"),
        Stepper(X, 428, SW, "Velocidad (fps)",   6,   1,   30, 1),
    ]
    BH = 36
    buttons = [
        Button((X, 490,        SW, BH), "⏸  Pausar / Continuar", toggle=True),
        Button((X, 490+BH+8,   SW, BH), "↺  Reiniciar",          danger=True),
    ]
    return {"steppers": steppers, "buttons": buttons, "fps": 6}
