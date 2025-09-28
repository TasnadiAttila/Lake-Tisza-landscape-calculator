from abc import ABC
from collections import deque
from math import cos, pi
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, QgsRasterLayer, QgsRectangle, QgsRaster
from tisza_to_tajmetria.Metrics.IMetricCalculator import IMetricsCalculator
import processing

class MeanPatchArea(IMetricsCalculator, ABC):
    name = "Mean Patch Area"

    @staticmethod
    def calculateMetric(layer):
        temp_layer = layer

        if layer.crs().isGeographic():
            projected_crs = QgsCoordinateReferenceSystem("EPSG:32634")  # UTM vagy EOV
            temp_layer = processing.run(
                "gdal:warpreproject",
                {
                    'INPUT': layer,
                    'TARGET_CRS': projected_crs,
                    'RESAMPLING': 0,
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                }
            )['OUTPUT']

        provider = temp_layer.dataProvider()
        extent = temp_layer.extent()
        width = temp_layer.width()
        height = temp_layer.height()
        block = provider.block(1, extent, width, height)

        pixel_width = extent.width() / width
        pixel_height = extent.height() / height
        pixel_area = pixel_width * pixel_height

        visited = [[False for _ in range(width)] for _ in range(height)]
        class_patch_areas = {}
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),          (0, 1),
                      (1, -1),  (1, 0),  (1, 1)]

        def bfs(start_row, start_col, class_value):
            queue = deque()
            queue.append((start_row, start_col))
            visited[start_row][start_col] = True
            patch_size = 0
            while queue:
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

        for row in range(height):
            for col in range(width):
                if visited[row][col]:
                    continue
                value = block.value(row, col)
                if value is None or value == 0:
                    continue
                patch_pixel_count = bfs(row, col, value)
                area = (patch_pixel_count * pixel_area) / 1e6  # km²-be
                if value not in class_patch_areas:
                    class_patch_areas[value] = []
                class_patch_areas[value].append(area)

        mean_patch_area = {}
        for cls, areas in class_patch_areas.items():
            mean_patch_area[cls] = sum(areas) / len(areas) if areas else 0.0

        return mean_patch_area
