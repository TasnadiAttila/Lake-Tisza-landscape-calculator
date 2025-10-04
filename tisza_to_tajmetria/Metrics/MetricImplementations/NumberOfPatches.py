from abc import ABC
from collections import deque
from qgis.core import QgsCoordinateReferenceSystem
from tisza_to_tajmetria.Metrics.IMetricCalculator import IMetricsCalculator
import processing


class NumberOfPatches(IMetricsCalculator, ABC):
    name = "Number of Patches"

    @staticmethod
    def calculateMetric(layer):
        temp_layer = layer

        if layer.crs().isGeographic():
            projected_crs = QgsCoordinateReferenceSystem("EPSG:32634")
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

        visited = [[False for _ in range(width)] for _ in range(height)]
        class_patch_counts = {}
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),          (0, 1),
                      (1, -1),  (1, 0),  (1, 1)]

        def bfs(start_row, start_col, class_value):
            queue = deque()
            queue.append((start_row, start_col))
            visited[start_row][start_col] = True
            while queue:
                r, c = queue.popleft()
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < height and 0 <= nc < width and not visited[nr][nc]:
                        neighbor_value = block.value(nr, nc)
                        if neighbor_value == class_value:
                            visited[nr][nc] = True
                            queue.append((nr, nc))

        for row in range(height):
            for col in range(width):
                if visited[row][col]:
                    continue
                value = block.value(row, col)
                if value is None or value == 0:
                    continue
                bfs(row, col, value)
                if value not in class_patch_counts:
                    class_patch_counts[value] = 0
                class_patch_counts[value] += 1

        return class_patch_counts
