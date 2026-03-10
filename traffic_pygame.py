"""
Simulación de tráfico — Intersección compleja de 4 vías
Visualización con Pygame  →  python traffic_pygame.py

Controles:
    SPACE          Pausar / Continuar
    R              Reiniciar
    Q / ESC        Salir
"""

import sys
import os
import pygame
import numpy as np

from model.fourway_model import FourWayModel, DEFAULT_PARAMS, ORIGINS

# ── Layout ────────────────────────────────────────────────────────────────────
WIN_SIZE = 680       # píxeles del área de simulación (cuadrada)
SIDE_W   = 240       # ancho del panel lateral
WIN_W    = WIN_SIZE + SIDE_W
WIN_H    = WIN_SIZE

L     = 80.0         # semiancho del mundo en unidades
w     = 3.5          # ancho de carril
SCALE = WIN_SIZE / (2 * L)   # píxeles por unidad de mundo

# ── Paleta ────────────────────────────────────────────────────────────────────
C = dict(
    grass      = ( 74, 124,  89),
    road       = ( 70,  70,  70),
    lane_mark  = (200, 200, 200),
    car_move   = ( 25, 118, 210),
    car_wait   = ( 69,  90, 100),
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
    yellow_l   = (249, 168,  37),
)

LIGHT_CLR = {
    'G':  C["green_l"],
    'Y':  C["yellow_l"],
    'R':  C["red_l"],
    'AR': (20, 20, 20),
}

PHASE_NAMES = ["Norte↓", "Oeste→", "Este↑", "Sur←"]

# ── Imágenes de semáforos (cargadas una vez) ──────────────────────────────────
_SIGNAL_IMGS: dict = {}

def _scale_proportional(img, target_h):
    """Escala manteniendo la proporción original dado un alto objetivo."""
    ow, oh = img.get_size()
    w = max(1, round(ow * target_h / oh))
    return pygame.transform.smoothscale(img, (w, target_h))


def _load_signals():
    """Carga las imágenes de semáforos desde images/signals/."""
    if _SIGNAL_IMGS:
        return
    base = os.path.join(os.path.dirname(__file__), "images", "signals")
    raw = {}
    for name, state in [("green", "G"), ("yellow", "Y"), ("red", "R")]:
        raw[state] = pygame.image.load(os.path.join(base, f"{name}.png")).convert_alpha()
        _SIGNAL_IMGS[f"{state}_small"] = _scale_proportional(raw[state], 36)
        _SIGNAL_IMGS[f"{state}_large"] = _scale_proportional(raw[state], 56)
    # AR (transición) — versión oscurecida del rojo
    for suffix in ("small", "large"):
        base_img = _SIGNAL_IMGS[f"R_{suffix}"].copy()
        dark = pygame.Surface(base_img.get_size(), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 160))
        base_img.blit(dark, (0, 0))
        _SIGNAL_IMGS[f"AR_{suffix}"] = base_img

# ── Conversión de coordenadas ─────────────────────────────────────────────────
def w2s(x, y):
    """Coordenadas de mundo → píxeles de pantalla."""
    return int((x + L) * SCALE), int((L - y) * SCALE)


def w2s_rect(wx, wy, ww, wh):
    """Rectángulo de mundo → pygame.Rect."""
    sx = int((wx + L) * SCALE)
    sy = int((L - (wy + wh)) * SCALE)
    return pygame.Rect(sx, sy, max(1, int(ww * SCALE)), max(1, int(wh * SCALE)))


# ── Geometría de carriles (igual que draw_intersection del notebook) ───────────
ROAD_RECTS = [
    (-L/2 + w*2,  w*14,   L - w*3,  2*w),   # horizontal parcial superior
    (-L/2 + 6,   -w*14,   L - w*3,  2*w),   # horizontal parcial inferior
    (-L,         -w*3,    2*L,       2*w),   # horizontal principal 1
    (-L,         -w*5,    2*L,       2*w),   # horizontal principal 2
    (-L,          w*3,    2*L,       2*w),   # horizontal principal 3
    (-L,          w*5,    2*L,       2*w),   # horizontal principal 4
    (-w*16,      -L,      2*w,       L - w), # vertical corto izquierdo
    ( w*16,      -L,      2*w,       L - w), # vertical corto derecho
    (-w*10,      -L,      2*w,       2*L),   # vertical largo 1
    (-w*12,      -L,      2*w,       2*L),   # vertical largo 2
    ( w*10,      -L,      2*w,       2*L),   # vertical largo 3
    ( w*12,      -L,      2*w,       2*L),   # vertical largo 4
]

