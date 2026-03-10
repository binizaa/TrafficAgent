import mesa
from mesa import DataCollector
from mesa.space import SingleGrid
from mesa.visualization import SolaraViz, make_space_component, make_plot_component


# ---------- Agents ----------

class Tree(mesa.Agent):
    """Un árbol que puede estar vivo, ardiendo o muerto."""

    ALIVE = "alive"
    BURNING = "burning"
    DEAD = "dead"

    def __init__(self, model):
        super().__init__(model)
        self.state = self.ALIVE

    def step(self):
        if self.state == self.BURNING:
            # Propagar fuego a vecinos vivos
            neighbors = self.model.grid.get_neighbors(self.pos, moore=False, include_center=False)
            for neighbor in neighbors:
                if isinstance(neighbor, Tree) and neighbor.state == self.ALIVE:
                    neighbor.state = self.BURNING
            # El árbol en llamas muere
            self.state = self.DEAD


# ---------- Model ----------

class ForestModel(mesa.Model):
    """Modelo de incendio forestal."""

    def __init__(self, width=20, height=20, density=0.65, seed=None):
        super().__init__(seed=seed)
        self.width = width
        self.height = height
        self.density = density
        self.grid = SingleGrid(width, height, torus=False)

        self.datacollector = DataCollector(
            model_reporters={
                "Alive":   lambda m: sum(1 for a in m.agents if isinstance(a, Tree) and a.state == Tree.ALIVE),
                "Burning": lambda m: sum(1 for a in m.agents if isinstance(a, Tree) and a.state == Tree.BURNING),
                "Dead":    lambda m: sum(1 for a in m.agents if isinstance(a, Tree) and a.state == Tree.DEAD),
            }
        )

        # Poblar la grilla
        for contents, (x, y) in self.grid.coord_iter():
            if self.random.random() < self.density:
                tree = Tree(self)
                self.grid.place_agent(tree, (x, y))
                # Columna izquierda comienza ardiendo
                if x == 0:
                    tree.state = Tree.BURNING

        self.datacollector.collect(self)
        self.running = True

    def step(self):
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)
        # Parar si no hay árboles ardiendo
        if not any(a.state == Tree.BURNING for a in self.agents if isinstance(a, Tree)):
            self.running = False


# ---------- Visualization ----------

COLORS = {
    Tree.ALIVE:   "#228B22",   # verde
    Tree.BURNING: "#FF4500",   # rojo-naranja
    Tree.DEAD:    "#4A3728",   # marrón oscuro
}


def agent_portrayal(agent):
    if isinstance(agent, Tree):
        return {"color": COLORS[agent.state], "size": 25}
    return {}


model_params = {
    "width":   {"type": "SliderInt", "value": 20, "min": 5, "max": 50, "step": 5, "label": "Ancho"},
    "height":  {"type": "SliderInt", "value": 20, "min": 5, "max": 50, "step": 5, "label": "Alto"},
    "density": {"type": "SliderFloat", "value": 0.65, "min": 0.1, "max": 1.0, "step": 0.05, "label": "Densidad"},
}

SpaceView = make_space_component(agent_portrayal)
ChartView = make_plot_component(["Alive", "Burning", "Dead"])

model_instance = ForestModel()

page = SolaraViz(
    model_instance,
    components=[SpaceView, ChartView],
    model_params=model_params,
    name="Forest Fire Model",
)
page  # noqa: B018 – requerido por SolaraViz


if __name__ == "__main__":
    # Ejecución en consola (sin UI)
    model = ForestModel(width=20, height=20, density=0.65)
    for _ in range(30):
        if not model.running:
            break
        model.step()

    data = model.datacollector.get_model_vars_dataframe()
    print(data.tail(10))
    print(f"\nEstado final — Vivos: {data['Alive'].iloc[-1]}, "
          f"Ardiendo: {data['Burning'].iloc[-1]}, "
          f"Muertos: {data['Dead'].iloc[-1]}")
