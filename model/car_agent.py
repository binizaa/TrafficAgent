import numpy as np
from config import DISTANCIA_MINIMA


class CarAgent:
    def __init__(self, path, color, speed):
        self.path = path
        self.color = color
        self.base_speed = speed
        self.current_speed = speed
        self.current_step = 0.0
        self.active = True if path else False
        self.pos = np.array(path[0], dtype=float) if path else np.array([0.0, 0.0])

    def update(self, other_agents):
        if not self.active:
            return

        target_speed = self.base_speed

        mi_idx = int(self.current_step)
        self.pos = np.array(self.path[min(mi_idx, len(self.path) - 1)], dtype=float)

        for other in other_agents:
            if other is self:
                continue

            distancia = np.linalg.norm(other.pos - self.pos)

            if distancia < DISTANCIA_MINIMA * 2:
                if other.current_step > self.current_step:
                    if distancia < DISTANCIA_MINIMA:
                        target_speed = 0
                    else:
                        ratio = (distancia - DISTANCIA_MINIMA) / DISTANCIA_MINIMA
                        target_speed = min(self.base_speed, other.current_speed * ratio)
                    break

        self.current_speed = target_speed
        self.current_step += self.current_speed

        if int(self.current_step) >= len(self.path):
            self.active = False