# Posiciones de los 4 semáforos representativos (mundo)
LIGHT_LOCS = {
    'O680': ( 0,     w*7),
    'Y468': ( 0,    -w*7),
    'B468': ( w*7,   0),
    'G263': (-w*7,   0),
}


# ── Widgets ───────────────────────────────────────────────────────────────────
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
        if self.toggle and self.active:   bg = C["btn_active"]
        elif self._hover and self.danger: bg = C["btn_dh"]
        elif self._hover:                 bg = C["btn_hover"]
        elif self.danger:                 bg = C["btn_danger"]
        else:                             bg = C["btn"]
        pygame.draw.rect(surf, bg,        self.rect, border_radius=6)
        pygame.draw.rect(surf, C["gray"], self.rect, 1, border_radius=6)
        txt = font.render(self.label, True, C["white"])
        surf.blit(txt, txt.get_rect(center=self.rect.center))


class Stepper:
    def __init__(self, x, y, width, label, value, lo, hi, step, fmt=None):
        self.label = label
        self.value = value
        self.lo, self.hi, self.step = lo, hi, step
        self.fmt   = fmt or (lambda v: str(int(v)))
        bw = 30
        self.btn_minus = Button((x,              y, bw, 28), "−")
        self.btn_plus  = Button((x + width - bw, y, bw, 28), "+")
        self.val_rect  = pygame.Rect(x + bw + 2, y, width - bw*2 - 4, 28)
        self.lbl_rect  = (x, y - 18)

    def handle_event(self, event):
        changed = False
        if self.btn_minus.handle_event(event):
            self.value = max(self.lo, round(self.value - self.step, 6)); changed = True
        if self.btn_plus.handle_event(event):
            self.value = min(self.hi, round(self.value + self.step, 6)); changed = True
        return changed

    def draw(self, surf, font_lbl, font_val):
        surf.blit(font_lbl.render(self.label, True, C["gray"]), self.lbl_rect)
        self.btn_minus.draw(surf, font_val)
        self.btn_plus.draw(surf, font_val)
        pygame.draw.rect(surf, C["panel_line"], self.val_rect, border_radius=4)
        val = font_val.render(self.fmt(self.value), True, C["white"])
        surf.blit(val, val.get_rect(center=self.val_rect.center))


