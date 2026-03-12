import agentpy as ap
import numpy as np


# ── HEADWAY ───────────────────────────────────────────────────────────────────
def headway_ahead(me, cars):
    if np.allclose(me.dir, [1, 0]) or np.allclose(me.dir, [-1, 0]):
        same_lane = [c for c in cars if c is not me
                     and np.allclose(c.dir, me.dir)
                     and abs(c.pos[1] - me.pos[1]) < 0.1]
    elif np.allclose(me.dir, [0, 1]) or np.allclose(me.dir, [0, -1]):
        same_lane = [c for c in cars if c is not me
                     and np.allclose(c.dir, me.dir)
                     and abs(c.pos[0] - me.pos[0]) < 0.1]
    else:
        same_lane = []
    if not same_lane:
        return None
    ahead = [(np.dot(c.pos - me.pos, me.dir), c)
             for c in same_lane if np.dot(c.pos - me.pos, me.dir) > 0]
    return min(ahead, key=lambda x: x[0])[1] if ahead else None


# ── AGENTE AUTO ───────────────────────────────────────────────────────────────
class Car(ap.Agent):
    def setup(self, origin, params):
        self.origin    = origin
        self.state     = 'moving'
        self.is_moving = True
        self.v         = params['v_free']
        self.p         = params
        L, w           = params['L'], params['w']
        off            = w / 2

        self.turn  = None; self.turn2 = None; self.turn3 = None
        self.has_turned = False; self.has_turned2 = False

        if origin == 'G263':
            self.pos=np.array([-L,-off-w*4],dtype=float); self.dir=np.array([+1,0],dtype=float)
            self.stopline=np.array([-L+w*6,-off-w*4]); self.goal=np.array([-L+w*12,-L])
            self.turn=np.array([-L+w*12,-off-w*4])
        elif origin == 'G279':
            self.pos=np.array([-L,-off-w*2],dtype=float); self.dir=np.array([+1,0],dtype=float)
            self.stopline=np.array([-L+w*6,-off-w*2]); self.goal=np.array([-L,-off])
            self.turn=np.array([0,0])
        elif origin == 'G468':
            self.pos=np.array([-L,-off-w*4],dtype=float); self.dir=np.array([+1,0],dtype=float)
            self.stopline=np.array([-L+w*6,-off-w*4]); self.goal=np.array([-L+w*8,-L])
            self.turn=np.array([-L+w*8,-off-w*4])
        elif origin == 'G680':
            self.pos=np.array([-L,-off-w*2],dtype=float); self.dir=np.array([+1,0],dtype=float)
            self.stopline=np.array([-L+w*6,-off-w*2]); self.goal=np.array([L-41,+L])
            self.turn=np.array([L-41,-off-w*2])
        elif origin == 'Y468':
            self.pos=np.array([+off+w*10,-L],dtype=float); self.dir=np.array([0,+1],dtype=float)
            self.stopline=np.array([+off+w*10,-L+w*8]); self.goal=np.array([+off-w*10,-L])
            self.turn=np.array([+off+w*10,-L+w*10]); self.turn2=np.array([+off-w*10,-L+w*10])
        elif origin == 'Y263':
            self.pos=np.array([+off+w*10,-L],dtype=float); self.dir=np.array([0,+1],dtype=float)
            self.stopline=np.array([+off+w*10,-L+w*8]); self.goal=np.array([-L+w*12,-L])
            self.turn=np.array([+off+w*10,-off-w*4]); self.turn2=np.array([+off-w*16,-off-w*4])
        elif origin == 'Y1064':
            self.pos=np.array([+off+w*12,-L],dtype=float); self.dir=np.array([0,+1],dtype=float)
            self.stopline=np.array([+off+w*12,-L+w*8]); self.goal=np.array([-L,-off+w*4])
            self.turn=np.array([+off+w*12,-off+w*4])
        elif origin == 'Y680':
            self.pos=np.array([+off+w*12,-L],dtype=float); self.dir=np.array([0,+1],dtype=float)
            self.stopline=np.array([+off+w*12,-L+w*8]); self.goal=np.array([+off+w*12,L])
            self.turn=np.array([0,0])
        elif origin == 'P279':
            self.pos=np.array([+off+w*16,-L],dtype=float); self.dir=np.array([0,+1],dtype=float)
            self.stopline=np.array([+off+w*16,-L+w*8]); self.goal=np.array([-L,-off])
            self.turn=np.array([+off+w*16,-off-w*4])
        elif origin == 'B468':
            self.pos=np.array([+L,+off+w*3],dtype=float); self.dir=np.array([-1,0],dtype=float)
            self.stopline=np.array([+off+w*16,+off+w*3]); self.goal=np.array([+L,+off])
            self.turn=np.array([+off-w*10,+off+w*3])
        elif origin == 'B263':
            self.pos=np.array([+L,+off+w*3],dtype=float); self.dir=np.array([-1,0],dtype=float)
            self.stopline=np.array([+off+w*16,+off+w*3]); self.goal=np.array([-L+w*12,-L])
            self.turn=np.array([+off-w*10,+off+w*3]); self.turn2=np.array([+off-w*10,-off-w*4])
            self.turn3=np.array([+off-w*16,-off-w*4])
        elif origin == 'B1064':
            self.pos=np.array([+L,+off+w*5],dtype=float); self.dir=np.array([-1,0],dtype=float)
            self.stopline=np.array([+off+w*16,+off+w*5]); self.goal=np.array([-L,+off+w*5])
            self.turn=np.array([0,0])
        elif origin == 'B680':
            self.pos=np.array([+L,+off+w*5],dtype=float); self.dir=np.array([-1,0],dtype=float)
            self.stopline=np.array([+off+w*16,+off+w*5]); self.goal=np.array([+off+w*12,L])
            self.turn=np.array([+off+w*12,+off+w*5])
        elif origin == 'O680':
            self.pos=np.array([-off-w*8,L],dtype=float); self.dir=np.array([0,-1],dtype=float)
            self.stopline=np.array([-off-w*8,L-w*6]); self.goal=np.array([+off+w*11,L])
            self.turn=np.array([-off-w*8,L-w*8]); self.turn2=np.array([+off+w*11,L-w*8])
        elif origin == 'O279':
            self.pos=np.array([-off-w*8,L],dtype=float); self.dir=np.array([0,-1],dtype=float)
            self.stopline=np.array([-off-w*8,L-w*6]); self.goal=np.array([-L,-off-w])
            self.turn=np.array([-off-w*8,-off-w])
        elif origin == 'O263':
            self.pos=np.array([-off-w*10,L],dtype=float); self.dir=np.array([0,-1],dtype=float)
            self.stopline=np.array([-off-w*10,L-w*6]); self.goal=np.array([-L+w*12,-L])
            self.turn=np.array([-off-w*10,-off-w*4]); self.turn2=np.array([-off-w*14,-off-w*4])
        elif origin == 'O1064':
            self.pos=np.array([-off-w*10,L],dtype=float); self.dir=np.array([0,-1],dtype=float)
            self.stopline=np.array([-off-w*10,L-w*6]); self.goal=np.array([-L,-off+w*7])
            self.turn=np.array([-off-w*10,-off+w*7])

    def dist_to(self, p):
        return np.linalg.norm(self.pos - np.array(p))

    def step(self):
        lights = self.model.ctrl.lights()
        cars   = list(self.model.cars)

        self.is_moving = False
        if self.state == 'done':
            return
        if self.dist_to(self.goal) < 3.0:
            self.state = 'done'; return

        vmax = self.v

        if (self.stopline is not None
                and np.allclose(self.pos, self.stopline, atol=3.0)
                and lights[self.origin] != 'G'):
            return

        # ── Giros ──
        if self.origin == 'B263':
            if not self.has_turned and self.turn is not None and np.allclose(self.pos, self.turn, atol=3.0):
                self.dir = np.array([0, -1], dtype=float); self.has_turned = True
            elif self.has_turned and self.turn2 is not None and np.allclose(self.pos, self.turn2, atol=3.0):
                self.dir = np.array([-1, 0], dtype=float); self.has_turned2 = True
            elif self.has_turned2 and self.turn3 is not None and np.allclose(self.pos, self.turn3, atol=3.0):
                self.dir = np.array([0, -1], dtype=float)
        elif self.origin in ['Y468', 'Y263', 'O680', 'O263']:
            if self.origin == 'O680':
                if not self.has_turned and self.turn is not None and np.allclose(self.pos, self.turn, atol=3.0):
                    self.dir = np.array([1, 0], dtype=float); self.has_turned = True
                elif self.has_turned and self.turn2 is not None and np.allclose(self.pos, self.turn2, atol=3.0):
                    self.dir = np.array([0, 1], dtype=float)
            elif self.origin == 'O263':
                if not self.has_turned and self.turn is not None and np.allclose(self.pos, self.turn, atol=3.0):
                    self.dir = np.array([-1, 0], dtype=float); self.has_turned = True
                elif self.has_turned and self.turn2 is not None and np.allclose(self.pos, self.turn2, atol=3.0):
                    self.dir = np.array([0, -1], dtype=float)
            elif not self.has_turned and self.turn is not None and np.allclose(self.pos, self.turn, atol=3.0):
                self.dir = np.array([-1, 0], dtype=float); self.has_turned = True
            elif self.has_turned and self.turn2 is not None and np.allclose(self.pos, self.turn2, atol=3.0):
                self.dir = np.array([0, -1], dtype=float)
        else:
            if self.turn is not None and np.allclose(self.pos, self.turn, atol=3.0):
                if self.origin in ['G263', 'G468', 'B468']:   self.dir = np.array([0, -1], dtype=float)
                elif self.origin in ['G680', 'B680']:          self.dir = np.array([0, +1], dtype=float)
                elif self.origin in ['Y1064', 'O1064']:        self.dir = np.array([-1, 0], dtype=float)
                elif self.origin in ['P279', 'O279']:          self.dir = np.array([+1, 0], dtype=float)

        # ── Headway ──
        head = headway_ahead(self, cars)
        if head is not None and np.linalg.norm(head.pos - self.pos) < self.p['headway']:
            vmax = 0.0

        if vmax > 0.0:
            self.pos = self.pos + self.dir * vmax
            self.is_moving = True

        L = self.p['L']
        if abs(self.pos[0]) > L or abs(self.pos[1]) > L:
            self.state = 'done'
