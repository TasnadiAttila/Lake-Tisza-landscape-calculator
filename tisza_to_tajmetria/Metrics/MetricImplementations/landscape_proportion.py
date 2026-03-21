from abc import ABC
from tisza_to_tajmetria.Metrics.i_metric_calculator import IMetricsCalculator
from qgis.core import (
    QgsRasterLayer,
    QgsVectorLayer,
    QgsProcessingFeedback,
    QgsProcessingContext
)
from ..helper import check_interruption, reproject_layer_for_metrics
import processing

class LandscapeProportion(IMetricsCalculator, ABC):
    """Calculate the Landscape Proportion (LP).
    Unitless metric representing the proportion of the landscape occupied by patches (0-1)."""
    name = "Landscape Proportion"

    @staticmethod
    def calculate_metric(layer):
        if not isinstance(layer, QgsRasterLayer):
            raise TypeError("Input layer must be a raster layer")

        temp_layer = reproject_layer_for_metrics(layer)

        feedback = QgsProcessingFeedback()
        context = QgsProcessingContext()

        polygon_output = processing.run(
            "gdal:polygonize",
            {
                'INPUT': temp_layer,
                'BAND': 1,
                'FIELD': 'VALUE',
                'EIGHT_CONNECTEDNESS': True,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            },
            feedback=feedback,
            context=context
        )['OUTPUT']

        polygon_layer = QgsVectorLayer(polygon_output, "temp_polygons", "ogr")
        if not polygon_layer.isValid():
            raise RuntimeError("Polygonized layer is invalid")

        provider = temp_layer.dataProvider()
        nodata = provider.sourceNoDataValue(1)

        total_patch_area = 0.0
        for feature_index, feature in enumerate(polygon_layer.getFeatures()):
            if feature_index % 256 == 0:
                check_interruption(yield_thread=True)
            value = feature["VALUE"]

            if nodata is not None and value == nodata:
                continue
            if value <= 0:
                continue

            geom = feature.geometry()
            if geom and not geom.isEmpty():
                total_patch_area += geom.area()


        pixel_area = abs(temp_layer.rasterUnitsPerPixelX() * temp_layer.rasterUnitsPerPixelY())
        raster_total_area = temp_layer.width() * temp_layer.height() * pixel_area

        if raster_total_area == 0:
            return 0.0

        lp = total_patch_area / raster_total_area  # unitless

        return lp
