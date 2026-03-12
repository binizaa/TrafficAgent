import numpy as np
from config import DISTANCIA_MINIMA, SEMAFORO_STOP_RADIO, SEMAFORO_BUFFER
from model.traffic_light import TrafficLight

_LOOKAHEAD        = 80     # pasos hacia adelante para detectar semáforo/agente
_STUCK_UMBRAL_MS  = 3000  # ms quieto antes de pedir paso de emergencia
_PASO_FRAMES      = 90    # frames que dura el paso de emergencia (~1.5s a 60fps)


class CarAgent:
    def __init__(self, path, color, speed):
        self.path = path
        self.color = color
        self.base_speed = speed
        self.current_speed = speed
        self.current_step = 0.0
        self.active = True if path else False
        self.pos = np.array(path[0], dtype=float) if path else np.array([0.0, 0.0])
        # IDs de semáforos cuya zona el carro entró mientras estaban en VERDE
        self._committed = set()
        # Anti-estancamiento
        self._stuck_ms    = 0    # tiempo acumulado sin moverse
        self._paso_frames = 0    # frames restantes de paso de emergencia

    def _blocked_by_light(self, traffic_lights):
        """
        Devuelve True si el carro debe detenerse por un semáforo.
        Un carro solo puede cruzar la zona de un semáforo si entró mientras
        estaba en VERDE (committed). Si no se comprometió antes de que cambiara
        a rojo, no puede entrar aunque ya esté cerca.
        """
        idx = int(self.current_step)
        car_pos = self.pos

        for light in traffic_lights:
            lid = id(light)
            lx, ly = light.pos
            stop_r = SEMAFORO_STOP_RADIO
            in_zone = ((car_pos[0] - lx) ** 2 + (car_pos[1] - ly) ** 2) < stop_r ** 2

            if light.state == TrafficLight.VERDE:
                # Si estamos en la zona con verde → comprometido con este cruce
                if in_zone:
                    self._committed.add(lid)
                else:
                    self._committed.discard(lid)
                continue

            # Semáforo en ROJO o AMARILLO
            if lid in self._committed:
                # Entramos con verde: terminamos de cruzar
                if not in_zone:
                    self._committed.discard(lid)  # ya salimos de la zona
                continue  # seguimos hasta salir

            # No estamos comprometidos: bloqueamos si el path entra al buffer previo
            # El carro se detiene ANTES de la zona, a SEMAFORO_BUFFER píxeles del borde
            outer_r = stop_r + SEMAFORO_BUFFER
            for i in range(idx, min(idx + _LOOKAHEAD, len(self.path))):
                px, py = self.path[i]
                if (px - lx) ** 2 + (py - ly) ** 2 < outer_r ** 2:
                    return True

        return False

    def _nearest_agent_on_path(self, other_agents):
        """
        Busca el carro más cercano que esté físicamente sobre los próximos
        _LOOKAHEAD pasos de NUESTRA ruta, sin importar de qué ruta sea.
        Devuelve la distancia mínima encontrada (inf si nadie bloquea).
        """
        idx = int(self.current_step)
        min_dist = float('inf')

        for other in other_agents:
            if other is self or not other.active:
                continue

            ox, oy = other.pos

            for i in range(idx + 2, min(idx + _LOOKAHEAD, len(self.path))):
                px, py = self.path[i]
                d = ((px - ox) ** 2 + (py - oy) ** 2) ** 0.5
                if d < DISTANCIA_MINIMA * 1.5:
                    if d < min_dist:
                        min_dist = d
                    break   # solo el punto más cercano por agente

        return min_dist

    def update(self, other_agents, traffic_lights=(), dt_ms=16):
        if not self.active:
            return

        mi_idx = int(self.current_step)
        self.pos = np.array(self.path[min(mi_idx, len(self.path) - 1)], dtype=float)

        # Semáforo tiene prioridad absoluta (el paso de emergencia no lo omite)
        if self._blocked_by_light(traffic_lights):
            target_speed = 0
            self._stuck_ms    = 0
            self._paso_frames = 0
        elif self._paso_frames > 0:
            # Paso de emergencia activo: ignora bloqueo de otros agentes
            target_speed       = self.base_speed
            self._paso_frames -= 1
            self._stuck_ms     = 0
        else:
            dist = self._nearest_agent_on_path(other_agents)
            if dist < DISTANCIA_MINIMA:
                target_speed    = 0
                self._stuck_ms += dt_ms
                # Si lleva demasiado tiempo parado, activar paso de emergencia
                if self._stuck_ms >= _STUCK_UMBRAL_MS:
                    self._paso_frames = _PASO_FRAMES
                    self._stuck_ms    = 0
            elif dist < DISTANCIA_MINIMA * 1.5:
                ratio        = (dist - DISTANCIA_MINIMA) / DISTANCIA_MINIMA
                target_speed = self.base_speed * max(0.0, ratio)
                self._stuck_ms = 0
            else:
                target_speed   = self.base_speed
                self._stuck_ms = 0

        self.current_speed = target_speed
        self.current_step += self.current_speed

        if int(self.current_step) >= len(self.path):
            self.active = False
