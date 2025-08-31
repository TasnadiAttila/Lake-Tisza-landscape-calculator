from abc import ABC
from .IMetricsCalculator import IMetricsCalculator

class EffectiveMeshSize(IMetricsCalculator, ABC):
    """Calculate effective mesh size in square kilometers"""
    name = "Effective Mesh Size"

    @staticmethod
    def calculateMetric(layer):
        provider = layer.dataProvider()
        extent = layer.extent()
        pixel_size_x = layer.rasterUnitsPerPixelX()
        pixel_size_y = layer.rasterUnitsPerPixelY()
        pixel_area = abs(pixel_size_x * pixel_size_y)

        stats = {}
        block = provider.block(1, extent, layer.width(), layer.height())
        for row in range(layer.height()):
            for col in range(layer.width()):
                val = block.value(row, col)
                if val is not None:
                    stats[val] = stats.get(val, 0) + 1

        areas = [count * pixel_area for count in stats.values()]
        total_area = sum(areas)

        ems = sum([a ** 2 for a in areas]) / total_area

        return ems / 1_000_000