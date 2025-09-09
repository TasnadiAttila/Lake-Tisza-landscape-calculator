from abc import ABC
from .IMetricsCalculator import IMetricsCalculator
import numpy as np

class Euclidean(IMetricsCalculator, ABC):
    """Calculate average Euclidean distance between patch centroids in raster"""
    name = "Euclidean Nearest Neighbour"

    @staticmethod
    def calculateMetric(layer):
        provider = layer.dataProvider()
        pixel_size_x = layer.rasterUnitsPerPixelX()
        pixel_size_y = layer.rasterUnitsPerPixelY()

        extent = layer.extent()
        width = layer.width()
        height = layer.height()

        stats = {}
        block = provider.block(1, extent, width, height)
        for row in range(height):
            for col in range(width):
                val = block.value(row, col)
                if val is None:
                    continue
                if val not in stats:
                    stats[val] = [[], []]  # x_coords, y_coords
                stats[val][0].append(col * pixel_size_x)
                stats[val][1].append(row * pixel_size_y)

        centroids = []
        for x_list, y_list in stats.values():
            if len(x_list) == 0:
                continue
            x_mean = np.mean(x_list)
            y_mean = np.mean(y_list)
            centroids.append((x_mean, y_mean))

        if len(centroids) < 2:
            return 0

        centroids = np.array(centroids)

        avg_distance = 0
        count = 0
        n = len(centroids)
        for i in range(n):
            for j in range(i+1, n):
                dx = centroids[i, 0] - centroids[j, 0]
                dy = centroids[i, 1] - centroids[j, 1]
                dist = np.sqrt(dx**2 + dy**2)
                avg_distance += dist
                count += 1

        return avg_distance / count
