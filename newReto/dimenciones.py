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
        self.position = path[0]
        self.active = True
        self.path_id = path_id 

    def update(self, width, height):
        if not self.active: return

        # Avanzar según la velocidad
        self.current_step += self.speed
        idx = int(self.current_step)

        # 1. ELIMINACIÓN POR FINAL DE RUTA
        if idx >= len(self.path):
            self.active = False
            return

        self.position = self.path[idx]
        px, py = self.position

        # 2. ELIMINACIÓN POR CONTACTO CON EXTREMOS (Sin rebote)
        # Usamos un margen pequeño (3px) para detectar el borde de la imagen
        margin = 3
        if px <= margin or px >= width - margin or py <= margin or py >= height - margin:
            self.active = False
            return

    def draw(self, img):
        if not self.active: return
        pos = (int(self.position[0]), int(self.position[1]))
        
        # Dibujar vehículo
        # cv2.circle(img, pos, 6, self.color, -1)
        # cv2.circle(img, pos, 7, (0, 0, 0), 1)
        cv2.circle(img, pos, 13, self.color, -1)
        cv2.circle(img, pos, 14, (0, 0, 0), 1)
        
        # Mostrar ID de ruta
        cv2.putText(img, str(self.path_id), (pos[0]-5, pos[1]-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)

# --- PROCESAMIENTO DE RUTAS ---
def get_ordered_paths(routes_img_path, target_size):
    routes_img = cv2.imread(routes_img_path)
    if routes_img is None: return []
    routes_img = cv2.resize(routes_img, target_size)

    hsv = cv2.cvtColor(routes_img, cv2.COLOR_BGR2HSV)
    mask = cv2.bitwise_or(
        cv2.inRange(hsv, np.array([0, 120, 70]), np.array([10, 255, 255])),
        cv2.inRange(hsv, np.array([170, 120, 70]), np.array([180, 255, 255]))
    )

    # Adelgazamos la línea para que sea de 1px (evita que el agente "vuelva" por el otro borde de la línea)
    skeleton = cv2.ximgproc.thinning(mask, thinningType=cv2.ximgproc.THINNING_GUOHALL)
    contours, _ = cv2.findContours(skeleton, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    paths = []
    for i, cnt in enumerate(contours):
        pts = [tuple(p[0]) for p in cnt]
        # Solo agregamos si tiene longitud suficiente y NO agregamos versiones invertidas
        if len(pts) > 30: 
            paths.append({'id': i, 'pts': pts})
            
    return paths

# --- SIMULACIÓN ---
def run_simulation(base_img_path, routes_img_path):
    base_img = cv2.imread(base_img_path)
    if base_img is None: return
    h, w = base_img.shape[:2]

    all_paths = get_ordered_paths(routes_img_path, (w, h))
    if not all_paths:
        print("Error: No se detectaron rutas rojas.")
        return

    # Cycler para intercalar las rutas 0, 1, 2, 3, 4, 5...
    path_cycler = cycle(all_paths)
    agents = []
    
    last_spawn_time = time.time()
    spawn_delay = 0.5 

    while True:
        frame_img = base_img.copy()
        current_time = time.time()

        # Spawner intercalado
        if current_time - last_spawn_time > spawn_delay:
            p_data = next(path_cycler)
            new_agent = CarAgent(
                path=p_data['pts'],
                color=(random.randint(50,255), random.randint(50,255), random.randint(50,255)),
                speed=random.uniform(3, 5),
                path_id=p_data['id']
            )
            agents.append(new_agent)
            last_spawn_time = current_time

        # Actualizar y filtrar agentes
        agents = [a for a in agents if a.active]
        
        for agent in agents:
            agent.update(w, h)
            agent.draw(frame_img)

        cv2.imshow('Simulador Final - Sin Rebotes', frame_img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

run_simulation('images/fondo.png', 'images/rutas/ruta1.png')