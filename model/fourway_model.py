# -*- coding: utf-8 -*-
"""
Modelo de intersección compleja de 4 vías (agentpy).
"""

import agentpy as ap
import numpy as np

ORIGINS = [
    'G263', 'G279', 'G468', 'G680',
    'Y468', 'Y263', 'Y1064', 'Y680', 'P279',
    'B468', 'B263', 'B1064', 'B680',
    'O680', 'O279', 'O263', 'O1064',
]

DEFAULT_PARAMS = {
    'steps':          500,
    'green_ns':        10,
    'green_ew':        10,
    'yellow':           5,
    'all_red':          6,
    'interval_G263':    5,  'interval_P279':    5,
    'interval_G279':    5,  'interval_G468':    5,
    'interval_G680':    0,  'interval_Y468':    5,
    'interval_Y263':    5,  'interval_Y1064':   5,
    'interval_Y680':    5,  'interval_B468':    5,
    'interval_B263':    5,  'interval_B1064':   5,
    'interval_B680':    5,  'interval_O680':    5,
    'interval_O279':    5,  'interval_O263':    5,
    'interval_O1064':   5,
    'v_free':          7.0,
    'headway':         8.0,
    'L':              80.0,
    'w':               3.5,
}


# ── SEMÁFORO ──────────────────────────────────────────────────────────────────
class FourWaySignals(ap.Agent):
    def setup(self, green_ns, green_ew, yellow, all_red):
        self.g      = int(green_ns)
        self.y      = int(yellow)
        self.ar     = int(all_red)
        self.phase  = 0
        self.sub    = 'G'
        self.t_in   = 0

    def lights(self):
        L = {d: 'R' for d in ORIGINS}
        if self.phase == 0:
            for d in ['O680', 'O279', 'O263', 'O1064']: L[d] = self.sub
        elif self.phase == 1:
            for d in ['G263', 'G279', 'G468', 'G680']:  L[d] = self.sub
        elif self.phase == 2:
            for d in ['Y468', 'Y263', 'Y1064', 'Y680', 'P279']: L[d] = self.sub
        elif self.phase == 3:
            for d in ['B468', 'B263', 'B1064', 'B680']: L[d] = self.sub
        return L

    def step(self):
        if   self.sub == 'G'  and self.t_in >= self.g:
            self.sub, self.t_in = 'Y', 0
        elif self.sub == 'Y'  and self.t_in >= self.y:
            self.sub, self.t_in = 'AR', 0
        elif self.sub == 'AR' and self.t_in >= self.ar:
            self.phase = (self.phase + 1) % 4
            self.sub, self.t_in = 'G', 0
        else:
            self.t_in += 1


