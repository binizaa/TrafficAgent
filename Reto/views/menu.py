import pygame

from config import WINDOW_W, WINDOW_H, TUNABLE_PARAMS, PARAM_SECTIONS


class Button:
    def __init__(self, x, y, w, h, text, color, hover):
        self.rect  = pygame.Rect(x, y, w, h)
        self.text  = text
        self.color = color
        self.hover = hover

    def draw(self, screen, font, text_color=(255, 255, 255)):
        col = self.hover if self.rect.collidepoint(pygame.mouse.get_pos()) else self.color
        pygame.draw.rect(screen, col, self.rect, border_radius=5)
        pygame.draw.rect(screen, (180, 180, 180), self.rect, 1, border_radius=5)
        surf = font.render(self.text, True, text_color)
        screen.blit(surf, (
            self.rect.x + (self.rect.w - surf.get_width())  // 2,
            self.rect.y + (self.rect.h - surf.get_height()) // 2,
        ))

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


class MenuScreen:
    _ROW_H   = 42
    _FIRST_Y = 100
    _SEC_PAD = 24
    _LABEL_X = 80
    _MINUS_X = 720
    _VAL_X   = 760
    _PLUS_X  = 800

    def _row_y(self, i):
        extra = sum(self._SEC_PAD for s in PARAM_SECTIONS if s <= i)
        return self._FIRST_Y + i * self._ROW_H + extra

    def __init__(self, screen):
        self.screen = screen
        self._btn_minus, self._btn_plus = [], []
        for i in range(len(TUNABLE_PARAMS)):
            y  = self._row_y(i)
            cy = y + (self._ROW_H - 28) // 2
            self._btn_minus.append(Button(self._MINUS_X, cy, 32, 28, '-', (120, 40, 40), (180, 60, 60)))
            self._btn_plus.append( Button(self._PLUS_X,  cy, 32, 28, '+', (40, 110, 40), (60, 160, 60)))

        start_y = self._row_y(len(TUNABLE_PARAMS)) + 20

        # Botón toggle heurística
        toggle_y = start_y
        self._btn_toggle = Button(WINDOW_W // 2 - 140, toggle_y, 280, 38,
                                  '', (60, 40, 100), (90, 60, 150))

        self._btn_start = Button(WINDOW_W // 2 - 140, toggle_y + 50, 280, 48,
                                 'INICIAR SIMULACIÓN', (30, 100, 30), (50, 160, 50))

    def handle(self, event, p):
        for i, (key, _, vmin, vmax, step) in enumerate(TUNABLE_PARAMS):
            if self._btn_minus[i].clicked(event):
                p[key] = round(max(vmin, p[key] - step), 3)
            if self._btn_plus[i].clicked(event):
                p[key] = round(min(vmax, p[key] + step), 3)
        if self._btn_toggle.clicked(event):
            p['use_heuristic'] = not p.get('use_heuristic', True)
        if self._btn_start.clicked(event):
            return 'start'
        return None

    def draw(self, p):
        font_lg = pygame.font.SysFont('monospace', 20, bold=True)
        font_md = pygame.font.SysFont('monospace', 14)
        font_sm = pygame.font.SysFont('monospace', 12)

        self.screen.fill((20, 24, 32))

        title = font_lg.render('SIMULACIÓN DE TRÁFICO — PARÁMETROS', True, (220, 220, 90))
        self.screen.blit(title, (WINDOW_W // 2 - title.get_width() // 2, 30))
        pygame.draw.line(self.screen, (70, 70, 70), (60, 68), (WINDOW_W - 60, 68), 1)

        for i, (key, label, _, _, step) in enumerate(TUNABLE_PARAMS):
            y = self._row_y(i)

            if i in PARAM_SECTIONS:
                hdr = font_sm.render(PARAM_SECTIONS[i], True, (120, 180, 255))
                self.screen.blit(hdr, (self._LABEL_X, y - 18))
                pygame.draw.line(self.screen, (45, 55, 75),
                                 (self._LABEL_X, y - 6), (WINDOW_W - self._LABEL_X, y - 6), 1)

            row_rect = pygame.Rect(self._LABEL_X - 6, y, WINDOW_W - self._LABEL_X * 2 + 12, self._ROW_H)
            if row_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(self.screen, (30, 35, 48), row_rect, border_radius=4)

            lbl = font_md.render(label, True, (200, 200, 200))
            self.screen.blit(lbl, (self._LABEL_X, y + (self._ROW_H - lbl.get_height()) // 2))

            val_str = f'{p[key]:.1f}' if isinstance(step, float) else str(p[key])
            val = font_md.render(val_str, True, (100, 240, 120))
            self.screen.blit(val, (self._VAL_X, y + (self._ROW_H - val.get_height()) // 2))

            self._btn_minus[i].draw(self.screen, font_md)
            self._btn_plus[i].draw(self.screen, font_md)

        # Render toggle heurística
        use_h = p.get('use_heuristic', True)
        toggle_color = (30, 110, 50) if use_h else (110, 50, 30)
        toggle_hover  = (50, 160, 70) if use_h else (160, 70, 50)
        self._btn_toggle.color = toggle_color
        self._btn_toggle.hover = toggle_hover
        self._btn_toggle.text  = ('Modo: CON heuristica' if use_h
                                  else 'Modo: SIN heuristica')
        self._btn_toggle.draw(self.screen, font_md)

        self._btn_start.draw(self.screen, font_lg)

        hint = font_sm.render('[ESC] Salir', True, (90, 90, 90))
        self.screen.blit(hint, (10, WINDOW_H - 22))
