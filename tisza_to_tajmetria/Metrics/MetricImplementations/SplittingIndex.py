from abc import ABC
from tisza_to_tajmetria.Metrics.IMetricCalculator import IMetricsCalculator
import numpy as np
from scipy import ndimage

class SplittingIndex(IMetricsCalculator, ABC):
    """Calculate Splitting Index per class"""
    name = "Splitting Index"

    @staticmethod
    def calculateMetric(layer):
        provider = layer.dataProvider()
        pixel_size_x = layer.rasterUnitsPerPixelX()
        pixel_size_y = layer.rasterUnitsPerPixelY()

        width = layer.width()
        height = layer.height()

        # Raszter beolvasása
        block = provider.block(1, layer.extent(), width, height)
        raster_array = np.zeros((height, width), dtype=int)

        for row in range(height):
            for col in range(width):
                val = block.value(row, col)
                if val is None or val == 0:
                    raster_array[row, col] = 0  # háttér
                else:
                    raster_array[row, col] = int(val)

        splitting_index = {}

        for val in np.unique(raster_array):
            if val == 0:
                continue  # háttér kizárása

            binary_mask = (raster_array == val).astype(int)
            labeled_array, num_features = ndimage.label(binary_mask)

            patch_areas = []
            for i in range(1, num_features + 1):
                patch_size_pixels = np.sum(labeled_array == i)
                patch_size_area_km2 = (patch_size_pixels * pixel_size_x * pixel_size_y) / 1_000_000
                patch_areas.append(patch_size_area_km2)

            if patch_areas:
                total_area = sum(patch_areas)
                SI = (total_area**2) / sum(a**2 for a in patch_areas)
                splitting_index[val] = SI

        return splitting_index
