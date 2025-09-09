from qgis.core import QgsProject
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from tisza_to_tajmetria.Metrics.Metrics import Metrics


class ComboBoxHandler:

    @staticmethod
    def addClearButtonToCombobox(combobox):
        combobox.setEditable(True)
        combobox.lineEdit().setClearButtonEnabled(True)
        combobox.lineEdit().setPlaceholderText("Search...")

    @staticmethod
    def loadLayersToCombobox(combobox, layer_types=None):
        if layer_types is None:
            layer_types = ['raster', 'vector']

        combobox.clear()
        layers = QgsProject.instance().mapLayers().values()
        model = QStandardItemModel(combobox)

        for layer in layers:
            if ('raster' in layer_types and layer.type() == layer.RasterLayer) or \
                    ('vector' in layer_types and layer.type() == layer.VectorLayer):
                item = QStandardItem(layer.name())
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                item.setData(Qt.Unchecked, Qt.CheckStateRole)
                item.setData(layer, Qt.UserRole)
                model.appendRow(item)

        if model.rowCount() == 0:
            model.appendRow(QStandardItem("No available layers"))

        combobox.setModel(model)

        ComboBoxHandler.keepPopupOpen(combobox)

        combobox.view().pressed.connect(
            lambda index: combobox.keepPopupOpen(index, combobox)
        )

        return combobox

    @staticmethod
    def loadMetricsToCombobox(combobox):
        combobox.clear()
        model = QStandardItemModel(combobox)

        for metric in Metrics:
            item = QStandardItem(metric.getMetricName)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item.setData(Qt.Unchecked, Qt.CheckStateRole)
            item.setData((metric.getMetricCalculation(), metric.getMetricName), Qt.UserRole)
            model.appendRow(item)

        combobox.setModel(model)

        combobox.view().pressed.connect(
            lambda index: ComboBoxHandler.toggleMetricCheckbox(index, combobox)
        )

        return combobox

    @staticmethod
    def toggleMetricCheckbox(index, combobox):
        item = combobox.model().itemFromIndex(index)
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)

    @staticmethod
    def getCheckedItems(combobox):
        checkItems = []
        model = combobox.model()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item.checkState() == Qt.Checked:
                checkItems.append(item.data(Qt.UserRole))
        return checkItems

    @staticmethod
    def keepPopupOpen(combobox):
        view = combobox.view()
        view._original_mouseReleaseEvent = view.mouseReleaseEvent
        view.mouseReleaseEvent = lambda event: ComboBoxHandler.handleMouseReleaseEvent(combobox, event)

    @staticmethod
    def handleMouseReleaseEvent(combobox, event):
        view = combobox.view()
        index = view.indexAt(event.pos())

        if index.isValid():
            item = combobox.model().itemFromIndex(index)
            if item.checkState() == Qt.Checked:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)
        else:
            view._original_mouseReleaseEvent(event)