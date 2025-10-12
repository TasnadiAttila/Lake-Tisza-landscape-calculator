from abc import ABC
from tisza_to_tajmetria.Metrics.IMetricCalculator import IMetricsCalculator
import numpy as np
from scipy import ndimage

class PatchDensity(IMetricsCalculator, ABC):
    """Calculate detailed Patch Density Index"""
    name = "Detailed Patch Density Index"

    @staticmethod
    def calculateMetric(layer):
        provider = layer.dataProvider()
        pixel_size_x = layer.rasterUnitsPerPixelX()
        pixel_size_y = layer.rasterUnitsPerPixelY()

        extent = layer.extent()
        width = layer.width()
        height = layer.height()

        # Olvassuk be a rasztert
        block = provider.block(1, extent, width, height)
        raster_array = np.zeros((height, width), dtype=int)

        for row in range(height):
            for col in range(width):
                val = block.value(row, col)
                if val is None:
                    raster_array[row, col] = 0  # háttér
                else:
                    raster_array[row, col] = int(val) + 1  # +1 hogy a háttér 0 maradjon

        patch_stats = {}
        total_patches = 0

        for val in np.unique(raster_array):
            if val == 0:
                continue  # ne számoljuk a háttér patch-et

            binary_mask = (raster_array == val).astype(int)
            labeled_array, num_features = ndimage.label(binary_mask)
            total_patches += num_features

            patch_areas = []
            for i in range(1, num_features + 1):
                patch_size_pixels = np.sum(labeled_array == i)
                patch_size_area = patch_size_pixels * pixel_size_x * pixel_size_y
                patch_areas.append(patch_size_area)

            # Csak a patch-ek számát és területeket tároljuk, mean_patch_area nélkül
            patch_stats[val-1] = {
                "num_patches": num_features,
                "patch_areas": patch_areas
            }

        total_area = width * pixel_size_x * height * pixel_size_y
        patch_density = total_patches / total_area if total_area != 0 else 0

        return {
            "patch_density": patch_density,
            "total_patches": total_patches,
            "total_area": total_area,
            "patch_stats": patch_stats
        }
