"""
Traffic Light Crossing - agentpy + pygame
"""

import agentpy as ap
import pygame
import numpy as np
import sys

# ── ROUTE GROUPS ──────────────────────────────────────────────────────────────
# Each approach lists its possible internal routes and the probability of
# a spawned car choosing each one (must sum to 1.0).
ROUTE_GROUPS = {
    'Norte': {
        'routes': ['O680', 'O279', 'O263', 'O1064'],
        'probs':  [0.25,   0.25,   0.25,   0.25],
    },
    'Sur': {
        'routes': ['Y468', 'Y263', 'Y1064', 'Y680', 'P279'],
        'probs':  [0.20,   0.20,   0.20,    0.20,   0.20],
    },
    'Este': {
        'routes': ['B468', 'B263', 'B1064', 'B680'],
        'probs':  [0.25,   0.25,   0.25,    0.25],
    },
    'Oeste': {
        'routes': ['G263', 'G279', 'G468', 'G680'],
        'probs':  [0.25,   0.25,   0.25,   0.25],
    },
}
APPROACHES = list(ROUTE_GROUPS.keys())

# ── PARAMETERS ────────────────────────────────────────────────────────────────
params = {
    'steps': 150,
    'green_ns': 10,
    'green_ew': 10,
    'yellow': 5,
    'all_red': 6,
    # One arrival rate per approach; route within approach is chosen by ROUTE_GROUPS probs
    'lambda_Norte': 0.4,
    'lambda_Sur':   0.4,
    'lambda_Este':  0.4,
    'lambda_Oeste': 0.4,
    'v_free': 7.0,
    'headway': 8.0,
    'L': 80.0,
    'w': 3.5
}

# ── COLORS ────────────────────────────────────────────────────────────────────
BG_COLOR      = (34, 34, 34)
ROAD_COLOR    = (80, 80, 80)
LANE_COLOR    = (200, 200, 200)
CAR_MOVING    = (56, 142, 60)
CAR_STOP      = (249, 168, 37)
CAR_BORDER    = (10, 10, 10)
RED_LIGHT     = (211, 47, 47)
YELLOW_LIGHT  = (249, 168, 37)
GREEN_LIGHT   = (56, 142, 60)
AR_LIGHT      = (20, 20, 20)
UI_BG         = (255, 255, 255, 200)
TEXT_COLOR    = (30, 30, 30)

# ── WINDOW & SCALE ────────────────────────────────────────────────────────────
WINDOW_SIZE  = 800
PANEL_HEIGHT = 60
MARGIN       = 20

def world_to_screen(pos, L, screen_size):
    """Convert world coords [-L,L] to screen pixels."""
    scale = (screen_size - 2 * MARGIN) / (2 * L)
    sx = int((pos[0] + L) * scale + MARGIN)
    sy = int((L - pos[1]) * scale + MARGIN)
    return sx, sy

def scale_val(val, L, screen_size):
    return val * (screen_size - 2 * MARGIN) / (2 * L)

# ── TRAFFIC LIGHT CONTROLLER ──────────────────────────────────────────────────
class FourWaySignals:
    def __init__(self, green_ns, green_ew, yellow, all_red):
        self.g      = int(green_ns)
        self.y      = int(yellow)
        self.ar     = int(all_red)
        self.phase  = 0
        self.sub    = 'G'
        self.t_in   = 0
        self.t      = 0

    def lights(self):
        L = {d: 'R' for d in [
            'G263','G279','G468','G680',
            'Y468','Y263','Y1064','Y680','P279',
            'B468','B263','B1064','B680',
            'O680','O279','O263','O1064'
        ]}
        if self.phase == 0:
            for d in ['O680','O279','O263','O1064']: L[d] = self.sub
        elif self.phase == 1:
            for d in ['G263','G279','G468','G680']:  L[d] = self.sub
        elif self.phase == 2:
            for d in ['Y468','Y263','Y1064','Y680','P279']: L[d] = self.sub
        elif self.phase == 3:
            for d in ['B468','B263','B1064','B680']: L[d] = self.sub
        return L

    def step(self):
        self.t += 1
        if   self.sub == 'G'  and self.t_in >= self.g:
            self.sub, self.t_in = 'Y', 0
        elif self.sub == 'Y'  and self.t_in >= self.y:
            self.sub, self.t_in = 'AR', 0
        elif self.sub == 'AR' and self.t_in >= self.ar:
            self.phase = (self.phase + 1) % 4
            self.sub, self.t_in = 'G', 0
        else:
            self.t_in += 1

    @property
    def phase_name(self):
        phases = {0: "Norte-Sur", 1: "Este-Oeste", 2: "Diagonal Y", 3: "Diagonal B"}
        return phases.get(self.phase, "?")


