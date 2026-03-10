"""
Simulación de tráfico en una intersección en cruz con carriles separados.

Diseño:
  - Calle horizontal tiene 2 carriles:
      · fila (cy-1): coches de izquierda → derecha  (RIGHT)
      · fila (cy+1): coches de derecha  → izquierda (LEFT)
  - Calle vertical tiene 2 carriles:
      · col (cx-1): coches de abajo → arriba (UP)
      · col (cx+1): coches de arriba → abajo (DOWN)
  - Zona de cruce: filas cy-1..cy+1, cols cx-1..cx+1
  - Semáforo en el centro (cx, cy).
"""

import mesa
from mesa import DataCollector
from mesa.space import MultiGrid
from mesa.visualization import SolaraViz, make_space_component, make_plot_component

# ──────────────────────────────────────────────
#  Constantes
# ──────────────────────────────────────────────
RIGHT = ( 1,  0)
LEFT  = (-1,  0)
UP    = ( 0,  1)
DOWN  = ( 0, -1)

AXIS_H = "horizontal"
AXIS_V = "vertical"


# ──────────────────────────────────────────────
#  Semáforo
# ──────────────────────────────────────────────
class TrafficLight(mesa.Agent):
    def __init__(self, model, green_ticks=5):
        super().__init__(model)
        self.green_axis = AXIS_H
        self.green_ticks = green_ticks
        self._counter = 0

    @property
    def green_h(self):
        return self.green_axis == AXIS_H

    @property
    def green_v(self):
        return self.green_axis == AXIS_V

    def step(self):
        self._counter += 1
        if self._counter >= self.green_ticks:
            self._counter = 0
            self.green_axis = AXIS_V if self.green_axis == AXIS_H else AXIS_H


# ──────────────────────────────────────────────
#  Coche
# ──────────────────────────────────────────────
class Car(mesa.Agent):
    def __init__(self, model, direction):
        super().__init__(model)
        self.direction = direction
        self.axis = AXIS_H if direction[1] == 0 else AXIS_V
        self.waiting = False

    def step(self):
        x, y = self.pos
        dx, dy = self.direction
        nx, ny = x + dx, y + dy
        w, h = self.model.grid.width, self.model.grid.height

        # Salió → eliminar
        if not (0 <= nx < w and 0 <= ny < h):
            self.model.grid.remove_agent(self)
            self.remove()
            self.model.cars_passed += 1
            return

        # ¿La celda siguiente está dentro de la zona de cruce?
        in_intersection = self.model.in_intersection(nx, ny)

        light = self.model.traffic_light
        if in_intersection:
            if self.axis == AXIS_H and not light.green_h:
                self.waiting = True
                return
            if self.axis == AXIS_V and not light.green_v:
                self.waiting = True
                return

        self.waiting = False

        # Colisión con otro coche
        cell = self.model.grid.get_cell_list_contents([(nx, ny)])
        if any(isinstance(a, Car) for a in cell):
            self.waiting = True
            return

        self.model.grid.move_agent(self, (nx, ny))


# ──────────────────────────────────────────────
#  Modelo
# ──────────────────────────────────────────────
class IntersectionModel(mesa.Model):
    def __init__(self, size=17, green_ticks=6, num_cars=8, spawn_rate=0.3, seed=None):
        super().__init__(seed=seed)
        self.size = size
        self.spawn_rate = spawn_rate
        self.cars_passed = 0

        cx, cy = size // 2, size // 2
        self.cx = cx
        self.cy = cy

        # Zona de cruce (3 × 3 celdas en el centro)
        self.intersection_xs = range(cx - 1, cx + 2)
        self.intersection_ys = range(cy - 1, cy + 2)

        # Carriles por dirección
        self.lane = {
            RIGHT: cy - 1,   # y fijo, avanza en x
            LEFT:  cy + 1,
            UP:    cx - 1,   # x fijo, avanza en y
            DOWN:  cx + 1,
        }

        self.grid = MultiGrid(size, size, torus=False)

        self.traffic_light = TrafficLight(self, green_ticks=green_ticks)
        self.grid.place_agent(self.traffic_light, (cx, cy))

        self.datacollector = DataCollector(
            model_reporters={
                "Esperando":  lambda m: sum(1 for a in m.agents if isinstance(a, Car) and a.waiting),
                "Circulando": lambda m: sum(1 for a in m.agents if isinstance(a, Car) and not a.waiting),
                "Cruzaron":   lambda m: m.cars_passed,
            }
        )
        self.datacollector.collect(self)

        # Colocar coches iniciales distribuidos entre las 4 direcciones
        directions = [RIGHT, LEFT, UP, DOWN]
        for i in range(num_cars):
            direction = directions[i % 4]
            self._place_car_in_lane(direction)

    def _place_car_in_lane(self, direction):
        """Coloca un coche en la posición libre más cercana a la entrada de su carril."""
        s = self.size
        cx, cy = self.cx, self.cy

        if direction == RIGHT:
            cells = [(x, self.lane[RIGHT]) for x in range(0, cx - 1)]
        elif direction == LEFT:
            cells = [(x, self.lane[LEFT]) for x in range(s - 1, cx + 1, -1)]
        elif direction == UP:
            cells = [(self.lane[UP], y) for y in range(0, cy - 1)]
        else:  # DOWN
            cells = [(self.lane[DOWN], y) for y in range(s - 1, cy + 1, -1)]

        for pos in cells:
            cell = self.grid.get_cell_list_contents([pos])
            if not any(isinstance(a, Car) for a in cell):
                car = Car(self, direction)
                self.grid.place_agent(car, pos)
                return

    def in_intersection(self, x, y):
        return x in self.intersection_xs and y in self.intersection_ys

    def _spawn_cars(self):
        s = self.size
        spawn_points = [
            ((0,   self.lane[RIGHT]), RIGHT),
            ((s-1, self.lane[LEFT]),  LEFT),
            ((self.lane[UP],   0),    UP),
            ((self.lane[DOWN], s-1),  DOWN),
        ]
        for pos, direction in spawn_points:
            if self.random.random() < self.spawn_rate:
                cell = self.grid.get_cell_list_contents([pos])
                if not any(isinstance(a, Car) for a in cell):
                    car = Car(self, direction)
                    self.grid.place_agent(car, pos)

    def step(self):
        self._spawn_cars()
        self.traffic_light.step()

        # Mover primero los coches más lejos del centro (los que ya salieron del cruce)
        # para despejar el espacio antes de que entren los de atrás.
        cars = [a for a in list(self.agents) if isinstance(a, Car)]
        cx, cy = self.cx, self.cy

        def dist(car):
            x, y = car.pos
            return abs(x - cx) + abs(y - cy)

        for car in sorted(cars, key=dist, reverse=True):
            if car in self.agents:
                car.step()

        self.datacollector.collect(self)


