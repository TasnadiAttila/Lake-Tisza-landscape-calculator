from qgis.core import QgsProject
import xlsxwriter
import subprocess
import sys

class ComboBoxHandler:
    @staticmethod
    def add_clear_button_to_combobox(combobox):
        """Add clear button and search functionality to combobox"""
        combobox.setEditable(True)
        combobox.lineEdit().setClearButtonEnabled(True)
        combobox.lineEdit().setPlaceholderText("Search...")

    @staticmethod
    def load_layers_to_combobox(combobox, layer_types=None):
        """Load layers to combobox with optional type filtering"""
        if layer_types is None:
            layer_types = ['raster', 'vector']

        combobox.clear()
        layers = QgsProject.instance().mapLayers().values()
        filtered_layers = []

        for layer in layers:
            if ('raster' in layer_types and layer.type() == layer.RasterLayer) or \
               ('vector' in layer_types and layer.type() == layer.VectorLayer):
                filtered_layers.append(layer)

        for layer in filtered_layers:
            combobox.addItem(layer.name(), layer)

        if combobox.count() == 0:
            combobox.addItem("No available layers")

        return combobox

class ExcelHelper:
    def __init__(self):
        self.iface = None

    def ensure_xlsxwriter_installed(self):
        try:
            import xlsxwriter
        except ModuleNotFoundError:
            self.iface.messageBar().pushMessage(
                "Info",
                "xlsxwriter nincs telepítve, telepítés...",
                level=Qgis.Info,
                duration=5
            )
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "xlsxwriter"])
            import xlsxwriter

    def createOutputExcelFile(filePath):
        wb = xlsxwriter.Workbook(filePath)
        ws = wb.add_worksheet()
        wb.close()

class LandscapeMetricCalculator:

    @staticmethod
    def calculateEffectiveMeshSize(layer):
        """Calculate effective mesh size in square kilometers"""
        provider = layer.dataProvider()
        extent = layer.extent()
        pixel_size_x = layer.rasterUnitsPerPixelX()
        pixel_size_y = layer.rasterUnitsPerPixelY()
        pixel_area = abs(pixel_size_x * pixel_size_y)

        stats = {}
        block = provider.block(1, extent, layer.width(), layer.height())
        for row in range(layer.height()):
            for col in range(layer.width()):
                val = block.value(row, col)
                if val is not None:
                    stats[val] = stats.get(val, 0) + 1

        areas = [count * pixel_area for count in stats.values()]
        total_area = sum(areas)

        ems = sum([a ** 2 for a in areas]) / total_area

        return ems / 1_000_000