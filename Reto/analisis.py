"""
analisis.py — Simulación comparativa de los 3 modos durante 600 pasos
(equivalente a ~1 minuto a 10 pasos/segundo).

Genera 4 gráficas:
  1. Throughput acumulado por paso
  2. Autos activos en la intersección por paso
  3. Distribución de velocidad promedio de autos en movimiento
  4. Eficiencia: throughput final vs autos creados
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from config import DEFAULT_PARAMS
from model.traffic_model import TrafficModel

# ── Configuración ──────────────────────────────────────────────────────────────
STEPS      = 600          # 1 minuto a 10 fps
N_RUNS     = 3            # repeticiones por modo (para promediar ruido)
MODES      = {
    0: 'Sin heurística',
    1: 'Heurística básica',
    2: 'Heurística avanzada',
}
COLORS     = {0: '#E57373', 1: '#64B5F6', 2: '#81C784'}
ALPHA_BAND = 0.20         # transparencia de banda ±σ


def run_once(mode: int, steps: int) -> dict:
    """Ejecuta una simulación y devuelve series temporales."""
    params = dict(DEFAULT_PARAMS)
    params['mode']  = mode
    params['steps'] = steps

    sim = TrafficModel(params)
    sim.setup()

    throughput_series = []
    active_series     = []
    avg_speed_series  = []

    for _ in range(steps):
        sim.step()
        throughput_series.append(sim.throughput)
        active_series.append(len(sim.cars))

        moving = [c for c in sim.cars if c.is_moving]
        avg_v  = float(np.mean([c.v for c in moving])) if moving else 0.0
        avg_speed_series.append(avg_v)

    total_spawned = sum(sim.spawn_counts.values())
    return {
        'throughput': np.array(throughput_series),
        'active':     np.array(active_series),
        'avg_speed':  np.array(avg_speed_series),
        'spawned':    total_spawned,
        'final_thru': sim.throughput,
    }


def collect_runs(mode: int, steps: int, n: int) -> dict:
    """Corre n repeticiones y devuelve media ± desviación."""
    runs = [run_once(mode, steps) for _ in range(n)]
    result = {}
    for key in ('throughput', 'active', 'avg_speed'):
        stack = np.stack([r[key] for r in runs])
        result[f'{key}_mean'] = stack.mean(axis=0)
        result[f'{key}_std']  = stack.std(axis=0)
    result['spawned_mean'] = np.mean([r['spawned']    for r in runs])
    result['final_mean']   = np.mean([r['final_thru'] for r in runs])
    result['final_std']    = np.std( [r['final_thru'] for r in runs])
    return result


# ── Recolección de datos ───────────────────────────────────────────────────────
print(f"Ejecutando {N_RUNS} corridas × {len(MODES)} modos × {STEPS} pasos…")
data = {}
for mode_id, mode_name in MODES.items():
    print(f"  Modo {mode_id}: {mode_name}…", end=' ', flush=True)
    data[mode_id] = collect_runs(mode_id, STEPS, N_RUNS)
    print("listo")

t = np.arange(1, STEPS + 1)

# ── Gráficas ───────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(16, 10))
fig.suptitle(
    f'Comparativa de modos — {STEPS} pasos (~1 min)  |  {N_RUNS} corridas/modo',
    fontsize=14, fontweight='bold', y=0.98
)
gs = gridspec.GridSpec(2, 2, hspace=0.42, wspace=0.32)

# ── Gráfica 1: Throughput acumulado ───────────────────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
for mid, mname in MODES.items():
    d = data[mid]
    ax1.plot(t, d['throughput_mean'], color=COLORS[mid], label=mname, linewidth=2)
    ax1.fill_between(t,
        d['throughput_mean'] - d['throughput_std'],
        d['throughput_mean'] + d['throughput_std'],
        color=COLORS[mid], alpha=ALPHA_BAND)
ax1.set_title('Throughput acumulado (autos que salieron)')
ax1.set_xlabel('Paso')
ax1.set_ylabel('Autos completados')
ax1.legend(fontsize=9)
ax1.grid(alpha=0.3)

# ── Gráfica 2: Autos activos ──────────────────────────────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
for mid, mname in MODES.items():
    d = data[mid]
    ax2.plot(t, d['active_mean'], color=COLORS[mid], label=mname, linewidth=2)
    ax2.fill_between(t,
        d['active_mean'] - d['active_std'],
        d['active_mean'] + d['active_std'],
        color=COLORS[mid], alpha=ALPHA_BAND)
ax2.set_title('Autos activos en intersección')
ax2.set_xlabel('Paso')
ax2.set_ylabel('Autos en simulación')
ax2.legend(fontsize=9)
ax2.grid(alpha=0.3)

# ── Gráfica 3: Velocidad promedio de autos en movimiento ──────────────────────
ax3 = fig.add_subplot(gs[1, 0])
for mid, mname in MODES.items():
    d = data[mid]
    ax3.plot(t, d['avg_speed_mean'], color=COLORS[mid], label=mname, linewidth=2)
    ax3.fill_between(t,
        d['avg_speed_mean'] - d['avg_speed_std'],
        d['avg_speed_mean'] + d['avg_speed_std'],
        color=COLORS[mid], alpha=ALPHA_BAND)
ax3.set_title('Velocidad promedio (autos en movimiento)')
ax3.set_xlabel('Paso')
ax3.set_ylabel('Velocidad (u/paso)')
ax3.legend(fontsize=9)
ax3.grid(alpha=0.3)

# ── Gráfica 4: Eficiencia final ───────────────────────────────────────────────
ax4 = fig.add_subplot(gs[1, 1])
labels   = list(MODES.values())
spawned  = [data[m]['spawned_mean']  for m in MODES]
finished = [data[m]['final_mean']    for m in MODES]
errors   = [data[m]['final_std']     for m in MODES]
x = np.arange(len(labels))
w = 0.35
bars1 = ax4.bar(x - w/2, spawned,  w, label='Creados',     color='#B0BEC5', edgecolor='gray')
bars2 = ax4.bar(x + w/2, finished, w, label='Completados', color=[COLORS[m] for m in MODES],
                edgecolor='gray', yerr=errors, capsize=5)
ax4.set_title('Eficiencia final: creados vs completados')
ax4.set_xticks(x); ax4.set_xticklabels(labels, fontsize=9)
ax4.set_ylabel('Autos')
ax4.legend(fontsize=9)
ax4.grid(axis='y', alpha=0.3)

# Etiquetas de eficiencia (%)
for i, (sp, fi) in enumerate(zip(spawned, finished)):
    pct = fi / sp * 100 if sp > 0 else 0
    ax4.text(i + w/2, fi + max(errors) * 0.5, f'{pct:.0f}%',
             ha='center', va='bottom', fontsize=9, fontweight='bold')

# ── Tabla resumen en consola ───────────────────────────────────────────────────
print('\n' + '─' * 58)
print(f"{'Modo':<22} {'Creados':>8} {'Salieron':>10} {'Efic.':>7} {'V̄ final':>9}")
print('─' * 58)
for mid, mname in MODES.items():
    d    = data[mid]
    sp   = d['spawned_mean']
    fi   = d['final_mean']
    pct  = fi / sp * 100 if sp > 0 else 0
    vfin = d['avg_speed_mean'][-10:].mean()   # promedio últimos 10 pasos
    print(f"{mname:<22} {sp:>8.1f} {fi:>10.1f} {pct:>6.1f}% {vfin:>8.2f}")
print('─' * 58)

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resultados_simulacion.png')
fig.savefig(out_path, dpi=150, bbox_inches='tight')
print(f'\nGráfica guardada en: {out_path}')
plt.show()
