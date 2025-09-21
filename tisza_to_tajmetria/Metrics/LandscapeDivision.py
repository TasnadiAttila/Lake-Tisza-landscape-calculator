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

class LandscapeDivision(IMetricsCalculator, ABC):
    """Calculate the Landscape Division Index (LDI)"""
    name = "Landscape Division"

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

        # 1. Raster -> Polygon
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

        total_area = 0.0
        patch_areas = []

        for feature in polygon_layer.getFeatures():
            value = feature["VALUE"]

            if nodata is not None and value == nodata:
                continue
            if value <= 0:
                continue

            geom = feature.geometry()
            if geom and not geom.isEmpty():
                area = geom.area()  # m²
                patch_areas.append(area)
                total_area += area

        if total_area == 0:
            return 0.0

        sum_squared = sum((a / total_area) ** 2 for a in patch_areas)
        ldi = 1 - sum_squared

        return ldi
