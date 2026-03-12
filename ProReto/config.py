CSV_FILE = 'rutas_cache.csv'
FONDO_PATH = 'images/fondo.png'
ANCHO_MAXIMO_VENTANA = 1000
FPS = 60
RADIO_COCHE = 8
DISTANCIA_MINIMA = 24

# --- SEMÁFOROS ---
# Posiciones en coordenadas ORIGINALES del mapa (antes de escalar).
# grupo 0 = Norte/Sur  |  grupo 1 = Este/Oeste
# Cuando grupo 0 está en verde, grupo 1 está en rojo, y viceversa.
SEMAFOROS = [
    # Norte: ruta 1 cruza ruta 5 en ~(2113, 942) — para antes
    {"pos": (2180, 960), "direccion": "N", "grupo": 0},
    # Sur: rutas 4 y 5 se cruzan en ~(1091, 587)
    {"pos": (1091, 587), "direccion": "S", "grupo": 0},
    # Este: ruta 2 cruza ruta 4 en ~(1078, 887) — para un poco antes
    {"pos": (950, 800),  "direccion": "E", "grupo": 1},
    # Oeste: ruta 3 pasa por el fondo del mapa (1467,1484 → 1031,1526)
    {"pos": (1250, 1430), "direccion": "O", "grupo": 1},
]

SEMAFORO_VERDE_MS    = 5000   # ms en verde
SEMAFORO_AMARILLO_MS = 1500   # ms en amarillo
SEMAFORO_STOP_RADIO  = 80     # radio de la zona común (coords escaladas)
SEMAFORO_BUFFER      = 50     # píxeles extra ANTES de la zona donde el carro se detiene
