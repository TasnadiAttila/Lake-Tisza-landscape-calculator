from abc import ABC
from tisza_to_tajmetria.Metrics.i_metric_calculator import IMetricsCalculator
from ..helper import bfs, check_interruption, reproject_layer_for_metrics

class EffectiveMeshSize(IMetricsCalculator, ABC):
    """Calculate effective mesh size in square kilometers"""
    name = "Effective Mesh Size"

    @staticmethod
    def calculate_metric(layer):
        temp_layer = reproject_layer_for_metrics(layer)

        provider = temp_layer.dataProvider()
        extent = temp_layer.extent()
        width = temp_layer.width()
        height = temp_layer.height()
        block = provider.block(1, extent, width, height)

        pixel_width = extent.width() / width
        pixel_height = extent.height() / height
        pixel_area = abs(pixel_width * pixel_height)

        nodata = provider.sourceNoDataValue(1)
        visited = [[False for _ in range(width)] for _ in range(height)]
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

        patch_areas = []

        for row in range(height):
            if row % 32 == 0:
                check_interruption(yield_thread=True)
            for col in range(width):
                if visited[row][col]:
                    continue
                val = block.value(row, col)

                if val is None:
                    continue
                if nodata is not None and val == nodata:
                    continue
                if val == 0:
                    continue

                patch_pixel_count = bfs(row, col, val, context)
                if patch_pixel_count > 0:
                    patch_areas.append(patch_pixel_count * pixel_area)

        total_area = sum(patch_areas)
        if total_area == 0:
            return 0.0

        ems = sum(a ** 2 for a in patch_areas) / total_area

        return ems / 1_000_000