from abc import ABC
from ..Helper import bfs
from qgis.core import QgsCoordinateReferenceSystem, QgsProject
from tisza_to_tajmetria.Metrics.IMetricCalculator import IMetricsCalculator
import processing
import statistics

class MedianPatchArea(IMetricsCalculator, ABC):
    name = "Median Patch Area"

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

        pixel_width = extent.width() / width
        pixel_height = extent.height() / height
        pixel_area = pixel_width * pixel_height

        visited = [[False for _ in range(width)] for _ in range(height)]
        class_patch_areas = {}
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),          (0, 1),
                      (1, -1),  (1, 0),  (1, 1)]

        context = {
            "block": block,
            "visited": visited,
            "height": height,
            "width": width,
            "directions": directions
        }

        for row in range(height):
            for col in range(width):
                if visited[row][col]:
                    continue
                value = block.value(row, col)
                if value is None or value == 0:
                    continue
                patch_pixel_count = bfs(row, col, value, context)
                area = (patch_pixel_count * pixel_area) / 1e6
                if value not in class_patch_areas:
                    class_patch_areas[value] = []
                class_patch_areas[value].append(area)

        median_patch_area = {}
        for cls, areas in class_patch_areas.items():
            if areas:
                median_patch_area[cls] = statistics.median(areas)
            else:
                median_patch_area[cls] = 0.0

        return median_patch_area
