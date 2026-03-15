import os
import pygame

from config import (
    SIM_SIZE, MARGIN,
    BG_COLOR, ROAD_COLOR, LANE_COLOR,
    CAR_MOVING, CAR_STOP, CAR_BORDER,
    RED_LIGHT, YELLOW_LIGHT, GREEN_LIGHT, AR_LIGHT,
)
from model.traffic_model import TrafficModel


def world_to_screen(pos, L, screen_size):
    scale = (screen_size - 2 * MARGIN) / (2 * L)
    sx = int((pos[0] + L) * scale + MARGIN)
    sy = int((L - pos[1]) * scale + MARGIN)
    return sx, sy


def scale_val(val, L, screen_size):
    return val * (screen_size - 2 * MARGIN) / (2 * L)


class Renderer:
    def __init__(self, screen, p):
        self.screen = screen
        self.p      = p
        self.L      = p['L']
        self.w      = p['w']
        self.size   = SIM_SIZE

    def w2s(self, pos):
        return world_to_screen(pos, self.L, self.size)

    def sv(self, val):
        return scale_val(val, self.L, self.size)

    def draw(self, sim):
        self.screen.fill(BG_COLOR)
        L, w = self.L, self.w

        # ── Carreteras ──
        road_rects = [
            (-L/2+w*2,  w*14,  L-w*3, 2*w),
            (-L/2+6,   -w*14,  L-w*3, 2*w),
            (-L,       -w*3,   2*L,   2*w),
            (-L,       -w*5,   2*L,   2*w),
            (-L,        w*3,   2*L,   2*w),
            (-L,        w*5,   2*L,   2*w),
            (-w*16,    -L,     2*w,   L-w),
            ( w*16,    -L,     2*w,   L-w),
            (-w*10,    -L,     2*w,   2*L),
            (-w*12,    -L,     2*w,   2*L),
            ( w*10,    -L,     2*w,   2*L),
            ( w*12,    -L,     2*w,   2*L),
        ]
        for x, y, rw, rh in road_rects:
            p1 = self.w2s([x, y + rh])
            p2 = self.w2s([x + rw, y])
            rx = min(p1[0], p2[0]); ry = min(p1[1], p2[1])
            rwidth = abs(p2[0] - p1[0]); rheight = abs(p2[1] - p1[1])
            if rwidth > 0 and rheight > 0:
                pygame.draw.rect(self.screen, ROAD_COLOR, (rx, ry, rwidth, rheight))

        # ── Marcas de carril ──
        lane_lines = [
            ((-L, w*5),  (L, w*5)),
            ((-L,-w*3),  (L,-w*3)),
            ((w*12,-L),  (w*12, L)),
            ((-w*10,-L), (-w*10, L)),
            ((-w*16,-L), (-w*16,-w*5)),
            ((w*18,-L),  (w*18,-w*5)),
        ]
        for p1, p2 in lane_lines:
            pygame.draw.line(self.screen, LANE_COLOR, self.w2s(p1), self.w2s(p2), 1)

        # ── Semáforos ──
        lights    = sim.ctrl.lights()
        color_map = {'R': RED_LIGHT, 'Y': YELLOW_LIGHT, 'G': GREEN_LIGHT, 'AR': AR_LIGHT}
        light_locs = {
            'O680': (0,  w*7),
            'Y468': (0, -w*7),
            'B468': ( w*7, 0),
            'G263': (-w*7, 0),
        }
        radius = int(self.sv(2.5))
        for d, (wx, wy) in light_locs.items():
            sx, sy = self.w2s([wx, wy])
            col = color_map.get(lights.get(d, 'R'), RED_LIGHT)
            pygame.draw.circle(self.screen, (40, 40, 40), (sx, sy), radius + 2)
            pygame.draw.circle(self.screen, col, (sx, sy), radius)

        # ── Etiquetas de avenidas ──
        self._draw_road_labels(L, w)

        # ── Autos ──
        car_r = max(3, int(self.sv(2.0)))
        for car in sim.cars:
            sx, sy = self.w2s(car.pos)
            col = CAR_MOVING if car.is_moving else CAR_STOP
            pygame.draw.circle(self.screen, col, (sx, sy), car_r)
            pygame.draw.circle(self.screen, CAR_BORDER, (sx, sy), car_r, 1)

    def _draw_road_labels(self, L, w):
        font  = pygame.font.SysFont('monospace', 11, bold=True)
        COLOR = (230, 220, 80)
        off   = w / 2

        def blit_h(world_x, world_y, text, right_align=False):
            sx, sy = self.w2s([world_x, world_y])
            surf = font.render(text, True, COLOR)
            x = sx - surf.get_width() - 3 if right_align else sx + 3
            self.screen.blit(surf, (x, sy - surf.get_height() // 2))

        def blit_v(world_x, world_y, text, rotate_deg=90):
            sx, sy   = self.w2s([world_x, world_y])
            surf     = font.render(text, True, COLOR)
            rotated  = pygame.transform.rotate(surf, rotate_deg)
            self.screen.blit(rotated, (sx - rotated.get_width() // 2,
                                       sy - rotated.get_height() // 2))

        blit_h(-L, -off - w*4, "Av. 263 / 468")
        blit_h(-L, -off - w*2, "Av. 279 / 680")
        blit_h( L,  off + w*3, "Av. 468 / 263",  right_align=True)
        blit_h( L,  off + w*5, "Av. 1064 / 680", right_align=True)
        blit_v(off + w*10, -L, "Av. 468 / 263",  rotate_deg=90)
        blit_v(off + w*12, -L, "Av. 1064 / 680", rotate_deg=90)
        blit_v(off + w*16, -L, "Paseo 279",       rotate_deg=90)
        blit_v(-off - w*8,  L, "Av. 680 / 279",  rotate_deg=-90)
        blit_v(-off - w*10, L, "Av. 263 / 1064", rotate_deg=-90)


def save_background_png(p, out_dir):
    surf    = pygame.Surface((SIM_SIZE, SIM_SIZE))
    sim_tmp = TrafficModel(p)
    sim_tmp.setup()
    Renderer(surf, p).draw(sim_tmp)
    out = os.path.join(out_dir, 'background.png')
    pygame.image.save(surf, out)
    print(f"background.png guardado en: {out}")
