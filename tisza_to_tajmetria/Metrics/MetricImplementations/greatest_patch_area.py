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

class GreatestPatchArea(IMetricsCalculator, ABC):
    """Calculate the largest patch area by converting raster to polygons and measuring"""
    name = "Greatest Patch Area"

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

        max_area = 0.0
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
                area = geom.area()
                if area > max_area:
                    max_area = area


        return max_area / 1e6