# ── COCHE ─────────────────────────────────────────────────────────────────────
class Car(ap.Agent):
    def setup(self, origin):
        self.origin = origin
        self.state  = 'moving'
        self.v      = self.model.p.v_free
        L, w = self.model.p.L, self.model.p.w
        off  = w / 2

        self.turn  = None; self.turn2 = None; self.turn3 = None
        self.has_turned = False; self.has_turned2 = False

        if origin == 'G263':
            self.pos=np.array([-L,-off-w*4]); self.dir=np.array([+1,0])
            self.stopline=np.array([-L+w*6,-off-w*4]); self.goal=np.array([-L+w*12,-L])
            self.turn=np.array([-L+w*12,-off-w*4])
        elif origin == 'G279':
            self.pos=np.array([-L,-off-w*2]); self.dir=np.array([+1,0])
            self.stopline=np.array([-L+w*6,-off-w*2]); self.goal=np.array([-L,-off])
            self.turn=np.array([0,0])
        elif origin == 'G468':
            self.pos=np.array([-L,-off-w*4]); self.dir=np.array([+1,0])
            self.stopline=np.array([-L+w*6,-off-w*4]); self.goal=np.array([-L+w*8,-L])
            self.turn=np.array([-L+w*8,-off-w*4])
        elif origin == 'G680':
            self.pos=np.array([-L,-off-w*2]); self.dir=np.array([+1,0])
            self.stopline=np.array([-L+w*6,-off-w*2]); self.goal=np.array([L-41,+L])
            self.turn=np.array([L-41,-off-w*2])
        elif origin == 'Y468':
            self.pos=np.array([+off+w*10,-L]); self.dir=np.array([0,+1])
            self.stopline=np.array([+off+w*10,-L+w*8]); self.goal=np.array([+off-w*10,-L])
            self.turn=np.array([+off+w*10,-L+w*10]); self.turn2=np.array([+off-w*10,-L+w*10])
        elif origin == 'Y263':
            self.pos=np.array([+off+w*10,-L]); self.dir=np.array([0,+1])
            self.stopline=np.array([+off+w*10,-L+w*8]); self.goal=np.array([-L+w*12,-L])
            self.turn=np.array([+off+w*10,-off-w*4]); self.turn2=np.array([+off-w*16,-off-w*4])
        elif origin == 'Y1064':
            self.pos=np.array([+off+w*12,-L]); self.dir=np.array([0,+1])
            self.stopline=np.array([+off+w*12,-L+w*8]); self.goal=np.array([-L,-off+w*4])
            self.turn=np.array([+off+w*12,-off+w*4])
        elif origin == 'Y680':
            self.pos=np.array([+off+w*12,-L]); self.dir=np.array([0,+1])
            self.stopline=np.array([+off+w*12,-L+w*8]); self.goal=np.array([+off+w*12,L])
            self.turn=np.array([0,0])
        elif origin == 'P279':
            self.pos=np.array([+off+w*16,-L]); self.dir=np.array([0,+1])
            self.stopline=np.array([+off+w*16,-L+w*8]); self.goal=np.array([-L,-off])
            self.turn=np.array([+off+w*16,-off-w*4])
        elif origin == 'B468':
            self.pos=np.array([+L,+off+w*3]); self.dir=np.array([-1,0])
            self.stopline=np.array([+off+w*16,+off+w*3]); self.goal=np.array([+L,+off])
            self.turn=np.array([+off-w*10,+off+w*3])
        elif origin == 'B263':
            self.pos=np.array([+L,+off+w*3]); self.dir=np.array([-1,0])
            self.stopline=np.array([+off+w*16,+off+w*3]); self.goal=np.array([-L+w*12,-L])
            self.turn=np.array([+off-w*10,+off+w*3]); self.turn2=np.array([+off-w*10,-off-w*4])
            self.turn3=np.array([+off-w*16,-off-w*4])
        elif origin == 'B1064':
            self.pos=np.array([+L,+off+w*5]); self.dir=np.array([-1,0])
            self.stopline=np.array([+off+w*16,+off+w*5]); self.goal=np.array([-L,+off+w*5])
            self.turn=np.array([0,0])
        elif origin == 'B680':
            self.pos=np.array([+L,+off+w*5]); self.dir=np.array([-1,0])
            self.stopline=np.array([+off+w*16,+off+w*5]); self.goal=np.array([+off+w*12,L])
            self.turn=np.array([+off+w*12,+off+w*5])
        elif origin == 'O680':
            self.pos=np.array([-off-w*8,L]); self.dir=np.array([0,-1])
            self.stopline=np.array([-off-w*8,L-w*6]); self.goal=np.array([+off+w*11,L])
            self.turn=np.array([-off-w*8,L-w*8]); self.turn2=np.array([+off+w*11,L-w*8])
        elif origin == 'O279':
            self.pos=np.array([-off-w*8,L]); self.dir=np.array([0,-1])
            self.stopline=np.array([-off-w*8,L-w*6]); self.goal=np.array([-L,-off-w])
            self.turn=np.array([-off-w*8,-off-w])
        elif origin == 'O263':
            self.pos=np.array([-off-w*10,L]); self.dir=np.array([0,-1])
            self.stopline=np.array([-off-w*10,L-w*6]); self.goal=np.array([-L+w*12,-L])
            self.turn=np.array([-off-w*10,-off-w*4]); self.turn2=np.array([-off-w*14,-off-w*4])
        elif origin == 'O1064':
            self.pos=np.array([-off-w*10,L]); self.dir=np.array([0,-1])
            self.stopline=np.array([-off-w*10,L-w*6]); self.goal=np.array([-L,-off+w*7])
            self.turn=np.array([-off-w*10,-off+w*7])

    def dist_to(self, p):
        return np.linalg.norm(self.pos - p)

    def step(self):
        if self.state == 'done': return
        if self.dist_to(self.goal) < 3.0:
            self.state = 'done'; return

        vmax   = self.v
        lights = self.model.ctrl.lights()

        if not np.allclose(self.stopline, [0, 0]) and \
           np.allclose(self.pos, self.stopline, atol=3.0) and \
           lights[self.origin] != 'G':
            return

        # Giros
        if self.origin == 'B263':
            if not self.has_turned and self.turn is not None and np.allclose(self.pos, self.turn, atol=3.0):
                self.dir = np.array([0, -1]); self.has_turned = True
            elif self.has_turned and self.turn2 is not None and np.allclose(self.pos, self.turn2, atol=3.0):
                self.dir = np.array([-1, 0]); self.has_turned2 = True
            elif self.has_turned2 and self.turn3 is not None and np.allclose(self.pos, self.turn3, atol=3.0):
                self.dir = np.array([0, -1])
        elif self.origin in ['Y468', 'Y263', 'O680', 'O263']:
            if self.origin == 'O680':
                if not self.has_turned and self.turn is not None and np.allclose(self.pos, self.turn, atol=3.0):
                    self.dir = np.array([1, 0]); self.has_turned = True
                elif self.has_turned and self.turn2 is not None and np.allclose(self.pos, self.turn2, atol=3.0):
                    self.dir = np.array([0, 1])
            elif self.origin == 'O263':
                if not self.has_turned and self.turn is not None and np.allclose(self.pos, self.turn, atol=3.0):
                    self.dir = np.array([-1, 0]); self.has_turned = True
                elif self.has_turned and self.turn2 is not None and np.allclose(self.pos, self.turn2, atol=3.0):
                    self.dir = np.array([0, -1])
            elif not self.has_turned and self.turn is not None and np.allclose(self.pos, self.turn, atol=3.0):
                self.dir = np.array([-1, 0]); self.has_turned = True
            elif self.has_turned and self.turn2 is not None and np.allclose(self.pos, self.turn2, atol=3.0):
                self.dir = np.array([0, -1])
        else:
            if self.turn is not None and np.allclose(self.pos, self.turn, atol=3.0):
                if self.origin in ['G263', 'G468', 'B468']:    self.dir = np.array([0, -1])
                elif self.origin in ['G680', 'B680']:           self.dir = np.array([0, +1])
                elif self.origin in ['Y1064', 'O1064']:         self.dir = np.array([-1, 0])
                elif self.origin in ['P279', 'O279']:           self.dir = np.array([+1, 0])

        head = self.model.headway_ahead(self)
        if head is not None:
            if np.linalg.norm(head.pos - self.pos) < self.model.p.headway:
                vmax = 0.0

        if vmax > 0.0:
            self.pos = self.pos + self.dir * vmax

        if abs(self.pos[0]) > self.model.p.L or abs(self.pos[1]) > self.model.p.L:
            self.state = 'done'


