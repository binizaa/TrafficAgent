"""
Simulación de tráfico — Intersección en Cruz
Visualización con Pygame  →  python traffic_pygame.py

Panel derecho con todos los controles.
Teclas rápidas: SPACE pausar, R reiniciar, Q salir.
"""

import sys
import pygame

from trafficAgent import IntersectionModel, Car, TrafficLight, RIGHT, LEFT, UP, DOWN

# ══════════════════════════════════════════════════════════════════════════════
#  Constantes de layout
# ══════════════════════════════════════════════════════════════════════════════
CELL       = 40          # píxeles por celda del modelo
SIDE_W     = 230         # ancho del panel lateral
GRID_CELLS = 17          # tamaño del modelo

GRID_PX  = GRID_CELLS * CELL
WIN_W    = GRID_PX + SIDE_W
WIN_H    = GRID_PX

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

CAR_CLR = {RIGHT: (230, 57, 70), LEFT: (69, 123, 157),
           UP: (42, 157, 143), DOWN: (233, 196, 106)}
CAR_WAIT = (130, 130, 130)

ARROW_VEC = {RIGHT: (1, 0), LEFT: (-1, 0), UP: (0, -1), DOWN: (0, 1)}


# ══════════════════════════════════════════════════════════════════════════════
#  Widgets
# ══════════════════════════════════════════════════════════════════════════════
class Button:
    """Botón rectangular con estado hover y toggle opcional."""

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
    """Control  [ − ]  valor  [ + ]  con límites y paso."""

    def __init__(self, x, y, w, label, value, lo, hi, step, fmt=None):
        self.label = label
        self.value = value
        self.lo, self.hi, self.step = lo, hi, step
        self.fmt   = fmt or (lambda v: str(v))
        bw = 30
        self.btn_minus = Button((x,           y, bw, 28), "−")
        self.btn_plus  = Button((x + w - bw,  y, bw, 28), "+")
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
        lbl = font_lbl.render(self.label, True, C["gray"])
        surf.blit(lbl, self.lbl_rect)
        self.btn_minus.draw(surf, font_val)
        self.btn_plus.draw(surf, font_val)
        pygame.draw.rect(surf, C["panel_line"], self.val_rect, border_radius=4)
        val = font_val.render(self.fmt(self.value), True, C["white"])
        surf.blit(val, val.get_rect(center=self.val_rect.center))


