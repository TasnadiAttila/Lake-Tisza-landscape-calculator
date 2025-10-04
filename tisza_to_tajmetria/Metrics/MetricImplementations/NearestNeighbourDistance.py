from abc import ABC
from ..Helper import bfs_collect
from qgis.core import QgsCoordinateReferenceSystem
from tisza_to_tajmetria.Metrics.IMetricCalculator import IMetricsCalculator
import processing
import math

class NearestNeighbourDistance(IMetricsCalculator, ABC):
    name = "Nearest Neighbour Distance"

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

        geotransform = (extent.xMinimum(), extent.width() / width, 0,
                        extent.yMaximum(), 0, -extent.height() / height)

        visited = [[False for _ in range(width)] for _ in range(height)]
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),          (0, 1),
                      (1, -1),  (1, 0),  (1, 1)]

        context = {
            "block": block,
            "visited": visited,
            "height": height,
            "width": width,
            "directions": directions,
            "geotransform": geotransform
        }

        class_centroids = {}

        for row in range(height):
            for col in range(width):
                if visited[row][col]:
                    continue
                value = block.value(row, col)
                if value is None or value == 0:
                    continue
                centroid = bfs_collect(row, col, value, context)
                if value not in class_centroids:
                    class_centroids[value] = []
                class_centroids[value].append(centroid)

        nnd_result = {}
        for cls, centroids in class_centroids.items():
            distances = []
            for i, (x1, y1) in enumerate(centroids):
                min_dist = float("inf")
                for j, (x2, y2) in enumerate(centroids):
                    if i == j:
                        continue
                    d = math.hypot(x1 - x2, y1 - y2)
                    if d < min_dist:
                        min_dist = d
                if min_dist < float("inf"):
                    distances.append(min_dist)
            nnd_result[cls] = sum(distances) / len(distances) if distances else 0.0

        return nnd_result