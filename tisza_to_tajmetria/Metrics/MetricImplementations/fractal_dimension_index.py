from abc import ABC
from tisza_to_tajmetria.Metrics.i_metric_calculator import IMetricsCalculator
from ..helper import check_interruption, reproject_layer_for_metrics
import numpy as np
import math


class FractalDimensionIndex(IMetricsCalculator, ABC):
    """Calculate Fractal Dimension Index (FDI) for raster patches"""
    name = "Fractal Dimension Index"

    @staticmethod
    def calculate_metric(layer):
        temp_layer = reproject_layer_for_metrics(layer)

        provider = temp_layer.dataProvider()
        nodata = provider.sourceNoDataValue(1)
        pixel_size_x = abs(temp_layer.rasterUnitsPerPixelX())
        pixel_size_y = abs(temp_layer.rasterUnitsPerPixelY())
        pixel_area = pixel_size_x * pixel_size_y

        extent = temp_layer.extent()
        width = temp_layer.width()
        height = temp_layer.height()

        block = provider.block(1, extent, width, height)

        stats = {}

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for row in range(height):
            if row % 16 == 0:
                check_interruption(yield_thread=True)
            for col in range(width):
                val = block.value(row, col)
                if val is None or np.isnan(val):
                    continue
                if nodata is not None and val == nodata:
                    continue
                if val == 0:
                    continue

                if val not in stats:
                    stats[val] = {"area": 0, "perimeter": 0.0}

                stats[val]["area"] += 1

                for dr, dc in directions:
                    r = row + dr
                    c = col + dc
                    if r < 0 or r >= height or c < 0 or c >= width:
                        stats[val]["perimeter"] += pixel_size_x if dr != 0 else pixel_size_y
                        continue

                    neighbor_val = block.value(r, c)
                    if nodata is not None and neighbor_val == nodata:
                        neighbor_val = None
                    if neighbor_val != val:
                        stats[val]["perimeter"] += pixel_size_x if dr != 0 else pixel_size_y

        fdi_values = []
        for class_val, data in stats.items():
            area = data["area"] * pixel_area
            perimeter = data["perimeter"]

            if area > 0 and perimeter > 0:
                fdi = (2 * math.log(perimeter)) / math.log(area)
                fdi_values.append(fdi)

        if len(fdi_values) == 0:
            return 0

        return np.mean(fdi_values)