# ──────────────────────────────────────────────
#  Helpers visuales
# ──────────────────────────────────────────────
CAR_COLORS = {
    RIGHT: "#E63946",
    LEFT:  "#457B9D",
    UP:    "#2A9D8F",
    DOWN:  "#E9C46A",
}


def agent_portrayal(agent):
    if isinstance(agent, TrafficLight):
        color = "#00CC44" if agent.green_h else "#FF3333"
        return {"color": color, "size": 50, "shape": "rect"}

    if isinstance(agent, Car):
        color = "#BBBBBB" if agent.waiting else CAR_COLORS.get(agent.direction, "#FFF")
        return {"color": color, "size": 20, "shape": "circle"}

    return {}


# ──────────────────────────────────────────────
#  SolaraViz
# ──────────────────────────────────────────────
model_params = {
    "size":        {"type": "SliderInt",   "value": 17,   "min": 11,  "max": 29,  "step": 2,    "label": "Tamaño grilla"},
    "green_ticks": {"type": "SliderInt",   "value": 6,    "min": 2,   "max": 20,  "step": 1,    "label": "Duración semáforo (pasos)"},
    "num_cars":    {"type": "SliderInt",   "value": 8,    "min": 0,   "max": 40,  "step": 1,    "label": "Cantidad inicial de coches"},
    "spawn_rate":  {"type": "SliderFloat", "value": 0.3,  "min": 0.0, "max": 0.8, "step": 0.05, "label": "Tasa de aparición continua"},
}

SpaceView = make_space_component(agent_portrayal)
ChartView = make_plot_component(["Esperando", "Circulando", "Cruzaron"])

model_instance = IntersectionModel()

page = SolaraViz(
    model_instance,
    components=[SpaceView, ChartView],
    model_params=model_params,
    name="Tráfico — Intersección en Cruz",
)
page  # noqa: B018


