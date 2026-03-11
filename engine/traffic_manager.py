from model.traffic_light import TrafficLight
from config import SEMAFORO_VERDE_MS, SEMAFORO_AMARILLO_MS

# Fases del ciclo:
#  0 -> grupo 0 (N/S) VERDE,    grupo 1 (E/O) ROJO
#  1 -> grupo 0 (N/S) AMARILLO, grupo 1 (E/O) ROJO
#  2 -> grupo 0 (N/S) ROJO,     grupo 1 (E/O) VERDE
#  3 -> grupo 0 (N/S) ROJO,     grupo 1 (E/O) AMARILLO

_FASE_DURACION = [
    SEMAFORO_VERDE_MS,
    SEMAFORO_AMARILLO_MS,
    SEMAFORO_VERDE_MS,
    SEMAFORO_AMARILLO_MS,
]

_FASE_ESTADOS = [
    # (estado_grupo0, estado_grupo1)
    (TrafficLight.VERDE,    TrafficLight.ROJO),
    (TrafficLight.AMARILLO, TrafficLight.ROJO),
    (TrafficLight.ROJO,     TrafficLight.VERDE),
    (TrafficLight.ROJO,     TrafficLight.AMARILLO),
]


class TrafficManager:
    def __init__(self, lights):
        self.lights = lights
        self.fase   = 0
        self.timer  = 0
        self._apply()

    def update(self, dt_ms):
        self.timer += dt_ms
        if self.timer >= _FASE_DURACION[self.fase]:
            self.timer = 0
            self.fase  = (self.fase + 1) % 4
            self._apply()

    def _apply(self):
        s0, s1 = _FASE_ESTADOS[self.fase]
        for light in self.lights:
            light.state = s0 if light.grupo == 0 else s1