# ── Dibujo ────────────────────────────────────────────────────────────────────
def draw_world(surf, model):
    # Fondo verde (pasto)
    surf.fill(C["grass"], pygame.Rect(0, 0, WIN_SIZE, WIN_H))

    # Carriles
    for (wx, wy, ww, wh) in ROAD_RECTS:
        pygame.draw.rect(surf, C["road"], w2s_rect(wx, wy, ww, wh))

    # Semáforos
    _load_signals()
    lights = model.ctrl.lights()
    for d, (wx, wy) in LIGHT_LOCS.items():
        sx, sy = w2s(wx, wy)
        state = lights.get(d, 'R')
        img = _SIGNAL_IMGS.get(f"{state}_small", _SIGNAL_IMGS["R_small"])
        surf.blit(img, (sx - img.get_width() // 2, sy - img.get_height() // 2))

    # Coches
    for car in model.cars:
        sx, sy = w2s(car.pos[0], car.pos[1])
        color  = C["car_move"] if car.state == 'moving' else C["car_wait"]
        pygame.draw.circle(surf, color,   (sx, sy), 5)
        pygame.draw.circle(surf, (0,0,0), (sx, sy), 5, 1)
        # Flecha de dirección
        dx, dy = int(car.dir[0]), int(car.dir[1])
        tip = (sx + dx * 8, sy - dy * 8)
        pygame.draw.line(surf, C["white"], (sx, sy), tip, 2)


def draw_panel(surf, model, ui, paused, font_title, font_lbl, font_val):
    pygame.draw.rect(surf, C["panel_bg"],  pygame.Rect(WIN_SIZE, 0, SIDE_W, WIN_H))
    pygame.draw.line(surf, C["panel_line"], (WIN_SIZE, 0), (WIN_SIZE, WIN_H), 1)

    X  = WIN_SIZE + 14
    CX = WIN_SIZE + SIDE_W // 2

    # Título
    t = font_title.render("INTERSECCIÓN COMPLEJA", True, C["title"])
    surf.blit(t, (CX - t.get_width()//2, 10))

    # Indicador de fase del semáforo
    phase_name = PHASE_NAMES[model.ctrl.phase]
    sub        = model.ctrl.sub
    _load_signals()
    img = _SIGNAL_IMGS.get(f"{sub}_large", _SIGNAL_IMGS["R_large"])
    surf.blit(img, (CX - img.get_width() // 2, 52 - img.get_height() // 2))
    pt = font_lbl.render(f"Fase: {phase_name} ({sub})", True, C["gray"])
    surf.blit(pt, pt.get_rect(centerx=CX, y=70))

    # Estadísticas
    total_created = sum(model.spawn_counts.values())
    active_cars   = len(model.cars)
    y = 95
    for lbl, val in [
        ("Paso",         str(model.t)),
        ("Creados",      str(total_created)),
        ("Completados",  str(model.throughput)),
        ("En ruta",      str(active_cars)),
        ("Velocidad",    f"{ui['fps']} fps"),
    ]:
        surf.blit(font_lbl.render(lbl, True, C["gray"]),  (X, y))
        vs = font_val.render(val, True, C["white"])
        surf.blit(vs, (WIN_SIZE + SIDE_W - vs.get_width() - 14, y))
        y += 20
    pygame.draw.line(surf, C["panel_line"], (X, y + 2), (WIN_SIZE + SIDE_W - 14, y + 2), 1)

    # Steppers y botones
    for stp in ui["steppers"]:
        stp.draw(surf, font_lbl, font_val)
    for btn in ui["buttons"]:
        btn.draw(surf, font_val)

    # Estado pausa
    estado = "⏸ PAUSADO" if paused else "▶ Corriendo"
    ec = C["yellow"] if paused else C["green_l"]
    es = font_lbl.render(estado, True, ec)
    surf.blit(es, es.get_rect(centerx=CX, y=WIN_H - 20))


# ── UI ────────────────────────────────────────────────────────────────────────
def build_ui():
    X  = WIN_SIZE + 14
    SW = SIDE_W - 28

    steppers = [
        Stepper(X, 248, SW, "Verde NS (ticks)",  10,  3, 30, 1),
        Stepper(X, 308, SW, "Verde EW (ticks)",  10,  3, 30, 1),
        Stepper(X, 368, SW, "Intervalo autos",    5,  1, 20, 1),
        Stepper(X, 428, SW, "Velocidad (fps)",    8,  1, 30, 1),
    ]
    BH = 36
    buttons = [
        Button((X, 488,        SW, BH), "⏸  Pausar / Continuar", toggle=True),
        Button((X, 488+BH+8,   SW, BH), "↺  Reiniciar",          danger=True),
    ]
    return {"steppers": steppers, "buttons": buttons, "fps": 8}


def make_model(ui):
    p = dict(DEFAULT_PARAMS)
    p['green_ns'] = int(ui["steppers"][0].value)
    p['green_ew'] = int(ui["steppers"][1].value)
    interval      = int(ui["steppers"][2].value)
    for origin in ORIGINS:
        p[f'interval_{origin}'] = interval
    p['interval_G680'] = 0   # G680 desactivado en original
    model = FourWayModel(p)
    model.t = 0
    model.setup()
    return model


# ── Bucle principal ───────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Tráfico — Intersección Compleja")

    font_title = pygame.font.SysFont("Arial", 13, bold=True)
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

            for stp in ui["steppers"]:
                stp.handle_event(event)

            if btn_pause.handle_event(event):
                paused = btn_pause.active
            if btn_restart.handle_event(event):
                model  = make_model(ui)
                paused = False
                btn_pause.active = False

        ui["fps"] = int(stp_fps.value)

        if not paused:
            model.t += 1
            model.step()

        draw_world(screen, model)
        draw_panel(screen, model, ui, paused, font_title, font_lbl, font_val)
        pygame.display.flip()
        clock.tick(ui["fps"])

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
