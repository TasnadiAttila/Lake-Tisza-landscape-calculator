from abc import ABC
from .IMetricsCalculator import IMetricsCalculator
from qgis.core import (
    QgsRasterLayer,
    QgsVectorLayer,
    QgsProcessingFeedback,
    QgsProcessingContext
)
import processing
import os

class LandscapeProportion(IMetricsCalculator, ABC):
    """Calculate the Landscape Proportion (LP).
    Unitless metric representing the proportion of the landscape occupied by patches (0-1)."""
    name = "Landscape Proportion"

    @staticmethod
    def calculateMetric(layer):
        if not isinstance(layer, QgsRasterLayer):
            raise TypeError("Input layer must be a raster layer")

        feedback = QgsProcessingFeedback()
        context = QgsProcessingContext()

        temp_folder = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp")
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)
        polygon_output = os.path.join(temp_folder, "temp_raster_to_polygon.gpkg")

        processing.run(
            "gdal:polygonize",
            {
                'INPUT': layer.source(),
                'BAND': 1,
                'FIELD': 'VALUE',
                'EIGHT_CONNECTEDNESS': False,
                'OUTPUT': polygon_output
            },
            feedback=feedback,
            context=context
        )

        polygon_layer = QgsVectorLayer(polygon_output, "temp_polygons", "ogr")
        if not polygon_layer.isValid():
            raise RuntimeError("Polygonized layer is invalid")

        provider = layer.dataProvider()
        nodata = provider.sourceNoDataValue(1)

        total_patch_area = 0.0
        for feature in polygon_layer.getFeatures():
            value = feature["VALUE"]

            if nodata is not None and value == nodata:
                continue
            if value <= 0:
                continue

            geom = feature.geometry()
            if geom and not geom.isEmpty():
                total_patch_area += geom.area()


        pixel_area = layer.rasterUnitsPerPixelX() * layer.rasterUnitsPerPixelY()
        raster_total_area = layer.width() * layer.height() * pixel_area

        if raster_total_area == 0:
            return 0.0

        lp = total_patch_area / raster_total_area  # unitless

        return lp
