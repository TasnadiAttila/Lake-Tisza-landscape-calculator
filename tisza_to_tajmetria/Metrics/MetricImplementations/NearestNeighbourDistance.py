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
        """Calculate average nearest neighbour distance (per class) in kilometers.

        For each land cover class a centroid is computed for every contiguous patch.
        The nearest neighbour (Euclidean) distance between patch centroids is
        computed in the layer's projected CRS (EPSG:32634 if original is geographic).
        Distances are converted from meters to kilometers before averaging.
        Returns: dict[class_value] -> mean_nearest_distance_km
        """
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
            distances_km = []
            for i, (x1, y1) in enumerate(centroids):
                min_dist_m = float("inf")
                for j, (x2, y2) in enumerate(centroids):
                    if i == j:
                        continue
                    d_m = math.hypot(x1 - x2, y1 - y2)  # meters in projected CRS
                    if d_m < min_dist_m:
                        min_dist_m = d_m
                if min_dist_m < float("inf"):
                    distances_km.append(min_dist_m / 1000.0)  # convert to km
            nnd_result[cls] = sum(distances_km) / len(distances_km) if distances_km else 0.0

        return nnd_result