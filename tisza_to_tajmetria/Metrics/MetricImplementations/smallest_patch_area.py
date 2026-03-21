from abc import ABC
from tisza_to_tajmetria.Metrics.i_metric_calculator import IMetricsCalculator
from ..helper import check_interruption, reproject_layer_for_metrics
import numpy as np
from scipy import ndimage

class SmallestPatchArea(IMetricsCalculator, ABC):
    """Calculate the smallest patch area per class in km² (ignores background)"""
    name = "Smallest Patch Area"

    @staticmethod
    def calculate_metric(layer):
        temp_layer = reproject_layer_for_metrics(layer)

        provider = temp_layer.dataProvider()
        nodata = provider.sourceNoDataValue(1)
        pixel_size_x = abs(temp_layer.rasterUnitsPerPixelX())
        pixel_size_y = abs(temp_layer.rasterUnitsPerPixelY())

        width = temp_layer.width()
        height = temp_layer.height()

        block = provider.block(1, temp_layer.extent(), width, height)
        raster_array = np.zeros((height, width), dtype=int)

        for row in range(height):
            if row % 32 == 0:
                check_interruption(yield_thread=True)
            for col in range(width):
                val = block.value(row, col)
                if val is None or val == 0 or (nodata is not None and val == nodata):
                    raster_array[row, col] = 0  # háttér
                else:
                    raster_array[row, col] = int(val)

        smallest_patches = {}

        for val in np.unique(raster_array):
            check_interruption(yield_thread=True)
            if val == 0:
                continue  # háttér teljes kizárása

            binary_mask = (raster_array == val).astype(int)
            labeled_array, num_features = ndimage.label(binary_mask, structure=np.ones((3, 3), dtype=int))

            patch_areas = []
            for i in range(1, num_features + 1):
                patch_size_pixels = np.sum(labeled_array == i)
                patch_size_area_km2 = (patch_size_pixels * pixel_size_x * pixel_size_y) / 1_000_000
                patch_areas.append(patch_size_area_km2)

            if patch_areas:
                smallest_patches[val] = min(patch_areas)

        return smallest_patches
