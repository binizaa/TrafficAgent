# Traffic Intersection Simulation

Simulacion de un cruce de 4 vias con semaforos y agentes vehiculares, disenada para comparar distintas estrategias de comportamiento de conductores mediante modelado basado en agentes.

## Descripcion

El proyecto modela una interseccion vial con 4 accesos (Norte, Sur, Este, Oeste), semaforos de 4 fases y hasta 16 rutas de entrada. Se pueden comparar tres modos de comportamiento vehicular:

| Modo | Nombre | Descripcion |
|------|--------|-------------|
| 0 | Sin heuristica | Los autos ignoran semaforos y distancia de seguridad |
| 1 | Heuristica basica | Respetan semaforos y mantienen distancia minima |
| 2 | Heuristica avanzada | Modo 1 + personalidad de conductor (velocidad variable, tiempo de reaccion, aceleracion realista) |

## Estructura del proyecto

```
Reto/
├── config.py              # Parametros globales y configuracion
├── main.py                # Punto de entrada (UI interactiva con pygame)
├── analisis.py            # Herramienta de analisis comparativo (genera graficas)
├── background.png         # Fondo prerenderizado del cruce
├── charts/                # Graficas generadas por analisis.py
├── model/
│   ├── traffic_model.py   # Motor de simulacion (TrafficModel)
│   ├── signals.py         # Controlador de semaforos (FourWaySignals)
│   ├── car.py             # Agente vehiculo con heuristicas
│   └── carWithout.py      # Agente vehiculo base (sin heuristicas)
└── views/
    ├── renderer.py        # Visualizacion 2D
    └── menu.py            # Menu interactivo de parametros
```

## Requisitos

- Python 3.10+
- [agentpy](https://agentpy.readthedocs.io/)
- [pygame](https://www.pygame.org/)
- numpy
- matplotlib

Instalar dependencias:

```bash
pip install agentpy pygame numpy matplotlib
```

## Uso

### Simulacion interactiva

```bash
python main.py
```

Abre una ventana con un menu para configurar:
- Tasas de llegada (lambda) por direccion
- Tiempos de semaforo (verde, amarillo, todo-rojo)
- Parametros de dinamica vehicular
- Modo de heuristica (0 / 1 / 2)

Controles durante la simulacion:
- `ESC` — volver al menu
- `UP / DOWN` — ajustar FPS (1–60)
- Botones Pause / Resume / Stop en pantalla

### Analisis comparativo

```bash
python analisis.py
```

Ejecuta 3 modos x 3 corridas x 600 pasos y genera una grafica de 4 paneles en `charts/` con:
1. Flujo acumulado de autos completados
2. Autos activos en la interseccion (longitud de cola)
3. Velocidad promedio de autos en movimiento
4. Eficiencia (porcentaje de autos creados que completaron la ruta)

## Parametros configurables (`config.py`)

| Parametro | Descripcion | Valor por defecto |
|-----------|-------------|-------------------|
| `STEPS` | Duracion de la simulacion | 150 |
| `green_ns` | Tiempo de verde Norte-Sur | 10 |
| `green_ew` | Tiempo de verde Este-Oeste | 10 |
| `yellow` | Tiempo de amarillo | 5 |
| `all_red` | Tiempo de todo-rojo | 6 |
| `lam_*` | Tasa de llegada por direccion (Poisson) | 0.4 |
| `v_free` | Velocidad libre | 7.0 |
| `headway` | Distancia minima entre autos | 8.0 |
| `mode` | Modo de heuristica activo | 0 |

## Modelo de agentes

- **TrafficModel**: Modelo principal que coordina semaforos y vehiculos.
- **FourWaySignals**: Controlador de semaforos con ciclo de 4 fases (NS → EW → Diagonal Y → Diagonal B).
- **Car**: Agente vehiculo con heuristicas. En modo avanzado cada conductor tiene velocidad, distancia de seguridad y tiempo de reaccion propios.
- **CarWithout**: Variante base usada en modo 0.
