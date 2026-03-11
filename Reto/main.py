"""
Traffic Light Crossing - Pygame Migration
Migrated from agentpy/matplotlib to pygame
"""

import pygame
import numpy as np
import sys
import math

# ── PARAMETERS ────────────────────────────────────────────────────────────────
params = {
    'steps': 150,
    'green_ns': 10,
    'green_ew': 10,
    'yellow': 5,
    'all_red': 6,
    'interval_G263': 5,  'interval_P279': 5,
    'interval_G279': 5,  'interval_G468': 5,
    'interval_G680': 0,  'interval_Y468': 5,
    'interval_Y263': 5,  'interval_Y1064': 5,
    'interval_Y680': 5,  'interval_B468': 5,
    'interval_B263': 5,  'interval_B1064': 5,
    'interval_B680': 5,  'interval_O680': 5,
    'interval_O279': 5,  'interval_O263': 5,
    'interval_O1064': 5,
    'v_free': 7.0,
    'headway': 8.0,
    'L': 80.0,
    'w': 3.5
}

# ── COLORS ────────────────────────────────────────────────────────────────────
BG_COLOR      = (34, 34, 34)
ROAD_COLOR    = (80, 80, 80)
LANE_COLOR    = (200, 200, 200)
CAR_MOVING    = (30, 120, 210)
CAR_STOP      = (70, 90, 100)
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

# ── CAR AGENT ─────────────────────────────────────────────────────────────────
class Car:
    def __init__(self, origin, p):
        self.origin = origin
        self.state  = 'moving'
        self.v      = p['v_free']
        self.p      = p
        L, w        = p['L'], p['w']
        off         = w / 2

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

    def step(self, lights, cars):
        if self.state == 'done': return
        if self.dist_to(self.goal) < 3.0:
            self.state = 'done'; return

        vmax = self.v

        if self.stopline is not None and np.allclose(self.pos, self.stopline, atol=3.0) and lights[self.origin] != 'G':
            return

        # Turns
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
                if self.origin in ['G263','G468','B468']:         self.dir=np.array([0,-1],dtype=float)
                elif self.origin in ['G680','B680']:              self.dir=np.array([0,+1],dtype=float)
                elif self.origin in ['Y1064','O1064']:            self.dir=np.array([-1,0],dtype=float)
                elif self.origin in ['P279','O279']:              self.dir=np.array([+1,0],dtype=float)

        # Headway
        head = headway_ahead(self, cars, self.p['headway'])
        if head is not None:
            if np.linalg.norm(head.pos - self.pos) < self.p['headway']:
                vmax = 0.0

        if vmax > 0.0:
            self.pos = self.pos + self.dir * vmax

        L = self.p['L']
        if abs(self.pos[0]) > L or abs(self.pos[1]) > L:
            self.state = 'done'


def headway_ahead(me, cars, headway_dist):
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
    ahead = [(np.dot(c.pos-me.pos, me.dir), c)
             for c in same_lane if np.dot(c.pos-me.pos, me.dir) > 0]
    return min(ahead, key=lambda x: x[0])[1] if ahead else None


# ── SIMULATION ────────────────────────────────────────────────────────────────
class TrafficSimulation:
    def __init__(self, p):
        self.p = p
        self.ctrl = FourWaySignals(p['green_ns'], p['green_ew'], p['yellow'], p['all_red'])
        self.cars = []
        self.t = 0
        self.throughput = 0
        self.spawn_counts = {d: 0 for d in [
            'G263','G279','G468','G680',
            'Y468','Y263','Y1064','Y680','P279',
            'B468','B263','B1064','B680',
            'O680','O279','O263','O1064'
        ]}

    def spawn(self, origin, interval):
        if interval <= 0: return
        if self.t % interval == 0:
            self.cars.append(Car(origin, self.p))
            self.spawn_counts[origin] += 1

    def step(self):
        p = self.p
        self.spawn('G263',  p['interval_G263'])
        self.spawn('G279',  p['interval_G279'])
        self.spawn('G468',  p['interval_G468'])
        self.spawn('G680',  p['interval_G680'])
        self.spawn('Y468',  p['interval_Y468'])
        self.spawn('Y263',  p['interval_Y263'])
        self.spawn('Y1064', p['interval_Y1064'])
        self.spawn('Y680',  p['interval_Y680'])
        self.spawn('P279',  p['interval_P279'])
        self.spawn('B468',  p['interval_B468'])
        self.spawn('B263',  p['interval_B263'])
        self.spawn('B1064', p['interval_B1064'])
        self.spawn('B680',  p['interval_B680'])
        self.spawn('O680',  p['interval_O680'])
        self.spawn('O279',  p['interval_O279'])
        self.spawn('O263',  p['interval_O263'])
        self.spawn('O1064', p['interval_O1064'])

        self.ctrl.step()
        lights = self.ctrl.lights()

        for car in self.cars:
            car.step(lights, self.cars)

        done = [c for c in self.cars if c.state == 'done']
        self.throughput += len(done)
        self.cars = [c for c in self.cars if c.state != 'done']
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

    def draw_road(self, x, y, width, height, color=ROAD_COLOR):
        sx, sy = self.w2s([x, y + height])
        sw = int(abs(self.sv(width)))
        sh = int(abs(self.sv(height)))
        if sw > 0 and sh > 0:
            pygame.draw.rect(self.screen, color, (sx, sy, sw, sh))

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
            col = CAR_MOVING if car.state == 'moving' else CAR_STOP
            pygame.draw.circle(self.screen, col, (sx, sy), car_r)
            pygame.draw.circle(self.screen, CAR_BORDER, (sx, sy), car_r, 1)

        # ── HUD ──
        self._draw_hud(sim)

    def _draw_hud(self, sim):
        font_lg = pygame.font.SysFont('monospace', 18, bold=True)
        font_sm = pygame.font.SysFont('monospace', 13)

        # Top bar
        pygame.draw.rect(self.screen, (20, 20, 20), (0, 0, WINDOW_SIZE, 36))
        title = font_lg.render(f"Traffic Simulation  |  t = {sim.t}s", True, (220, 220, 220))
        self.screen.blit(title, (10, 8))

        # Stats box (bottom-right)
        total = sum(sim.spawn_counts.values())
        stats = [
            f"Created : {total}",
            f"Done    : {sim.throughput}",
            f"Active  : {len(sim.cars)}",
            f"Phase   : {sim.ctrl.phase_name}",
            f"Signal  : {sim.ctrl.sub}",
        ]
        box_w, box_h = 180, 100
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

        # Controls hint
        hint = font_sm.render("[SPACE] Pause  [R] Reset  [ESC] Quit", True, (120, 120, 120))
        self.screen.blit(hint, (10, WINDOW_SIZE - 22))


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Traffic Light Crossing Simulation")
    clock  = pygame.time.Clock()

    sim      = TrafficSimulation(params)
    renderer = Renderer(screen, params)

    running = True
    paused  = False
    fps     = 10  # simulation speed

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
                    sim = TrafficSimulation(params)
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