"""
Modelo de intersección en cruz.
"""

import mesa
from mesa import DataCollector
from mesa.space import MultiGrid

from model.agents import Car, TrafficLight, RIGHT, LEFT, UP, DOWN


class IntersectionModel(mesa.Model):
    """
    Intersección en cruz con carriles separados por dirección:
      RIGHT → fila cy-1    LEFT  → fila cy+1
      UP    → col  cx-1    DOWN  → col  cx+1
    """

    def __init__(self, size=17, green_ticks=6, num_cars=8, spawn_rate=0.3, seed=None):
        super().__init__(seed=seed)
        self.size       = size
        self.spawn_rate = spawn_rate
        self.cars_passed = 0

        cx, cy   = size // 2, size // 2
        self.cx, self.cy = cx, cy

        self.intersection_xs = range(cx - 1, cx + 2)
        self.intersection_ys = range(cy - 1, cy + 2)

        self.lane = {
            RIGHT: cy - 1,
            LEFT:  cy + 1,
            UP:    cx - 1,
            DOWN:  cx + 1,
        }

        self.grid = MultiGrid(size, size, torus=False)

        self.traffic_light = TrafficLight(self, green_ticks=green_ticks)
        self.grid.place_agent(self.traffic_light, (cx, cy))

        self.datacollector = DataCollector(
            model_reporters={
                "Esperando":  lambda m: sum(1 for a in m.agents
                                            if isinstance(a, Car) and a.waiting),
                "Circulando": lambda m: sum(1 for a in m.agents
                                            if isinstance(a, Car) and not a.waiting),
                "Cruzaron":   lambda m: m.cars_passed,
            }
        )
        self.datacollector.collect(self)

        # Coches iniciales distribuidos en los 4 carriles
        directions = [RIGHT, LEFT, UP, DOWN]
        for i in range(num_cars):
            self._place_car_in_lane(directions[i % 4])

    # ── Helpers ───────────────────────────────────────────────────────────────

    def in_intersection(self, x, y):
        return x in self.intersection_xs and y in self.intersection_ys

    def _place_car_in_lane(self, direction):
        """Coloca un coche en la celda libre más cercana a la entrada."""
        s = self.size
        cx, cy = self.cx, self.cy

        if direction == RIGHT:
            cells = [(x, self.lane[RIGHT]) for x in range(0, cx - 1)]
        elif direction == LEFT:
            cells = [(x, self.lane[LEFT])  for x in range(s - 1, cx + 1, -1)]
        elif direction == UP:
            cells = [(self.lane[UP],   y)  for y in range(0, cy - 1)]
        else:
            cells = [(self.lane[DOWN], y)  for y in range(s - 1, cy + 1, -1)]

        for pos in cells:
            if not any(isinstance(a, Car)
                       for a in self.grid.get_cell_list_contents([pos])):
                car = Car(self, direction)
                self.grid.place_agent(car, pos)
                return

    def _spawn_cars(self):
        s = self.size
        spawn_points = [
            ((0,   self.lane[RIGHT]), RIGHT),
            ((s-1, self.lane[LEFT]),  LEFT),
            ((self.lane[UP],   0),    UP),
            ((self.lane[DOWN], s-1),  DOWN),
        ]
        for pos, direction in spawn_points:
            if self.random.random() < self.spawn_rate:
                if not any(isinstance(a, Car)
                           for a in self.grid.get_cell_list_contents([pos])):
                    car = Car(self, direction)
                    self.grid.place_agent(car, pos)

    # ── Paso ──────────────────────────────────────────────────────────────────

    def step(self):
        self._spawn_cars()
        self.traffic_light.step()

        cx, cy = self.cx, self.cy
        cars = [a for a in list(self.agents) if isinstance(a, Car)]

        def dist(car):
            x, y = car.pos
            return abs(x - cx) + abs(y - cy)

        for car in sorted(cars, key=dist, reverse=True):
            if car in self.agents:
                car.step()

        self.datacollector.collect(self)
