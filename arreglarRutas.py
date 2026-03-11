"""
arreglarRutas.py
----------------
Lee rutas_cache.csv, encuentra puntos similares entre distintas rutas
(dentro de un radio UMBRAL) y los reemplaza por su promedio, de modo que
las rutas compartan exactamente el mismo punto en esas zonas comunes.

Uso:
    python arreglarRutas.py                # usa rutas_cache.csv por defecto
    python arreglarRutas.py mi_archivo.csv # CSV personalizado
    python arreglarRutas.py --umbral 60    # radio de similitud en píxeles originales
"""

import csv
import os
import sys
from collections import defaultdict


# ---------------------------------------------------------------------------
# Parámetros
# ---------------------------------------------------------------------------
UMBRAL_DEFAULT = 50   # radio en coordenadas originales del CSV
CSV_DEFAULT    = "rutas_cache.csv"


# ---------------------------------------------------------------------------
# Union-Find
# ---------------------------------------------------------------------------
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank   = [0] * n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path compression
            x = self.parent[x]
        return x

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------
def cargar_rutas(csv_path):
    rutas = []
    nombres = []
    with open(csv_path, newline="") as f:
        for row in csv.reader(f):
            nombres.append(row[0])
            pts = []
            for seg in row[1].split(";"):
                x, y = seg.split(",")
                pts.append([float(x), float(y)])
            rutas.append(pts)
    return nombres, rutas


def guardar_rutas(csv_path, nombres, rutas):
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        for nombre, ruta in zip(nombres, rutas):
            pts_str = ";".join(f"{p[0]:.4f},{p[1]:.4f}" for p in ruta)
            writer.writerow([nombre, pts_str])


# ---------------------------------------------------------------------------
# Algoritmo principal
# ---------------------------------------------------------------------------
def arreglar_rutas(rutas, umbral):
    """
    Dado un listado de rutas [[x,y], ...], agrupa los puntos de distintas
    rutas que están a menos de `umbral` píxeles y los reemplaza por su
    centroide, para que todas compartan el mismo punto en esa zona.

    Retorna las rutas modificadas (nuevas listas, no in-place).
    """

    # Índice plano: flat_idx  ->  (ruta_idx, punto_idx)
    flat   = []   # (ruta_idx, punto_idx, x, y)
    for ri, ruta in enumerate(rutas):
        for pi, (x, y) in enumerate(ruta):
            flat.append((ri, pi, x, y))

    n  = len(flat)
    uf = UnionFind(n)

    # Construir índice espacial simple por celda (grid hashing)
    celda = int(umbral)
    cuadricula: dict[tuple, list[int]] = defaultdict(list)
    for idx, (ri, pi, x, y) in enumerate(flat):
        cx, cy = int(x // celda), int(y // celda)
        cuadricula[(cx, cy)].append(idx)

    # Unir puntos cercanos de rutas distintas
    vecindad = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,0),(0,1),(1,-1),(1,0),(1,1)]
    for idx, (ri, pi, x, y) in enumerate(flat):
        cx, cy = int(x // celda), int(y // celda)
        for dcx, dcy in vecindad:
            for jdx in cuadricula.get((cx + dcx, cy + dcy), []):
                if jdx <= idx:
                    continue
                rj, _, xj, yj = flat[jdx]
                if ri == rj:
                    continue   # misma ruta → no mezclar
                dist2 = (x - xj) ** 2 + (y - yj) ** 2
                if dist2 < umbral ** 2:
                    uf.union(idx, jdx)

    # Agrupar por componente
    clusters: dict[int, list[int]] = defaultdict(list)
    for idx in range(n):
        clusters[uf.find(idx)].append(idx)

    # Calcular centroides y aplicar (solo para clusters multi-ruta)
    nuevas_rutas = [[list(pt) for pt in ruta] for ruta in rutas]
    puntos_modificados = 0

    for miembros in clusters.values():
        rutas_en_cluster = {flat[m][0] for m in miembros}
        if len(rutas_en_cluster) < 2:
            continue  # punto único en una sola ruta → no tocar

        cx = sum(flat[m][2] for m in miembros) / len(miembros)
        cy = sum(flat[m][3] for m in miembros) / len(miembros)

        for m in miembros:
            ri, pi, _, _ = flat[m]
            nuevas_rutas[ri][pi] = [cx, cy]
            puntos_modificados += 1

    print(f"  Puntos ajustados: {puntos_modificados} "
          f"(en {sum(1 for c in clusters.values() if len({flat[m][0] for m in c}) >= 2)} zonas comunes)")

    return nuevas_rutas


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    args    = sys.argv[1:]
    umbral  = UMBRAL_DEFAULT
    csv_in  = CSV_DEFAULT

    i = 0
    while i < len(args):
        if args[i] == "--umbral" and i + 1 < len(args):
            umbral = float(args[i + 1])
            i += 2
        else:
            csv_in = args[i]
            i += 1

    if not os.path.exists(csv_in):
        print(f"Error: no se encontró '{csv_in}'")
        sys.exit(1)

    # Backup automático
    backup = csv_in + ".bak"
    if not os.path.exists(backup):
        import shutil
        shutil.copy2(csv_in, backup)
        print(f"Backup guardado en: {backup}")

    print(f"Cargando rutas desde: {csv_in}  (umbral={umbral} px)")
    nombres, rutas = cargar_rutas(csv_in)
    total_pts = sum(len(r) for r in rutas)
    print(f"  Rutas: {len(rutas)}  |  Puntos totales: {total_pts}")

    rutas_nuevas = arreglar_rutas(rutas, umbral)

    guardar_rutas(csv_in, nombres, rutas_nuevas)
    print(f"Rutas guardadas en: {csv_in}")


if __name__ == "__main__":
    main()
