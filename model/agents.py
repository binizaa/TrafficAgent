"""
Agentes de la simulación de tráfico.
"""

import mesa

# ── Constantes de dirección ───────────────────────────────────────────────────
RIGHT = ( 1,  0)
LEFT  = (-1,  0)
UP    = ( 0,  1)
DOWN  = ( 0, -1)

AXIS_H = "horizontal"
AXIS_V = "vertical"


# ── Semáforo ──────────────────────────────────────────────────────────────────
class TrafficLight(mesa.Agent):
    """Alterna el eje con verde cada `green_ticks` pasos."""

    def __init__(self, model, green_ticks=5):
        super().__init__(model)
        self.green_axis  = AXIS_H
        self.green_ticks = green_ticks
        self._counter    = 0

    @property
    def green_h(self):
        return self.green_axis == AXIS_H

    @property
    def green_v(self):
        return self.green_axis == AXIS_V

    def step(self):
        self._counter += 1
        if self._counter >= self.green_ticks:
            self._counter = 0
            self.green_axis = AXIS_V if self.green_axis == AXIS_H else AXIS_H


# ── Coche ─────────────────────────────────────────────────────────────────────
class Car(mesa.Agent):
    """Coche que sigue su carril y respeta el semáforo."""

    def __init__(self, model, direction):
        super().__init__(model)
        self.direction = direction
        self.axis      = AXIS_H if direction[1] == 0 else AXIS_V
        self.waiting   = False

    def step(self):
        nx, ny = self.pos[0] + self.direction[0], self.pos[1] + self.direction[1]
        w, h   = self.model.grid.width, self.model.grid.height

        # Salió de la grilla → eliminar
        if not (0 <= nx < w and 0 <= ny < h):
            self.model.grid.remove_agent(self)
            self.remove()
            self.model.cars_passed += 1
            return

        # Semáforo
        if self.model.in_intersection(nx, ny):
            light = self.model.traffic_light
            if self.axis == AXIS_H and not light.green_h:
                self.waiting = True
                return
            if self.axis == AXIS_V and not light.green_v:
                self.waiting = True
                return

        self.waiting = False

        # Colisión con otro coche adelante
        if any(isinstance(a, Car)
               for a in self.model.grid.get_cell_list_contents([(nx, ny)])):
            self.waiting = True
            return

        self.model.grid.move_agent(self, (nx, ny))
