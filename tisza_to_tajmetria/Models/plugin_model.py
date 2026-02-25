# -*- coding: utf-8 -*-

from qgis.core import QgsColorRampShader


class PluginModel:
    UNIT_MAPPING = {
        "Effective Mesh Size": "km²",
        "Euclidean Distance": "km",
        "Fractal Dimension Index": "Index (1-2)",
        "Greatest Patch Area": "km²",
        "Landscape Division": "Index (0-1)",
        "Landscape Proportion": "Index (0-1)",
        "Land Cover": "%",
        "Total Landscape Area": "km²",
        "Mean Patch Area": "km²",
        "Median Patch Area": "km²",
        "Nearest Neighbour Distance": "km",
        "Number of Patches": "patches",
        "Patch Cohesion Index": "Index (0-100)",
        "Patch Density": "patches/km²",
        "Smallest Patch Area": "km²",
        "Splitting Index": "Index (>=1)",
    }

    EXPORT_HEADERS = [
        "Layer Name",
        "Metric Name",
        "Statistic Detail",
        "Value",
        "Unit",
        "Class ID",
        "Class Name",
    ]

    def __init__(self):
        self.last_calculation_data = None
        self.last_metric_data = None

    def set_calculation_results(self, data_to_write, metric_data):
        self.last_calculation_data = data_to_write
        self.last_metric_data = metric_data

    def has_calculation_results(self):
        return self.last_calculation_data is not None and self.last_metric_data is not None

    @staticmethod
    def get_land_cover_mapping_from_layer(layer):
        renderer = layer.renderer()
        mapping = {}

        if renderer.type() == 'paletted':
            classes = renderer.classes()
            for cls in classes:
                mapping[float(cls.value)] = cls.label

        elif renderer.type() == 'singlebandpseudocolor':
            shader = renderer.shader()
            if shader:
                color_ramp_shader = shader.rasterShaderFunction()
                if isinstance(color_ramp_shader, QgsColorRampShader):
                    for item in color_ramp_shader.colorRampItemList():
                        mapping[float(item.value)] = item.label

        elif renderer.type() == 'singlebandgray':
            mapping['min'] = layer.dataProvider().bandStatistics(1).minimumValue
            mapping['max'] = layer.dataProvider().bandStatistics(1).maximumValue

        elif renderer.type() == 'multibandcolor':
            mapping['Red band'] = renderer.redBand()
            mapping['Green band'] = renderer.greenBand()
            mapping['Blue band'] = renderer.blueBand()

        elif renderer.type() == 'hillshade':
            mapping['Band'] = renderer.band()
            mapping['Z factor'] = renderer.zFactor()
            mapping['Azimuth'] = renderer.azimuth()
            mapping['Altitude'] = renderer.altitude()

        return mapping
