from qgis.core import QgsProject
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from tisza_to_tajmetria.Metrics.Metrics import Metrics


class ComboBoxHandler:

    @staticmethod
    def addClearButtonToCombobox(combobox):
        combobox.setEditable(True)
        combobox.setInsertPolicy(combobox.NoInsert)
        combobox.setCurrentIndex(-1)

        combobox.lineEdit().textChanged.connect(
            lambda text: ComboBoxHandler.textChangeOnSearch(combobox, text)
        )
        combobox._popup_opened = False

    @staticmethod
    def textChangeOnSearch(combobox, text):
        if text != combobox.lineEdit().text():
            ComboBoxHandler.filterCombobox(combobox, text)

            if not combobox._popup_opened:
                combobox.showPopup()
                combobox._popup_opened = True

            combobox.lineEdit().setFocus()

    @staticmethod
    def filterCombobox(combobox, text):
        model = combobox.model()
        text = text.lower().strip()

        for i in range(model.rowCount()):
            item = model.item(i)
            if item.text() == "No available layers":
                combobox.view().setRowHidden(i, False)
                continue

            is_match = text in item.text().lower()
            combobox.view().setRowHidden(i, not is_match)

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
                item.setData(layer, Qt.UserRole)
                model.appendRow(item)

        if model.rowCount() == 0:
            model.appendRow(QStandardItem("No available layers"))

        combobox.setModel(model)

        ComboBoxHandler.keepPopupOpen(combobox)

        combobox.view().pressed.connect(
            lambda index: ComboBoxHandler.toggleMetricCheckbox(index, combobox)
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
        if item is None:
            return

        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)

        checked_items = []
        model = combobox.model()
        for i in range(model.rowCount()):
            row_item = model.item(i)
            if row_item.checkState() == Qt.Checked:
                checked_items.append(row_item.text())

        combobox.lineEdit().setText(", ".join(checked_items))

    @staticmethod
    def getCheckedItems(combobox):
        checked_items = []
        model = combobox.model()
        if model is None:
            return checked_items

        for i in range(model.rowCount()):
            item = model.item(i)
            if item and item.checkState() == Qt.Checked:
                checked_items.append(item.data(Qt.UserRole))
        return checked_items

    @staticmethod
    def keepPopupOpen(combobox):
        view = combobox.view()

        if hasattr(view, "_original_mouseReleaseEvent"):
            return

        view._original_mouseReleaseEvent = view.mouseReleaseEvent

        def _mouseReleaseEvent(event):
            index = view.indexAt(event.pos())
            if index.isValid():
                rect = view.visualRect(index)
                checkbox_area = rect.adjusted(0, 0, 20, 0)  # kb. checkbox hely
                if event.pos().x() <= checkbox_area.right():
                    ComboBoxHandler.toggleMetricCheckbox(index, combobox)
                    return

            view._original_mouseReleaseEvent(event)

        view.mouseReleaseEvent = _mouseReleaseEvent

    @staticmethod
    def handleMouseReleaseEvent(combobox, event):
        view = combobox.view()
        index = view.indexAt(event.pos())

        if index.isValid():
            ComboBoxHandler.toggleMetricCheckbox(index, combobox)
        else:
            view._original_mouseReleaseEvent(event)

    @staticmethod
    def updateLineEditWithCheckedItems(combobox):
        model = combobox.model()
        if model is None:
            combobox.lineEdit().clear()
            return

        checked_names = []
        for i in range(model.rowCount()):
            item = model.item(i)
            if item and item.checkState() == Qt.Checked:
                checked_names.append(item.text())

        combobox.lineEdit().setText(", ".join(checked_names))
