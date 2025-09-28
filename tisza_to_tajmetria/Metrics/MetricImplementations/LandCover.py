from abc import ABC
from tisza_to_tajmetria.Metrics.IMetricCalculator import IMetricsCalculator
import numpy as np

class LandCover(IMetricsCalculator, ABC):
    """
    Calculate the percentage of each land cover class in the raster.
    """
    name = "Land Cover Percentage"

    @staticmethod
    def calculateMetric(layer):
        provider = layer.dataProvider()

        extent = layer.extent()
        width = layer.width()
        height = layer.height()

        # Teljes raszter adat beolvasása
        block = provider.block(1, extent, width, height)

        total_pixels = 0
        class_counts = {}

        for row in range(height):
            for col in range(width):
                val = block.value(row, col)
                if val is None:
                    continue
                total_pixels += 1
                if val not in class_counts:
                    class_counts[val] = 0
                class_counts[val] += 1

        # Százalékok kiszámítása
        land_cover_percentages = {}
        for cls, count in class_counts.items():
            land_cover_percentages[cls] = (count / total_pixels) * 100

        return land_cover_percentages
