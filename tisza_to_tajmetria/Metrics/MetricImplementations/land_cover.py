from abc import ABC
from tisza_to_tajmetria.Metrics.i_metric_calculator import IMetricsCalculator
from ..helper import check_interruption

class LandCover(IMetricsCalculator, ABC):
    """
    Calculate the percentage of each land cover class in the raster.
    """
    name = "Land Cover"

    @staticmethod
    def calculate_metric(layer):
        provider = layer.dataProvider()
        nodata = provider.sourceNoDataValue(1)

        extent = layer.extent()
        width = layer.width()
        height = layer.height()

        block = provider.block(1, extent, width, height)

        total_pixels = 0
        class_counts = {}

        for row in range(height):
            if row % 32 == 0:
                check_interruption(yield_thread=True)
            for col in range(width):
                val = block.value(row, col)
                if val is None:
                    continue
                if nodata is not None and val == nodata:
                    continue
                if val == 0:
                    continue
                total_pixels += 1
                if val not in class_counts:
                    class_counts[val] = 0
                class_counts[val] += 1

        if total_pixels == 0:
            return {}

        land_cover_percentages = {}
        for cls, count in class_counts.items():
            land_cover_percentages[cls] = (count / total_pixels) * 100

        return land_cover_percentages
