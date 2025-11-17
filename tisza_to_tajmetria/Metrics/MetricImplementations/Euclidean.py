from abc import ABC
from qgis.core import QgsCoordinateReferenceSystem
from tisza_to_tajmetria.Metrics.IMetricCalculator import IMetricsCalculator
from ..Helper import bfs_collect
import processing
import math

class Euclidean(IMetricsCalculator, ABC):
    """Average pairwise Euclidean distance between patch centroids (km).

    Steps:
    - If the layer is geographic, reproject to EPSG:32634 (meters).
    - Identify contiguous patches per class and compute their centroids.
    - Compute all pairwise distances between patch centroids.
    - Return the mean distance in kilometers.
    """
    name = "Euclidean Distance"

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

        # Collect centroids for EACH contiguous patch across all classes
        patch_centroids = []
        for row in range(height):
            for col in range(width):
                if visited[row][col]:
                    continue
                val = block.value(row, col)
                if val is None or val == 0:
                    continue
                centroid = bfs_collect(row, col, val, context)
                patch_centroids.append(centroid)

        n = len(patch_centroids)
        if n < 2:
            return 0.0

        # Average pairwise distance in km
        total_km = 0.0
        pairs = 0
        for i in range(n):
            x1, y1 = patch_centroids[i]
            for j in range(i + 1, n):
                x2, y2 = patch_centroids[j]
                d_m = math.hypot(x1 - x2, y1 - y2)
                total_km += d_m / 1000.0
                pairs += 1

        return total_km / pairs if pairs else 0.0
