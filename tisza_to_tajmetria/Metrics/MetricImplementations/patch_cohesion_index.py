from abc import ABC
from qgis.core import QgsCoordinateReferenceSystem, QgsVectorLayer
from tisza_to_tajmetria.Metrics.i_metric_calculator import IMetricsCalculator
from ..helper import check_interruption
import processing
import math

class PatchCohesionIndex(IMetricsCalculator, ABC):
    name = "Patch Cohesion Index"

    @staticmethod
    def calculate_metric(layer):
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

        vector_result = processing.run(
            "gdal:polygonize",
            {
                'INPUT': temp_layer,
                'BAND': 1,
                'FIELD': 'class',
                'EIGHT_CONNECTEDNESS': True,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }
        )

        vector_path = vector_result['OUTPUT']
        vector_layer = QgsVectorLayer(vector_path, "patches", "ogr")

        if not vector_layer.isValid():
            raise ValueError("Polygonize failed: vector layer is not valid")

        class_patches = {}

        for feature_index, feature in enumerate(vector_layer.getFeatures()):
            if feature_index % 256 == 0:
                check_interruption(yield_thread=True)
            cls = feature['class']
            geom = feature.geometry()
            area = geom.area()      # m
            perimeter = geom.length()  # m

            if cls not in class_patches:
                class_patches[cls] = []
            class_patches[cls].append((area, perimeter))

        cohesion = {}
        for cls, patches in class_patches.items():
            
            
            sum_p = sum(p[1] for p in patches)
            sum_p_sqrt_a = sum(p[1] * math.sqrt(p[0]) for p in patches)
            
            if sum_p_sqrt_a == 0:
                cohesion[cls] = 0.0
            else:
                cohesion[cls] = max(0.0, (1 - (sum_p / sum_p_sqrt_a)) * 100)

        return cohesion