# ── HEADWAY ───────────────────────────────────────────────────────────────────
def headway_ahead(me, cars):
    if np.allclose(me.dir,[1,0]) or np.allclose(me.dir,[-1,0]):
        same_lane = [c for c in cars if c is not me
                     and np.allclose(c.dir,me.dir)
                     and abs(c.pos[1]-me.pos[1]) < 0.1]
    elif np.allclose(me.dir,[0,1]) or np.allclose(me.dir,[0,-1]):
        same_lane = [c for c in cars if c is not me
                     and np.allclose(c.dir,me.dir)
                     and abs(c.pos[0]-me.pos[0]) < 0.1]
    else:
        same_lane = []
    if not same_lane: return None
    ahead = [(np.dot(c.pos - me.pos, me.dir), c)
             for c in same_lane if np.dot(c.pos - me.pos, me.dir) > 0]
    return min(ahead, key=lambda x: x[0])[1] if ahead else None


# ── CAR AGENT (agentpy) ───────────────────────────────────────────────────────
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
        self.has_turned  = False; self.has_turned2 = False

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
        """Called by agentpy each simulation tick."""
        lights = self.model.ctrl.lights()
        cars   = list(self.model.cars)

        self.is_moving = False
        if self.state == 'done': return
        if self.dist_to(self.goal) < 3.0:
            self.state = 'done'; return

        vmax = self.v

        if self.stopline is not None and np.allclose(self.pos, self.stopline, atol=3.0) and lights[self.origin] != 'G':
            return

        # ── Turns ──
        if self.origin == 'B263':
            if not self.has_turned and self.turn is not None and np.allclose(self.pos,self.turn,atol=3.0):
                self.dir=np.array([0,-1],dtype=float); self.has_turned=True
            elif self.has_turned and self.turn2 is not None and np.allclose(self.pos,self.turn2,atol=3.0):
                self.dir=np.array([-1,0],dtype=float); self.has_turned2=True
            elif self.has_turned2 and self.turn3 is not None and np.allclose(self.pos,self.turn3,atol=3.0):
                self.dir=np.array([0,-1],dtype=float)
        elif self.origin in ['Y468','Y263','O680','O263']:
            if self.origin == 'O680':
                if not self.has_turned and self.turn is not None and np.allclose(self.pos,self.turn,atol=3.0):
                    self.dir=np.array([1,0],dtype=float); self.has_turned=True
                elif self.has_turned and self.turn2 is not None and np.allclose(self.pos,self.turn2,atol=3.0):
                    self.dir=np.array([0,1],dtype=float)
            elif self.origin == 'O263':
                if not self.has_turned and self.turn is not None and np.allclose(self.pos,self.turn,atol=3.0):
                    self.dir=np.array([-1,0],dtype=float); self.has_turned=True
                elif self.has_turned and self.turn2 is not None and np.allclose(self.pos,self.turn2,atol=3.0):
                    self.dir=np.array([0,-1],dtype=float)
            elif not self.has_turned and self.turn is not None and np.allclose(self.pos,self.turn,atol=3.0):
                self.dir=np.array([-1,0],dtype=float); self.has_turned=True
            elif self.has_turned and self.turn2 is not None and np.allclose(self.pos,self.turn2,atol=3.0):
                self.dir=np.array([0,-1],dtype=float)
        else:
            if self.turn is not None and np.allclose(self.pos,self.turn,atol=3.0):
                if self.origin in ['G263','G468','B468']:     self.dir=np.array([0,-1],dtype=float)
                elif self.origin in ['G680','B680']:          self.dir=np.array([0,+1],dtype=float)
                elif self.origin in ['Y1064','O1064']:        self.dir=np.array([-1,0],dtype=float)
                elif self.origin in ['P279','O279']:          self.dir=np.array([+1,0],dtype=float)

        # ── Headway ──
        head = headway_ahead(self, cars)
        if head is not None:
            if np.linalg.norm(head.pos - self.pos) < self.p['headway']:
                vmax = 0.0

        if vmax > 0.0:
            self.pos = self.pos + self.dir * vmax
            self.is_moving = True

        L = self.p['L']
        if abs(self.pos[0]) > L or abs(self.pos[1]) > L:
            self.state = 'done'


