import os
import csv


def load_and_scale_paths(filename, scale_factor):
    if not os.path.exists(filename):
        return None
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
