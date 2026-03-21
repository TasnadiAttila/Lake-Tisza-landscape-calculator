from collections import deque
import time

from PyQt5.QtCore import QThread
from qgis.core import QgsCoordinateReferenceSystem
import processing


def check_interruption(yield_thread=False):
    thread = QThread.currentThread()
    if thread is not None and thread.isInterruptionRequested():
        raise InterruptedError("Calculation cancelled")
    if yield_thread:
        time.sleep(0)


def _utm_epsg_for_lon_lat(lon, lat):
    zone = int((lon + 180) // 6) + 1
    zone = max(1, min(zone, 60))
    return 32600 + zone if lat >= 0 else 32700 + zone


def reproject_layer_for_metrics(layer):
    """Return a projected layer in meters when input CRS is geographic."""
    if not layer.crs().isGeographic():
        return layer

    extent = layer.extent()
    lon = extent.center().x()
    lat = extent.center().y()
    target_epsg = _utm_epsg_for_lon_lat(lon, lat)
    projected_crs = QgsCoordinateReferenceSystem(f"EPSG:{target_epsg}")

    return processing.run(
        "gdal:warpreproject",
        {
            'INPUT': layer,
            'TARGET_CRS': projected_crs,
            'RESAMPLING': 0,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }
    )['OUTPUT']

def bfs(start_row, start_col, class_value, context):
    block = context["block"]
    visited = context["visited"]
    height = context["height"]
    width = context["width"]
    directions = context["directions"]

    queue = deque()
    queue.append((start_row, start_col))
    visited[start_row][start_col] = True
    patch_size = 0
    processed_cells = 0

    while queue:
        processed_cells += 1
        if processed_cells % 512 == 0:
            check_interruption(yield_thread=True)

        r, c = queue.popleft()
        patch_size += 1
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < height and 0 <= nc < width and not visited[nr][nc]:
                neighbor_value = block.value(nr, nc)
                if neighbor_value == class_value:
                    visited[nr][nc] = True
                    queue.append((nr, nc))

    return patch_size


def bfs_collect(start_row, start_col, class_value, context):
    block = context["block"]
    visited = context["visited"]
    height = context["height"]
    width = context["width"]
    directions = context["directions"]
    geotransform = context["geotransform"]

    queue = deque()
    queue.append((start_row, start_col))
    visited[start_row][start_col] = True
    pixels = []
    processed_cells = 0

    while queue:
        processed_cells += 1
        if processed_cells % 512 == 0:
            check_interruption(yield_thread=True)

        r, c = queue.popleft()
        x = geotransform[0] + (c + 0.5) * geotransform[1]
        y = geotransform[3] - (r + 0.5) * abs(geotransform[5])
        pixels.append((x, y))

        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < height and 0 <= nc < width and not visited[nr][nc]:
                neighbor_value = block.value(nr, nc)
                if neighbor_value == class_value:
                    visited[nr][nc] = True
                    queue.append((nr, nc))

    xs, ys = zip(*pixels)
    centroid = (sum(xs) / len(xs), sum(ys) / len(ys))
    return centroid