# ── TRAFFIC MODEL (agentpy) ───────────────────────────────────────────────────
class TrafficModel(ap.Model):
    def setup(self):
        p = self.p
        self.ctrl = FourWaySignals(p['green_ns'], p['green_ew'], p['yellow'], p['all_red'])
        self.cars = ap.AgentList(self, 0, Car)
        self.throughput   = 0
        self.t            = 0
        # Count spawned cars per approach
        self.spawn_counts = {a: 0 for a in APPROACHES}

    def spawn_approach(self, approach, lam):
        """Spawn Poisson(lam) cars from `approach`; each picks its route by probability."""
        if lam <= 0: return
        k = np.random.poisson(lam)
        if k == 0: return
        group = ROUTE_GROUPS[approach]
        for _ in range(k):
            origin = np.random.choice(group['routes'], p=group['probs'])
            new_car = ap.AgentList(self, 1, Car, origin=origin, params=dict(self.p))
            self.cars = self.cars + new_car
            self.spawn_counts[approach] += 1

    def step(self):
        p = self.p
        for approach in APPROACHES:
            self.spawn_approach(approach, p[f'lambda_{approach}'])

        self.ctrl.step()
        self.cars.step()   # agentpy calls Car.step() on every agent

        done_count = sum(1 for c in self.cars if c.state == 'done')
        self.throughput += done_count
        alive_mask = [c.state != 'done' for c in self.cars]
        self.cars = self.cars.select(alive_mask)
        self.t += 1


