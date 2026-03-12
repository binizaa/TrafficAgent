"""
Traffic Light Crossing - agentpy + pygame
Punto de entrada principal.
"""
import sys
import os
import pygame

from config import DEFAULT_PARAMS, SIM_SIZE, UI_WIDTH, WINDOW_W, WINDOW_H
from model import TrafficModel
from views import Renderer, MenuScreen, Button, save_background_png


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Traffic Light Crossing Simulation")
    clock = pygame.time.Clock()

    save_background_png(DEFAULT_PARAMS, os.path.dirname(os.path.abspath(__file__)))

    cur_params = dict(DEFAULT_PARAMS)
    menu       = MenuScreen(screen)
    state      = 'menu'   # 'menu' | 'running' | 'paused'
    sim        = None
    renderer   = None
    fps        = 10

    font_btn = pygame.font.SysFont('monospace', 14, bold=True)
    font_sm  = pygame.font.SysFont('monospace', 12)
    font_hdr = pygame.font.SysFont('monospace', 11, bold=True)

    PX = SIM_SIZE + 20        # left edge inside right panel
    PW = UI_WIDTH - 40        # button width
    btn_pause = Button(PX, 60,  PW, 36, 'Pausar',   (50, 80, 150), (70, 110, 210))
    btn_stop  = Button(PX, 106, PW, 36, 'Terminar', (140, 40, 40), (200, 60, 60))

    running = True
    while running:
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state == 'menu':
                        running = False
                    else:
                        state = 'menu'
                elif state != 'menu':
                    if event.key == pygame.K_UP:
                        fps = min(60, fps + 2)
                    elif event.key == pygame.K_DOWN:
                        fps = max(1, fps - 2)

            if state == 'menu':
                result = menu.handle(event, cur_params)
                if result == 'start':
                    sim      = TrafficModel(cur_params)
                    sim.setup()
                    renderer = Renderer(screen, cur_params)
                    state    = 'running'
            elif state in ('running', 'paused'):
                if btn_pause.clicked(event):
                    state = 'paused' if state == 'running' else 'running'
                if btn_stop.clicked(event):
                    state = 'menu'

        if state == 'running':
            sim.step()

        # ── Render ──
        if state == 'menu':
            menu.draw(cur_params)
        else:
            renderer.draw(sim)

            # Panel derecho
            pygame.draw.rect(screen, (15, 18, 25), (SIM_SIZE, 0, UI_WIDTH, WINDOW_H))
            pygame.draw.line(screen, (60, 60, 60), (SIM_SIZE, 0), (SIM_SIZE, WINDOW_H), 1)

            ptitle = font_hdr.render('CONTROL', True, (160, 160, 200))
            screen.blit(ptitle, (SIM_SIZE + (UI_WIDTH - ptitle.get_width()) // 2, 20))
            pygame.draw.line(screen, (50, 50, 70), (SIM_SIZE + 10, 46), (SIM_SIZE + UI_WIDTH - 10, 46), 1)

            btn_pause.text = 'Reanudar' if state == 'paused' else 'Pausar'
            btn_pause.draw(screen, font_btn)
            btn_stop.draw(screen, font_btn)

            pygame.draw.line(screen, (50, 50, 70), (SIM_SIZE + 10, 154), (SIM_SIZE + UI_WIDTH - 10, 154), 1)
            shdr = font_hdr.render('ESTADÍSTICAS', True, (120, 180, 255))
            screen.blit(shdr, (PX, 162))

            total = sum(sim.spawn_counts.values())
            for idx, (txt, col) in enumerate([
                (f"Tiempo:     {sim.t} pasos",    (180, 180, 180)),
                (f"Creados:    {total}",           (180, 180, 180)),
                (f"Finalizados:{sim.throughput}",  (130, 220, 130)),
                (f"Activos:    {len(sim.cars)}",   (220, 180, 80)),
            ]):
                screen.blit(font_sm.render(txt, True, col), (PX, 182 + idx * 20))

            pygame.draw.line(screen, (50, 50, 70), (SIM_SIZE + 10, 270), (SIM_SIZE + UI_WIDTH - 10, 270), 1)
            screen.blit(font_hdr.render('SEMÁFORO', True, (120, 180, 255)), (PX, 278))
            for idx, (txt, col) in enumerate([
                (f"Fase:  {sim.ctrl.phase_name}", (200, 200, 100)),
                (f"Señal: {sim.ctrl.sub}",        (200, 200, 100)),
            ]):
                screen.blit(font_sm.render(txt, True, col), (PX, 298 + idx * 20))

            pygame.draw.line(screen, (50, 50, 70), (SIM_SIZE + 10, 346), (SIM_SIZE + UI_WIDTH - 10, 346), 1)
            screen.blit(font_hdr.render('LLEGADAS', True, (120, 180, 255)), (PX, 354))
            for idx, (ap, cnt) in enumerate(sim.spawn_counts.items()):
                txt = f"{ap+':':<8}{cnt}"
                screen.blit(font_sm.render(txt, True, (160, 210, 160)), (PX, 374 + idx * 20))

            screen.blit(font_sm.render("[↑↓] vel   [ESC] menú", True, (70, 70, 70)), (PX, WINDOW_H - 20))

        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
