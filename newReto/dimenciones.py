import cv2
import numpy as np
import random
import time
from itertools import cycle

# --- CLASE PARA EL AGENTE ---
class CarAgent:
    def __init__(self, path, color, speed, path_id):
        self.path = path              
        self.color = color            
        self.speed = speed            
        self.current_step = 0.0
        self.position = path[0] if path else (0,0)
        self.active = True if path else False
        self.path_id = path_id 

    def update(self, width, height):
        if not self.active: return

        self.current_step += self.speed
        idx = int(self.current_step)

        if idx >= len(self.path):
            self.active = False
            return

        self.position = self.path[idx]
        px, py = self.position

        # Margen de eliminación
        margin = 2
        if px <= margin or px >= width - margin or py <= margin or py >= height - margin:
            self.active = False

    def draw(self, img):
        if not self.active: return
        pos = (int(self.position[0]), int(self.position[1]))
        cv2.circle(img, pos, 13, self.color, -1)
        cv2.circle(img, pos, 14, (0, 0, 0), 1)

# --- PROCESAMIENTO DE RUTAS (LÓGICA INVERSA: AZUL -> ROJO) ---
def get_ordered_paths(routes_img_path, target_size):
    routes_img = cv2.imread(routes_img_path)
    if routes_img is None: return []
    
    routes_img = cv2.resize(routes_img, target_size)
    hsv = cv2.cvtColor(routes_img, cv2.COLOR_BGR2HSV)
    
    # 1. Máscaras
    mask_red1 = cv2.inRange(hsv, np.array([0, 150, 50]), np.array([10, 255, 255]))
    mask_red2 = cv2.inRange(hsv, np.array([170, 150, 50]), np.array([180, 255, 255]))
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)
    mask_blue = cv2.inRange(hsv, np.array([100, 150, 50]), np.array([140, 255, 255]))

    # 2. Esqueleto de las rutas rojas
    skeleton = cv2.ximgproc.thinning(mask_red, thinningType=cv2.ximgproc.THINNING_GUOHALL)
    
    # 3. Encontrar puntos de contacto (donde el azul toca el esqueleto rojo)
    # Dilatamos un poco el azul para asegurar intersección con el esqueleto de 1px
    kernel = np.ones((5,5), np.uint8)
    dilated_blue = cv2.dilate(mask_blue, kernel)
    start_points_mask = cv2.bitwise_and(skeleton, dilated_blue)
    
    # Obtener coordenadas de los puntos de inicio (semillas)
    start_y, start_x = np.where(start_points_mask > 0)
    seeds = list(zip(start_x, start_y))

    if not seeds:
        print("No se encontraron puntos donde el Rojo nazca del Azul.")
        return []

    # 4. Reconstrucción de rutas desde cada semilla
    ordered_paths = []
    
    # Para no repetir rutas si una zona azul es ancha
    visited_global = np.zeros_like(skeleton)

    for idx, (sx, sy) in enumerate(seeds):
        if visited_global[sy, sx]: continue
        
        path_pts = []
        curr_x, curr_y = sx, sy
        
        # Algoritmo de seguimiento de línea simple
        while True:
            path_pts.append((curr_x, curr_y))
            visited_global[curr_y, curr_x] = 255
            
            # Buscar vecino en el esqueleto no visitado (8-conectividad)
            roi = skeleton[max(0, curr_y-1):curr_y+2, max(0, curr_x-1):curr_x+2]
            found_next = False
            
            # Buscamos en los 8 vecinos
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0: continue
                    nx, ny = curr_x + dx, curr_y + dy
                    
                    if (0 <= ny < skeleton.shape[0] and 0 <= nx < skeleton.shape[1] and 
                        skeleton[ny, nx] > 0 and not visited_global[ny, nx]):
                        curr_x, curr_y = nx, ny
                        found_next = True
                        break
                if found_next: break
            
            if not found_next: break
            
        if len(path_pts) > 15: # Ignorar fragmentos cortos
            ordered_paths.append({'id': idx, 'pts': path_pts})

    return ordered_paths

# --- SIMULACIÓN ---
def run_simulation(base_img_path, routes_img_path):
    base_img = cv2.imread(base_img_path)
    if base_img is None: return
    
    h, w = base_img.shape[:2]
    all_paths = get_ordered_paths(routes_img_path, (w, h))
    
    if not all_paths:
        print("Error: No se detectaron rutas que inicien en azul.")
        return

    print(f"Rutas activas: {len(all_paths)}")
    path_cycler = cycle(all_paths)
    agents = []
    last_spawn_time = time.time()
    spawn_delay = 0.5 

    while True:
        frame_img = base_img.copy()
        
        if time.time() - last_spawn_time > spawn_delay:
            p_data = next(path_cycler)
            agents.append(CarAgent(
                path=p_data['pts'],
                color=(random.randint(50,255), random.randint(50,255), random.randint(50,255)),
                speed=random.uniform(2, 5),
                path_id=p_data['id']
            ))
            last_spawn_time = time.time()

        agents = [a for a in agents if a.active]
        for agent in agents:
            agent.update(w, h)
            agent.draw(frame_img)

        cv2.imshow('Simulacion: Salida desde Zona Azul', frame_img)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_simulation('images/fondo.png', 'images/rutas/ruta4.png')