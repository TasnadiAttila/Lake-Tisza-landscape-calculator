from abc import ABC
from qgis.core import QgsCoordinateReferenceSystem, QgsVectorLayer
from tisza_to_tajmetria.Metrics.IMetricCalculator import IMetricsCalculator
import processing

class PatchCohesionIndex(IMetricsCalculator, ABC):
    name = "Patch Cohesion Index"

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

        for feature in vector_layer.getFeatures():
            cls = feature['class']
            geom = feature.geometry()
            area = geom.area()      # m²
            perimeter = geom.length()  # m

            if cls not in class_patches:
                class_patches[cls] = []
            class_patches[cls].append((area, perimeter))

        total_area = sum([p[0] for patches in class_patches.values() for p in patches])

        cohesion = {}
        for cls, patches in class_patches.items():
            sum_p = sum(p[1] for p in patches)
            sum_pa = sum(p[1] * (p[0] ** 0.5) for p in patches)

            if sum_pa == 0 or total_area == 0:
                cohesion[cls] = 0.0
            else:
                cohesion[cls] = (1 - (sum_p / sum_pa)) * (1 - (1 / (total_area ** 0.5))) * 100

        return cohesion
