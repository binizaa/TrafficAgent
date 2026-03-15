class TrafficLight:
    VERDE    = "verde"
    AMARILLO = "amarillo"
    ROJO     = "rojo"

    COLOR_RGB = {
        VERDE:    (30, 210, 30),
        AMARILLO: (240, 200, 0),
        ROJO:     (210, 30, 30),
    }

    def __init__(self, pos, direccion, grupo):
        self.pos       = pos         # (x, y) ya escalado
        self.direccion = direccion   # "N", "S", "E", "O"
        self.grupo     = grupo       # 0 = N/S, 1 = E/O
        self.state     = self.VERDE if grupo == 0 else self.ROJO
