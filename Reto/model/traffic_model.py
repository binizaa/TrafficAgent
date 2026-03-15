import agentpy as ap
import numpy as np

from config import ROUTE_GROUPS, APPROACHES
from model.signals import FourWaySignals
from model.car import Car
from model.carWithout import CarWithout


class TrafficModel(ap.Model):
    def setup(self):
        p = self.p
        self.ctrl         = FourWaySignals(p['green_ns'], p['green_ew'], p['yellow'], p['all_red'])
        self._car_cls     = CarWithout if p.get('mode', 1) == 0 else Car
        self.cars         = ap.AgentList(self, 0, self._car_cls)
        self.throughput   = 0
        self.t            = 0
        self.spawn_counts = {a: 0 for a in APPROACHES}

    def spawn_approach(self, approach, lam):
        if lam <= 0:
            return
        k = np.random.poisson(lam)
        if k == 0:
            return
        group = ROUTE_GROUPS[approach]
        for _ in range(k):
            origin  = np.random.choice(group['routes'], p=group['probs'])
            new_car = ap.AgentList(self, 1, self._car_cls, origin=origin, params=dict(self.p))
            self.cars = self.cars + new_car
            self.spawn_counts[approach] += 1

    def step(self):
        p = self.p
        for approach in APPROACHES:
            self.spawn_approach(approach, p[f'lambda_{approach}'])

        self.ctrl.step()
        self.cars.step()

        done_count = sum(1 for c in self.cars if c.state == 'done')
        self.throughput += done_count
        self.cars = self.cars.select([c.state != 'done' for c in self.cars])
        self.t += 1