# ── RENDERER ──────────────────────────────────────────────────────────────────
class Renderer:
    def __init__(self, screen, p):
        self.screen = screen
        self.p = p
        self.L = p['L']
        self.w = p['w']
        self.size = WINDOW_SIZE

    def w2s(self, pos):
        return world_to_screen(pos, self.L, self.size)

    def sv(self, val):
        return scale_val(val, self.L, self.size)

    def draw(self, sim):
        self.screen.fill(BG_COLOR)
        L, w = self.L, self.w

        # ── Roads ──
        road_rects = [
            (-L/2+w*2,  w*14,   L-w*3,  2*w),
            (-L/2+6,   -w*14,   L-w*3,  2*w),
            (-L,       -w*3,    2*L,    2*w),
            (-L,       -w*5,    2*L,    2*w),
            (-L,        w*3,    2*L,    2*w),
            (-L,        w*5,    2*L,    2*w),
            (-w*16,    -L,      2*w,    L-w),
            ( w*16,    -L,      2*w,    L-w),
            (-w*10,    -L,      2*w,    2*L),
            (-w*12,    -L,      2*w,    2*L),
            ( w*10,    -L,      2*w,    2*L),
            ( w*12,    -L,      2*w,    2*L),
        ]
        for x, y, rw, rh in road_rects:
            p1 = self.w2s([x, y + rh])
            p2 = self.w2s([x + rw, y])
            rect_x = min(p1[0], p2[0])
            rect_y = min(p1[1], p2[1])
            rect_w = abs(p2[0] - p1[0])
            rect_h = abs(p2[1] - p1[1])
            if rect_w > 0 and rect_h > 0:
                pygame.draw.rect(self.screen, ROAD_COLOR, (rect_x, rect_y, rect_w, rect_h))

        # ── Lane markings ──
        lane_lines = [
            ((-L, w*5),  (L, w*5)),
            ((-L,-w*3),  (L,-w*3)),
            ((w*12,-L),  (w*12, L)),
            ((-w*10,-L), (-w*10, L)),
            ((-w*16,-L), (-w*16,-w*5)),
            ((w*18,-L),  (w*18,-w*5)),
        ]
        for p1, p2 in lane_lines:
            s1 = self.w2s(p1)
            s2 = self.w2s(p2)
            pygame.draw.line(self.screen, LANE_COLOR, s1, s2, 1)

        # ── Traffic lights ──
        lights = sim.ctrl.lights()
        color_map = {
            'R': RED_LIGHT, 'Y': YELLOW_LIGHT,
            'G': GREEN_LIGHT, 'AR': AR_LIGHT
        }
        light_locs = {
            'O680': (0, w*7),
            'Y468': (0, -w*7),
            'B468': (w*7, 0),
            'G263': (-w*7, 0),
        }
        radius = int(self.sv(2.5))
        for d, (wx, wy) in light_locs.items():
            sx, sy = self.w2s([wx, wy])
            col = color_map.get(lights.get(d, 'R'), RED_LIGHT)
            pygame.draw.circle(self.screen, (40, 40, 40), (sx, sy), radius + 2)
            pygame.draw.circle(self.screen, col, (sx, sy), radius)

        # ── Cars ──
        car_r = max(3, int(self.sv(2.0)))
        for car in sim.cars:
            sx, sy = self.w2s(car.pos)
            col = CAR_MOVING if car.is_moving else CAR_STOP
            pygame.draw.circle(self.screen, col, (sx, sy), car_r)
            pygame.draw.circle(self.screen, CAR_BORDER, (sx, sy), car_r, 1)

        self._draw_hud(sim)

    def _draw_hud(self, sim):
        font_lg = pygame.font.SysFont('monospace', 18, bold=True)
        font_sm = pygame.font.SysFont('monospace', 13)

        pygame.draw.rect(self.screen, (20, 20, 20), (0, 0, WINDOW_SIZE, 36))
        title = font_lg.render(f"Traffic Simulation  |  t = {sim.t}s", True, (220, 220, 220))
        self.screen.blit(title, (10, 8))

        total = sum(sim.spawn_counts.values())
        stats = [
            f"Created : {total}",
            f"Done    : {sim.throughput}",
            f"Active  : {len(sim.cars)}",
            f"Phase   : {sim.ctrl.phase_name}",
            f"Signal  : {sim.ctrl.sub}",
            f"N:{sim.spawn_counts['Norte']} S:{sim.spawn_counts['Sur']}"
            f" E:{sim.spawn_counts['Este']} O:{sim.spawn_counts['Oeste']}",
        ]
        box_w, box_h = 180, 118
        box_x = WINDOW_SIZE - box_w - 10
        box_y = WINDOW_SIZE - box_h - 10
        s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        s.fill((10, 10, 10, 190))
        self.screen.blit(s, (box_x, box_y))
        pygame.draw.rect(self.screen, (80, 80, 80), (box_x, box_y, box_w, box_h), 1)
        for i, line in enumerate(stats):
            col = (200, 200, 200) if i < 3 else (160, 200, 160)
            txt = font_sm.render(line, True, col)
            self.screen.blit(txt, (box_x + 8, box_y + 6 + i * 18))

        hint = font_sm.render("[SPACE] Pause  [R] Reset  [ESC] Quit", True, (120, 120, 120))
        self.screen.blit(hint, (10, WINDOW_SIZE - 22))


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Traffic Light Crossing Simulation")
    clock  = pygame.time.Clock()

    sim = TrafficModel(params)
    sim.setup()
    renderer = Renderer(screen, params)

    running = True
    paused  = False
    fps     = 10

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    sim = TrafficModel(params)
                    sim.setup()
                elif event.key == pygame.K_UP:
                    fps = min(60, fps + 2)
                elif event.key == pygame.K_DOWN:
                    fps = max(1, fps - 2)

        if not paused:
            sim.step()

        renderer.draw(sim)
        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
