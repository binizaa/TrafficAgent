# ── CONFIGURACIÓN GLOBAL ──────────────────────────────────────────────────────

# Ventana
SIM_SIZE = 800   # Área de simulación (cuadrada)
UI_WIDTH = 300   # Panel lateral
WINDOW_W = SIM_SIZE + UI_WIDTH
WINDOW_H = SIM_SIZE
MARGIN   = 40

# ── COLORES ───────────────────────────────────────────────────────────────────
BG_COLOR     = (34, 34, 34)
ROAD_COLOR   = (80, 80, 80)
LANE_COLOR   = (200, 200, 200)
CAR_MOVING   = (56, 142, 60)
CAR_STOP     = (249, 168, 37)
CAR_BORDER   = (10, 10, 10)
RED_LIGHT    = (211, 47, 47)
YELLOW_LIGHT = (249, 168, 37)
GREEN_LIGHT  = (56, 142, 60)
AR_LIGHT     = (20, 20, 20)
TEXT_COLOR   = (230, 220, 80)

# ── RUTAS POR ENFOQUE ─────────────────────────────────────────────────────────
ROUTE_GROUPS = {
    'Norte': {
        'routes': ['O680', 'O279', 'O263', 'O1064'],
        'probs':  [0.50,   0.15,   0.15,   0.20],
    },
    'Sur': {
        'routes': ['Y468', 'Y263', 'Y1064', 'Y680', 'P279'],
        'probs':  [0.20,   0.25,   0.10,    0.25,   0.20],
    },
    'Este': {
        'routes': ['B468', 'B263', 'B1064', 'B680'],
        'probs':  [0.50,   0.15,   0.15,   0.20],
    },
    'Oeste': {
        'routes': ['G263', 'G279', 'G468', 'G680'],
        'probs':  [0.50,   0.15,   0.15,   0.20],
    },
}
APPROACHES = list(ROUTE_GROUPS.keys())

# ── PARÁMETROS POR DEFECTO ────────────────────────────────────────────────────
DEFAULT_PARAMS = {
    'steps':         150,
    'green_ns':      10,
    'green_ew':      10,
    'yellow':        5,
    'all_red':       6,
    'lambda_Norte':  0.4,
    'lambda_Sur':    0.4,
    'lambda_Este':   0.4,
    'lambda_Oeste':  0.4,
    'v_free':        7.0,
    'headway':       8.0,
    'L':             80.0,
    'w':             3.5,
    'mode': 1,   # 0 = sin heurística | 1 = heurística básica | 2 = heurística avanzada
}

# ── PARÁMETROS AJUSTABLES (UI) ────────────────────────────────────────────────
# (key, label, min, max, step)
TUNABLE_PARAMS = [
    ('lambda_Norte', 'Llegada Norte (λ)',  0.0, 2.0, 0.1),
    ('lambda_Sur',   'Llegada Sur (λ)',    0.0, 2.0, 0.1),
    ('lambda_Este',  'Llegada Este (λ)',   0.0, 2.0, 0.1),
    ('lambda_Oeste', 'Llegada Oeste (λ)',  0.0, 2.0, 0.1),
    ('green_ns',     'Verde N-S (pasos)',  1,   30,  1  ),
    ('green_ew',     'Verde E-O (pasos)',  1,   30,  1  ),
    ('yellow',       'Amarillo (pasos)',   1,   10,  1  ),
    ('all_red',      'All-Red (pasos)',    1,   10,  1  ),
    ('v_free',       'Vel. libre',         1.0, 20.0, 0.5),
    ('headway',      'Headway (m)',        2.0, 20.0, 0.5),
]
PARAM_SECTIONS = {0: 'TASAS DE LLEGADA', 4: 'SEMÁFORO', 8: 'VEHÍCULOS'}
