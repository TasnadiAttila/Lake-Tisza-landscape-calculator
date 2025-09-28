from abc import ABC
from tisza_to_tajmetria.Metrics.IMetricCalculator import IMetricsCalculator
import numpy as np
import math


class FractalDimensionIndex(IMetricsCalculator, ABC):
    """Calculate Fractal Dimension Index (FDI) for raster patches"""
    name = "Fractal Dimension Index"

    @staticmethod
    def calculateMetric(layer):
        provider = layer.dataProvider()
        pixel_size_x = layer.rasterUnitsPerPixelX()
        pixel_size_y = layer.rasterUnitsPerPixelY()
        pixel_area = pixel_size_x * pixel_size_y

        extent = layer.extent()
        width = layer.width()
        height = layer.height()

        block = provider.block(1, extent, width, height)

        stats = {}

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for row in range(height):
            for col in range(width):
                val = block.value(row, col)
                if val is None or np.isnan(val):
                    continue

                if val not in stats:
                    stats[val] = {"area": 0, "perimeter": 0.0}

                stats[val]["area"] += 1

                for dr, dc in directions:
                    r = row + dr
                    c = col + dc
                    if r < 0 or r >= height or c < 0 or c >= width:
                        stats[val]["perimeter"] += pixel_size_x
                        continue

                    neighbor_val = block.value(r, c)
                    if neighbor_val != val:
                        stats[val]["perimeter"] += pixel_size_x

        fdi_values = []
        for class_val, data in stats.items():
            area = data["area"] * pixel_area
            perimeter = data["perimeter"]

            if area > 0 and perimeter > 0:
                fdi = (2 * math.log(0.25 * perimeter)) / math.log(area)
                fdi_values.append(fdi)

        if len(fdi_values) == 0:
            return 0

        return np.mean(fdi_values)
