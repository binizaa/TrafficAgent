import pygame
from config import RADIO_COCHE


def draw_agent(surface, agent):
    if not agent.active:
        return
    p = (int(agent.pos[0]), int(agent.pos[1]))
    pygame.draw.circle(surface, (20, 20, 20), p, RADIO_COCHE + 1)
    pygame.draw.circle(surface, agent.color, p, RADIO_COCHE)


def draw_frame(surface, background, agents):
    surface.blit(background, (0, 0))
    for agent in agents:
        draw_agent(surface, agent)
    pygame.display.flip()
