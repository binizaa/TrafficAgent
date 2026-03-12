import random
import numpy as np
import pygame
from itertools import cycle

from config import ANCHO_MAXIMO_VENTANA, FPS, DISTANCIA_MINIMA, CSV_FILE, FONDO_PATH, SEMAFOROS
from model.car_agent import CarAgent
from model.traffic_light import TrafficLight
from engine.traffic_manager import TrafficManager
from view.renderer import draw_frame
from engine.loader import load_and_scale_paths


def _build_traffic_lights(semaforos_cfg, scale):
    lights = []
    for cfg in semaforos_cfg:
        x, y = cfg["pos"]
        light = TrafficLight(
            pos=(x * scale, y * scale),
            direccion=cfg["direccion"],
            grupo=cfg["grupo"],
        )
        lights.append(light)
    return lights


def run():
    pygame.init()

    fondo_orig = pygame.image.load(FONDO_PATH)
    rect = fondo_orig.get_rect()
    scale = ANCHO_MAXIMO_VENTANA / rect.width if rect.width > ANCHO_MAXIMO_VENTANA else 1.0

    w, h = int(rect.width * scale), int(rect.height * scale)
    fondo_scaled = pygame.transform.smoothscale(fondo_orig, (w, h))

    pantalla = pygame.display.set_mode((w, h))
    pygame.display.set_caption("Simulación de Tráfico")

    paths = load_and_scale_paths(CSV_FILE, scale)
    if not paths:
        print("Error: no se encontraron rutas en", CSV_FILE)
        pygame.quit()
        return

    traffic_lights  = _build_traffic_lights(SEMAFOROS, scale)
    traffic_manager = TrafficManager(traffic_lights)

    cycler     = cycle(paths)
    agents     = []
    reloj      = pygame.time.Clock()
    last_spawn = pygame.time.get_ticks()
    spawn_delay = 700

    paused  = False
    running = True
    while running:
        dt = reloj.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                paused = not paused

        if not paused:
            traffic_manager.update(dt)

            if pygame.time.get_ticks() - last_spawn > spawn_delay:
                color = (random.randint(100, 255), random.randint(100, 255), 60)
                nuevo_camino = next(cycler)

                puede_aparecer = True
                inicio = np.array(nuevo_camino[0])
                for a in agents:
                    if np.linalg.norm(a.pos - inicio) < DISTANCIA_MINIMA * 1.5:
                        puede_aparecer = False
                        break

                if puede_aparecer:
                    agents.append(CarAgent(nuevo_camino, color, random.uniform(2.0, 3.5)))
                    last_spawn = pygame.time.get_ticks()

            for a in agents:
                a.update(agents, traffic_lights, dt)

            agents = [a for a in agents if a.active]

        draw_frame(pantalla, fondo_scaled, agents, traffic_lights, reloj.get_fps(), paused)

    pygame.quit()
