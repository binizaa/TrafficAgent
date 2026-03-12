import cv2
import numpy as np
import random
import time
import os
import csv
import pygame
from itertools import cycle

# --- CONFIGURACIÓN ---
CSV_FILE = 'rutas_cache.csv'
FONDO_PATH = 'images/fondo.png'
ANCHO_MAXIMO_VENTANA = 1000  
FPS = 60

# Radio del dibujo del coche (visual)
RADIO_COCHE = 8
# Distancia mínima entre centros para que NUNCA se toquen los bordes
# Si el radio es 8, el diámetro es 16. Ponemos 24 para dejar un margen de 8px de aire.
DISTANCIA_MINIMA = 24 

class CarAgent:
    def __init__(self, path, color, speed):
        self.path = path              
        self.color = color            
        self.base_speed = speed       
        self.current_speed = speed
        self.current_step = 0.0
        self.active = True if path else False
        self.pos = np.array(path[0], dtype=float) if path else np.array([0.0, 0.0])

    def update(self, other_agents):
        if not self.active: return
        
        # Intentamos ir a la velocidad máxima por defecto
        target_speed = self.base_speed
        
        mi_idx = int(self.current_step)
        self.pos = np.array(self.path[min(mi_idx, len(self.path)-1)], dtype=float)
        
        for other in other_agents:
            if other is self: continue
            
            # Vector de distancia
            dist_vec = other.pos - self.pos
            distancia = np.linalg.norm(dist_vec)
            
            # Filtro: Solo nos importa si está adelante en la misma ruta o cerca
            if distancia < DISTANCIA_MINIMA * 2: # Detectar desde un poco antes
                if other.current_step > self.current_step:
                    if distancia < DISTANCIA_MINIMA:
                        # Demasiado cerca: Frenazo total para mantener el hueco
                        target_speed = 0
                    else:
                        # Zona de precaución: Ajustar velocidad para no alcanzarlo
                        # Mantenemos una proporción de la velocidad del de adelante
                        ratio = (distancia - DISTANCIA_MINIMA) / DISTANCIA_MINIMA
                        target_speed = min(self.base_speed, other.current_speed * ratio)
                    break

        # Suavizado de aceleración/frenado para que no "vibre"
        self.current_speed = target_speed
        self.current_step += self.current_speed
        
        if int(self.current_step) >= len(self.path):
            self.active = False

    def draw(self, surface):
        if not self.active: return
        p = (int(self.pos[0]), int(self.pos[1]))
        # Dibujo del coche
        pygame.draw.circle(surface, (20, 20, 20), p, RADIO_COCHE + 1) # Borde
        pygame.draw.circle(surface, self.color, p, RADIO_COCHE)       # Color

def load_and_scale_paths(filename, scale_factor):
    if not os.path.exists(filename): return None
    paths = []
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            points = []
            for p in row[1].split(";"):
                coords = p.split(",")
                points.append((float(coords[0]) * scale_factor, float(coords[1]) * scale_factor))
            paths.append(points)
    return paths

def run_simulation():
    pygame.init()
    
    fondo_orig = pygame.image.load(FONDO_PATH)
    rect = fondo_orig.get_rect()
    scale = ANCHO_MAXIMO_VENTANA / rect.width if rect.width > ANCHO_MAXIMO_VENTANA else 1.0
    
    w, h = int(rect.width * scale), int(rect.height * scale)
    fondo_scaled = pygame.transform.smoothscale(fondo_orig, (w, h))
    
    pantalla = pygame.display.set_mode((w, h))
    pygame.display.set_caption("Simulación de Tráfico: Espaciado Rígido")
    
    interleaved_paths = load_and_scale_paths(CSV_FILE, scale)
    if not interleaved_paths: return

    cycler = cycle(interleaved_paths)
    agents = []
    reloj = pygame.time.Clock()
    last_spawn = pygame.time.get_ticks()
    spawn_delay = 700 

    running = True
    while running:
        reloj.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

        if pygame.time.get_ticks() - last_spawn > spawn_delay:
            color = (random.randint(100, 255), random.randint(100, 255), 60)
            nuevo_camino = next(cycler)
            
            # Validación de spawn MUY estricta:
            puede_aparecer = True
            inicio_nuevo = np.array(nuevo_camino[0]) * scale
            for a in agents:
                if np.linalg.norm(a.pos - inicio_nuevo) < DISTANCIA_MINIMA * 1.5:
                    puede_aparecer = False
                    break
            
            if puede_aparecer:
                agents.append(CarAgent(nuevo_camino, color, random.uniform(2.0, 3.5)))
                last_spawn = pygame.time.get_ticks()

        # Actualización
        for a in agents:
            a.update(agents)
        
        agents = [a for a in agents if a.active]

        # Render
        pantalla.blit(fondo_scaled, (0, 0))
        for a in agents:
            a.draw(pantalla)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    run_simulation()