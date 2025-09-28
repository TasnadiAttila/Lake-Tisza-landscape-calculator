from qgis.core import QgsProject
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5 import QtWidgets

from tisza_to_tajmetria.Metrics.MetricCollector import Metrics


class ComboBoxHandler:
    @staticmethod
    def makeComboboxEditable(combobox):
        combobox.setEditable(True)
        combobox.lineEdit().setPlaceholderText("Search...")

    @staticmethod
    def loadLayersToCombobox(combobox, layer_types=None):
        if layer_types is None:
            layer_types = ['raster']

        combobox.clear()
        layers = QgsProject.instance().mapLayers().values()
        model = QStandardItemModel(combobox)

        for layer in layers:
            if 'raster' in layer_types and layer.type() == layer.RasterLayer:
                item = QStandardItem(layer.name())
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                item.setData(Qt.Unchecked, Qt.CheckStateRole)
                item.setData(layer, Qt.UserRole)  # a réteg maga
                model.appendRow(item)

        if model.rowCount() == 0:
            item = QStandardItem("No layers found")
            item.setEnabled(False)
            model.appendRow(item)

        combobox.setModel(model)
        ComboBoxHandler.setupCommonFeatures(combobox)
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
        ComboBoxHandler.setupCommonFeatures(combobox)
        return combobox

    @staticmethod
    def setupCommonFeatures(combobox):
        ComboBoxHandler.makeComboboxEditable(combobox)
        ComboBoxHandler.keepPopupOpenOnClick(combobox)

        combobox.model().itemChanged.connect(
            lambda: ComboBoxHandler.updateLineEditText(combobox)
        )

        combobox.lineEdit().textChanged.connect(
            lambda text: ComboBoxHandler.filterModel(combobox, text)
        )

        ComboBoxHandler.updateLineEditText(combobox)

    @staticmethod
    def keepPopupOpenOnClick(combobox):
        view = combobox.view()

        def handle_press(index):
            item = combobox.model().itemFromIndex(index)
            if item and item.isEnabled():
                new_state = Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
                item.setCheckState(new_state)
            combobox.showPopup()

        try:
            view.pressed.disconnect()
        except Exception:
            pass

        view.pressed.connect(handle_press)

    @staticmethod
    def updateLineEditText(combobox):
        checked_items = []
        model = combobox.model()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item and item.checkState() == Qt.Checked:
                checked_items.append(item.text())

        combobox.lineEdit().blockSignals(True)
        combobox.lineEdit().setText(", ".join(checked_items))
        combobox.lineEdit().blockSignals(False)

    @staticmethod
    def filterModel(combobox, text):
        model = combobox.model()
        search_term = text.lower().strip()

        checked_items = [
            model.item(i).text() for i in range(model.rowCount())
            if model.item(i) and model.item(i).checkState() == Qt.Checked
        ]
        if search_term == "" or search_term == ", ".join(checked_items).lower():
            for i in range(model.rowCount()):
                combobox.view().setRowHidden(i, False)
            combobox.showPopup()
            return

        for i in range(model.rowCount()):
            item = model.item(i)
            if item:
                item_text = item.text().lower()
                is_hidden = search_term not in item_text and item.checkState() != Qt.Checked
                combobox.view().setRowHidden(i, is_hidden)

        combobox.showPopup()

    @staticmethod
    def getCheckedItems(combobox):
        checked_items_data = []
        model = combobox.model()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item and item.checkState() == Qt.Checked:
                checked_items_data.append(item.data(Qt.UserRole))
        return checked_items_data