# ══════════════════════════════════════════════════════════════════════════════
#  Dibujo de la intersección
# ══════════════════════════════════════════════════════════════════════════════
def cell_center(x, y):
    """Centro en píxeles de la celda del modelo (invierte eje Y)."""
    return (x * CELL + CELL // 2,
            (GRID_CELLS - 1 - y) * CELL + CELL // 2)


def draw_world(surf, model):
    cx, cy = model.cx, model.cy

    # Pasto
    surf.fill(C["grass"], pygame.Rect(0, 0, GRID_PX, GRID_PX))

    # Calles
    h = pygame.Rect(0,       (GRID_CELLS - cy - 2) * CELL, GRID_PX, 3 * CELL)
    v = pygame.Rect((cx-1)*CELL, 0,                          3 * CELL, GRID_PX)
    pygame.draw.rect(surf, C["road"], h)
    pygame.draw.rect(surf, C["road"], v)

    # Zona de cruce más oscura
    inter = pygame.Rect((cx-1)*CELL, (GRID_CELLS - cy - 2)*CELL, 3*CELL, 3*CELL)
    pygame.draw.rect(surf, C["inter"], inter)

    # Líneas de carril discontinuas
    def dash_h(row):
        py = (GRID_CELLS - row - 1) * CELL + CELL // 2
        for x in range(0, GRID_CELLS):
            if cx - 1 <= x <= cx + 1:
                continue
            px = x * CELL
            pygame.draw.line(surf, C["lane"], (px+6, py), (px+CELL-6, py), 1)

    def dash_v(col):
        px = col * CELL + CELL // 2
        for y in range(0, GRID_CELLS):
            if cy - 1 <= y <= cy + 1:
                continue
            py = (GRID_CELLS - y - 1) * CELL
            pygame.draw.line(surf, C["lane"], (px, py+6), (px, py+CELL-6), 1)

    dash_h(cy)        # línea central horizontal
    dash_v(cx)        # línea central vertical

    # Líneas de parada (rojas) en los bordes del cruce
    def stop_line(x0, y0, x1, y1):
        pygame.draw.line(surf, C["stop"],
                         cell_center(x0, y0), cell_center(x1, y1), 2)

    # Entrada RIGHT: borde izquierdo del cruce, carril cy-1
    lx = (cx - 1) * CELL
    t  = (GRID_CELLS - (cy + 2)) * CELL
    b  = (GRID_CELLS - (cy - 1)) * CELL
    pygame.draw.line(surf, C["stop"], (lx, t), (lx, b), 2)          # izquierda
    rx = (cx + 2) * CELL
    pygame.draw.line(surf, C["stop"], (rx, t), (rx, b), 2)          # derecha
    ty = (GRID_CELLS - (cy + 2)) * CELL
    by_ = (GRID_CELLS - (cy - 1)) * CELL
    pygame.draw.line(surf, C["stop"], (lx, ty), (rx, ty), 2)        # arriba
    pygame.draw.line(surf, C["stop"], (lx, by_), (rx, by_), 2)      # abajo

    # ── Coches ────────────────────────────────────────────────────────────────
    PAD = 5
    for agent in model.agents:
        if not isinstance(agent, Car):
            continue
        px, py = cell_center(*agent.pos)
        color  = CAR_WAIT if agent.waiting else CAR_CLR[agent.direction]

        if agent.direction in (UP, DOWN):
            cw, ch = CELL - PAD*2 - 4, CELL - PAD*2
        else:
            cw, ch = CELL - PAD*2, CELL - PAD*2 - 4

        rect = pygame.Rect(px - cw//2, py - ch//2, cw, ch)
        pygame.draw.rect(surf, color,    rect, border_radius=4)
        pygame.draw.rect(surf, (0,0,0),  rect, 1, border_radius=4)

        # Flecha
        dvx, dvy = ARROW_VEC[agent.direction]
        tip  = (px + dvx*(cw//2 - 2), py + dvy*(ch//2 - 2))
        base = (px - dvx*4,           py - dvy*4)
        pygame.draw.line(surf, C["white"], base, tip, 2)
        px2 = (tip[0] - dvx*5 + (-dvy)*3, tip[1] - dvy*5 + dvx*3)
        px3 = (tip[0] - dvx*5 - (-dvy)*3, tip[1] - dvy*5 - dvx*3)
        pygame.draw.polygon(surf, C["white"], [tip, px2, px3])

    # ── Semáforo ──────────────────────────────────────────────────────────────
    light = model.traffic_light
    lx, ly = cell_center(cx, cy)
    clr = C["green_l"] if light.green_h else C["red_l"]
    pygame.draw.circle(surf, (15, 15, 15), (lx, ly), CELL//2 - 2)
    pygame.draw.circle(surf, clr,          (lx, ly), CELL//2 - 6)


# ══════════════════════════════════════════════════════════════════════════════
#  Panel lateral
# ══════════════════════════════════════════════════════════════════════════════
def draw_side_panel(surf, model, ui, paused, font_title, font_lbl, font_val):
    panel = pygame.Rect(GRID_PX, 0, SIDE_W, WIN_H)
    pygame.draw.rect(surf, C["panel_bg"], panel)
    pygame.draw.line(surf, C["panel_line"], (GRID_PX, 0), (GRID_PX, WIN_H), 1)

    X = GRID_PX + 14

    # ── Título ──────────────────────────────────────────────────────────────
    t = font_title.render("TRÁFICO", True, C["title"])
    surf.blit(t, (GRID_PX + SIDE_W//2 - t.get_width()//2, 12))

    # ── Semáforo visual mini ─────────────────────────────────────────────────
    light = model.traffic_light
    lx0 = GRID_PX + SIDE_W//2 - 26
    pygame.draw.rect(surf, (30,30,30), (lx0, 36, 52, 22), border_radius=4)
    gh = C["green_l"] if light.green_h  else (50,50,50)
    gv = C["green_l"] if light.green_v  else (50,50,50)
    rh = C["red_l"]   if not light.green_h else (50,50,50)
    rv = C["red_l"]   if not light.green_v  else (50,50,50)
    pygame.draw.circle(surf, rh, (lx0+10, 47), 7)
    pygame.draw.circle(surf, gh, (lx0+26, 47), 7)
    pygame.draw.circle(surf, gv, (lx0+42, 47), 7)
    hl = font_lbl.render("H", True, C["white"]); surf.blit(hl, (lx0+7, 58))
    vl = font_lbl.render("V", True, C["white"]); surf.blit(vl, (lx0+39, 58))

    # ── Stats ────────────────────────────────────────────────────────────────
    data = model.datacollector.get_model_vars_dataframe()
    last = data.iloc[-1]
    stats = [
        ("Paso",       f"{model.steps}"),
        ("Esperando",  f"{int(last['Esperando'])}"),
        ("Circulando", f"{int(last['Circulando'])}"),
        ("Cruzaron",   f"{int(last['Cruzaron'])}"),
        ("Velocidad",  f"{ui['fps']} fps"),
    ]
    y = 80
    for lbl, val in stats:
        ls = font_lbl.render(lbl, True, C["gray"])
        vs = font_val.render(val, True, C["white"])
        surf.blit(ls, (X, y))
        surf.blit(vs, (GRID_PX + SIDE_W - vs.get_width() - 14, y))
        y += 20
    pygame.draw.line(surf, C["panel_line"], (X, y+2), (GRID_PX+SIDE_W-14, y+2), 1)

    # ── Steppers ────────────────────────────────────────────────────────────
    for stp in ui["steppers"]:
        stp.draw(surf, font_lbl, font_val)

    # ── Botones de acción ────────────────────────────────────────────────────
    for btn in ui["buttons"]:
        btn.draw(surf, font_val)

    # Estado pausa
    estado = "⏸ PAUSADO" if paused else "▶ Corriendo"
    ec = C["yellow"] if paused else C["green_l"]
    es = font_lbl.render(estado, True, ec)
    surf.blit(es, es.get_rect(centerx=GRID_PX + SIDE_W//2, y=WIN_H - 20))


# ══════════════════════════════════════════════════════════════════════════════
#  Construcción de la UI
# ══════════════════════════════════════════════════════════════════════════════
def build_ui():
    X = GRID_PX + 14
    SW = SIDE_W - 28   # ancho útil del panel

    steppers = [
        Stepper(X, 248, SW, "Coches iniciales", 8,   0, 40, 1),
        Stepper(X, 308, SW, "Duración semáforo", 6,  2, 20, 1),
        Stepper(X, 368, SW, "Aparición (prob)",  0.3, 0.0, 0.8, 0.05,
                fmt=lambda v: f"{v:.2f}"),
        Stepper(X, 428, SW, "Velocidad (fps)",   6,   1, 30, 1),
    ]

    BH = 36
    buttons = [
        Button((X, 490, SW, BH),        "⏸  Pausar / Continuar", toggle=True),
        Button((X, 490+BH+8, SW, BH),   "↺  Reiniciar",          danger=True),
    ]

    return {"steppers": steppers, "buttons": buttons, "fps": 6}


# ══════════════════════════════════════════════════════════════════════════════
#  Bucle principal
# ══════════════════════════════════════════════════════════════════════════════
def make_model(ui):
    nc  = int(ui["steppers"][0].value)
    gt  = int(ui["steppers"][1].value)
    sr  = ui["steppers"][2].value
    return IntersectionModel(GRID_CELLS, gt, nc, sr)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Tráfico — Intersección en Cruz")

    font_title = pygame.font.SysFont("Arial", 16, bold=True)
    font_lbl   = pygame.font.SysFont("Arial", 12)
    font_val   = pygame.font.SysFont("Arial", 13, bold=True)

    ui     = build_ui()
    model  = make_model(ui)
    paused = False
    clock  = pygame.time.Clock()

    btn_pause   = ui["buttons"][0]
    btn_restart = ui["buttons"][1]
    stp_fps     = ui["steppers"][3]

    running = True
    while running:
        # ── Eventos ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                    btn_pause.active = paused
                elif event.key == pygame.K_r:
                    model  = make_model(ui)
                    paused = False
                    btn_pause.active = False

            # Steppers
            for stp in ui["steppers"]:
                if stp.handle_event(event):
                    ui["fps"] = int(stp_fps.value)

            # Botones
            if btn_pause.handle_event(event):
                paused = btn_pause.active
            if btn_restart.handle_event(event):
                model  = make_model(ui)
                paused = False
                btn_pause.active = False

        # ── Paso del modelo ───────────────────────────────────────────────────
        if not paused:
            model.step()

        ui["fps"] = int(stp_fps.value)

        # ── Dibujo ────────────────────────────────────────────────────────────
        draw_world(screen, model)
        draw_side_panel(screen, model, ui, paused,
                        font_title, font_lbl, font_val)

        pygame.display.flip()
        clock.tick(ui["fps"])

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
