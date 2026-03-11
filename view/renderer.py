import pygame
from config import RADIO_COCHE

_font = None

def _get_font():
    global _font
    if _font is None:
        _font = pygame.font.SysFont("monospace", 15, bold=True)
    return _font


def draw_agent(surface, agent):
    if not agent.active:
        return
    p = (int(agent.pos[0]), int(agent.pos[1]))
    pygame.draw.circle(surface, (20, 20, 20), p, RADIO_COCHE + 1)
    pygame.draw.circle(surface, agent.color, p, RADIO_COCHE)


def draw_hud(surface, fps, agent_count, paused):
    font = _get_font()
    lines = [
        f"FPS:    {fps:5.1f}",
        f"Carros: {agent_count:5d}",
        f"{'[PAUSA]' if paused else ''}",
    ]
    padding = 8
    line_h = font.get_linesize()
    box_w = 140
    box_h = len(lines) * line_h + padding * 2

    # Fondo semitransparente
    overlay = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (10, 10))

    for i, text in enumerate(lines):
        color = (255, 80, 80) if paused and i == 2 else (220, 220, 220)
        surf = font.render(text, True, color)
        surface.blit(surf, (10 + padding, 10 + padding + i * line_h))


def draw_frame(surface, background, agents, fps, paused):
    surface.blit(background, (0, 0))
    for agent in agents:
        draw_agent(surface, agent)
    draw_hud(surface, fps, len(agents), paused)
    pygame.display.flip()