# ── MODELO ────────────────────────────────────────────────────────────────────
class FourWayModel(ap.Model):

    def setup(self):
        p = self.p
        self.ctrl = FourWaySignals(self, p.green_ns, p.green_ew, p.yellow, p.all_red)
        self.cars = ap.AgentList(self, 0, Car)
        self.throughput   = 0
        self.spawn_counts = {d: 0 for d in ORIGINS}

    def headway_ahead(self, me):
        if np.allclose(me.dir, [1, 0]) or np.allclose(me.dir, [-1, 0]):
            same_lane = [c for c in self.cars if c is not me
                         and np.allclose(c.dir, me.dir)
                         and abs(c.pos[1] - me.pos[1]) < 0.1]
        elif np.allclose(me.dir, [0, 1]) or np.allclose(me.dir, [0, -1]):
            same_lane = [c for c in self.cars if c is not me
                         and np.allclose(c.dir, me.dir)
                         and abs(c.pos[0] - me.pos[0]) < 0.1]
        else:
            same_lane = []
        if not same_lane: return None
        ahead = [(np.dot(c.pos - me.pos, me.dir), c)
                 for c in same_lane if np.dot(c.pos - me.pos, me.dir) > 0]
        return min(ahead, key=lambda x: x[0])[1] if ahead else None

    def spawn_deterministic(self, origin, interval):
        if interval <= 0: return
        if self.t % interval == 0:
            self.cars.append(Car(self, origin=origin))
            self.spawn_counts[origin] += 1

    def step(self):
        p = self.p
        for origin in ORIGINS:
            interval = getattr(p, f'interval_{origin}', 0)
            self.spawn_deterministic(origin, interval)

        self.ctrl.step()
        self.cars.step()
        self.throughput += len([c for c in self.cars if c.state == 'done'])
        self.cars = ap.AgentList(self, [c for c in self.cars if c.state != 'done'], Car)
