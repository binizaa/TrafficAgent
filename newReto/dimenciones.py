import cv2
import numpy as np
import random
import time
from itertools import cycle # Importante para intercalar

# --- CLASE PARA EL AGENTE (VEHÍCULO) ---
class CarAgent:
    def __init__(self, path, color, speed, path_id):
        self.path = path              
        self.color = color            
        self.speed = speed            
        self.current_step = 0.0
        self.position = path[0]
        self.active = True
        self.path_id = path_id # Para identificar visualmente la ruta

    def update(self, width, height):
        if not self.active: return

        self.current_step += self.speed
        idx = int(self.current_step)

        if idx >= len(self.path):
            self.active = False
            return

        self.position = self.path[idx]
        x, y = self.position

        margin = 2
        if x <= margin or x >= width - margin or y <= margin or y >= height - margin:
            self.active = False

    def draw(self, img):
        if not self.active: return
        pos = (int(self.position[0]), int(self.position[1]))
        # Dibujar el agente
        cv2.circle(img, pos, 6, self.color, -1)
        cv2.circle(img, pos, 7, (0, 0, 0), 1)
        # Mostrar el ID de la ruta sobre el carro para verificar que todas funcionan
        cv2.putText(img, str(self.path_id), (pos[0]-5, pos[1]-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,0), 1)

# --- FUNCIÓN PARA PROCESAR LAS RUTAS ---
def get_ordered_paths(routes_img_path, target_size):
    routes_img = cv2.imread(routes_img_path)
    if routes_img is None: return []
    routes_img = cv2.resize(routes_img, target_size)

    hsv = cv2.cvtColor(routes_img, cv2.COLOR_BGR2HSV)
    mask = cv2.bitwise_or(
        cv2.inRange(hsv, np.array([0, 120, 70]), np.array([10, 255, 255])),
        cv2.inRange(hsv, np.array([170, 120, 70]), np.array([180, 255, 255]))
    )

    skeleton = cv2.ximgproc.thinning(mask, thinningType=cv2.ximgproc.THINNING_GUOHALL)
    contours, _ = cv2.findContours(skeleton, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    paths = []
    for i, cnt in enumerate(contours):
        pts = [tuple(p[0]) for p in cnt]
        if len(pts) > 20: 
            # Guardamos la ruta con un ID único para seguimiento
            paths.append({'id': i, 'pts': pts})
            paths.append({'id': f"{i}_inv", 'pts': pts[::-1]})
    return paths

# --- SIMULACIÓN PRINCIPAL ---
def run_simulation(base_img_path, routes_img_path):
    base_img = cv2.imread(base_img_path)
    if base_img is None: return
    h, w = base_img.shape[:2]

    all_paths = get_ordered_paths(routes_img_path, (w, h))
    if not all_paths:
        print("No se detectaron rutas.")
        return

    # Creamos un ciclo infinito de las rutas disponibles para intercalarlas
    path_cycler = cycle(all_paths)
    
    agents = []
    colors = [(255, 100, 0), (0, 255, 100), (100, 100, 255), (0, 200, 255), (255, 0, 255)]
    
    last_spawn_time = time.time()
    spawn_delay = 0.3 # Aparición más rápida para ver todas funcionando pronto

    print(f"Rutas detectadas (incluyendo invertidas): {len(all_paths)}")
    print("Presiona 'q' para salir.")

    while True:
        frame_img = base_img.copy()
        current_time = time.time()

        # 1. APARECER NUEVOS AGENTES INTERCALADOS
        if current_time - last_spawn_time > spawn_delay:
            # En lugar de random, usamos el cycler para pasar a la siguiente ruta
            path_data = next(path_cycler)
            
            new_agent = CarAgent(
                path=path_data['pts'],
                color=random.choice(colors),
                speed=random.uniform(2, 5),
                path_id=path_data['id']
            )
            agents.append(new_agent)
            last_spawn_time = current_time

        # 2. ACTUALIZAR Y DIBUJAR
        agents = [a for a in agents if a.active]
        for agent in agents:
            agent.update(w, h)
            agent.draw(frame_img)

        # 3. INTERFAZ
        cv2.rectangle(frame_img, (10, 10), (250, 60), (255, 255, 255), -1)
        cv2.putText(frame_img, f"Agentes: {len(agents)}", (20, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        cv2.putText(frame_img, f"Rutas activas: {len(all_paths)}", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1)

        cv2.imshow('Simulador - Rutas Intercaladas', frame_img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

run_simulation('images/fondo.png', 'images/rutas/ruta1.png')