# ──────────────────────────────────────────────
#  Animación matplotlib
# ──────────────────────────────────────────────
def run_animation(size=17, green_ticks=6, num_cars=8, spawn_rate=0.3, steps=200, interval=200):
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.animation import FuncAnimation
    model = IntersectionModel(size=size, green_ticks=green_ticks,
                              num_cars=num_cars, spawn_rate=spawn_rate)

    cx, cy = model.cx, model.cy
    S = size

    # Escala: cada celda = 1 unidad. Rango del eje: [0, S]
    CELL = 1.0
    CAR_W, CAR_H = 0.55, 0.80  # tamaño del "coche"

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_xlim(0, S)
    ax.set_ylim(0, S)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("#4a7c59")   # fondo verde (pasto)

    # ── Fondo de calles (estático) ─────────────
    # Calle horizontal (filas cy-1, cy, cy+1)
    h_road = mpatches.Rectangle(
        (0, cy - 1), S, 3, color="#555555", zorder=1
    )
    # Calle vertical (cols cx-1, cx, cx+1)
    v_road = mpatches.Rectangle(
        (cx - 1, 0), 3, S, color="#555555", zorder=1
    )
    ax.add_patch(h_road)
    ax.add_patch(v_road)

    # Líneas de carril discontinuas (blancas)
    dash_kw = dict(color="white", linewidth=1, linestyle="--", zorder=2, alpha=0.6)
    # Centro horizontal
    for x0 in range(0, S, 2):
        if not (cx - 1 <= x0 <= cx + 1):   # saltar intersección
            ax.plot([x0, x0 + 1], [cy, cy], **dash_kw)
    # Centro vertical
    for y0 in range(0, S, 2):
        if not (cy - 1 <= y0 <= cy + 1):
            ax.plot([cx, cx], [y0, y0 + 1], **dash_kw)

    # Líneas de parada (rojas) justo antes del cruce
    stop_kw = dict(color="#FF4444", linewidth=2, zorder=3)
    ax.plot([cx - 1, cx - 1], [cy - 1, cy + 2], **stop_kw)   # entrada RIGHT
    ax.plot([cx + 2, cx + 2], [cy - 1, cy + 2], **stop_kw)   # entrada LEFT
    ax.plot([cx - 1, cx + 2], [cy - 1, cy - 1], **stop_kw)   # entrada UP
    ax.plot([cx - 1, cx + 2], [cy + 2, cy + 2], **stop_kw)   # entrada DOWN

    # ── Elementos dinámicos ────────────────────
    car_patches = {}      # agent_id → Rectangle
    arrow_patches = {}    # agent_id → FancyArrow

    ARROW_DIR = {
        RIGHT: ( 0.25, 0),
        LEFT:  (-0.25, 0),
        UP:    (0,  0.25),
        DOWN:  (0, -0.25),
    }
    CAR_COLOR_MAP = {
        RIGHT: "#E63946",
        LEFT:  "#457B9D",
        UP:    "#2A9D8F",
        DOWN:  "#E9C46A",
    }

    # Semáforo (círculo)
    light_circle = plt.Circle((cx + 0.5, cy + 0.5), 0.45,
                               color="#00CC44", zorder=6)
    ax.add_patch(light_circle)

    step_text = ax.text(0.5, 0.97, "", transform=ax.transAxes,
                        ha="center", va="top", color="white",
                        fontsize=10, fontweight="bold", zorder=10)

    def _car_xy(pos):
        """Esquina inferior-izquierda del rectángulo del coche centrado en la celda."""
        x, y = pos
        return x + (CELL - CAR_W) / 2, y + (CELL - CAR_H) / 2

    def update(_):  # noqa: ANN001
        model.step()

        # Actualizar semáforo
        light_circle.set_color("#00CC44" if model.traffic_light.green_h else "#FF3333")

        current_cars = {a.unique_id: a
                        for a in model.agents if isinstance(a, Car)}

        # Eliminar parches de coches que ya no existen
        for uid in list(car_patches):
            if uid not in current_cars:
                car_patches.pop(uid).remove()
                arrow_patches.pop(uid).remove()

        # Agregar o mover coches
        for uid, car in current_cars.items():
            bx, by = _car_xy(car.pos)
            color = "#AAAAAA" if car.waiting else CAR_COLOR_MAP[car.direction]

            if uid not in car_patches:
                rect = mpatches.FancyBboxPatch(
                    (bx, by), CAR_W, CAR_H,
                    boxstyle="round,pad=0.05",
                    facecolor=color, edgecolor="black", linewidth=0.5, zorder=5
                )
                ax.add_patch(rect)
                car_patches[uid] = rect

                dx, dy = ARROW_DIR[car.direction]
                arr = ax.annotate(
                    "", xy=(bx + CAR_W/2 + dx, by + CAR_H/2 + dy),
                    xytext=(bx + CAR_W/2, by + CAR_H/2),
                    arrowprops=dict(arrowstyle="->", color="white", lw=1.2),
                    zorder=6
                )
                arrow_patches[uid] = arr
            else:
                car_patches[uid].set_xy((bx, by))
                car_patches[uid].set_facecolor(color)

                dx, dy = ARROW_DIR[car.direction]
                arr = arrow_patches[uid]
                arr.xy    = (bx + CAR_W/2 + dx, by + CAR_H/2 + dy)
                arr.xyann = (bx + CAR_W/2,       by + CAR_H/2)

        data = model.datacollector.get_model_vars_dataframe()
        last = data.iloc[-1]
        step_text.set_text(
            f"Paso {model.steps}  |  "
            f"Esperando: {int(last['Esperando'])}  "
            f"Circulando: {int(last['Circulando'])}  "
            f"Cruzaron: {int(last['Cruzaron'])}"
        )

        return list(car_patches.values()) + [light_circle, step_text]

    ani = FuncAnimation(fig, update, frames=steps,
                        interval=interval, blit=False, repeat=False)
    plt.tight_layout()
    plt.show()
    return ani


# ──────────────────────────────────────────────
#  Punto de entrada
# ──────────────────────────────────────────────
if __name__ == "__main__":
    run_animation(size=17, green_ticks=6, num_cars=8, spawn_rate=0.3,
                  steps=300, interval=180)
