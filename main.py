"""
Punto de entrada — Simulación de tráfico en intersección compleja.

Uso:
    python main.py

Controles:
    SPACE          Pausar / Continuar
    R              Reiniciar
    Q / ESC        Salir
    Botones panel  Ajustar parámetros
"""

import sys
import pygame

from traffic_pygame import (
    draw_world, draw_panel, build_ui, make_model,
    WIN_W, WIN_H,
)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Tráfico — Intersección Compleja")

    font_title = pygame.font.SysFont("Arial", 13, bold=True)
    font_lbl   = pygame.font.SysFont("Arial", 12)
    font_val   = pygame.font.SysFont("Arial", 13, bold=True)

    ui     = build_ui()
    model  = make_model(ui)
    paused = False
    clock  = pygame.time.Clock()

    btn_pause   = ui["buttons"][0]
    btn_restart = ui["buttons"][1]
    stp_fps     = ui["steppers"][3]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                    btn_pause.active = paused
                elif event.key == pygame.K_r:
                    model  = make_model(ui)
                    paused = False
                    btn_pause.active = False

            for stp in ui["steppers"]:
                stp.handle_event(event)

            if btn_pause.handle_event(event):
                paused = btn_pause.active

            if btn_restart.handle_event(event):
                model  = make_model(ui)
                paused = False
                btn_pause.active = False

        ui["fps"] = int(stp_fps.value)

        if not paused:
            model.t += 1
            model.step()

        draw_world(screen, model)
        draw_panel(screen, model, ui, paused, font_title, font_lbl, font_val)

        pygame.display.flip()
        clock.tick(ui["fps"])

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
