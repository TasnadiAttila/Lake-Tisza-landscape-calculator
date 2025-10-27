from qgis.core import QgsProject
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5 import QtWidgets

from tisza_to_tajmetria.Metrics.MetricCollector import Metrics


class ComboBoxHandler:
    ALL_NONE_TEXT = "All / None"

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

        all_none_item = QStandardItem(ComboBoxHandler.ALL_NONE_TEXT)
        all_none_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        all_none_item.setData(Qt.Unchecked, Qt.CheckStateRole)
        all_none_item.setData(ComboBoxHandler.ALL_NONE_TEXT, Qt.UserRole)
        model.appendRow(all_none_item)

        found_layers = False
        for layer in layers:
            if 'raster' in layer_types and layer.type() == layer.RasterLayer:
                item = QStandardItem(layer.name())

                is_osm_standard = layer.name() == "OSM Standard"

                if is_osm_standard:
                    item.setFlags(Qt.ItemIsEnabled)
                    item.setData(Qt.Unchecked, Qt.CheckStateRole)
                else:
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                    item.setData(Qt.Unchecked, Qt.CheckStateRole)

                item.setData(layer, Qt.UserRole)
                model.appendRow(item)
                found_layers = True

        if not found_layers:
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

        all_none_item = QStandardItem(ComboBoxHandler.ALL_NONE_TEXT)
        all_none_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        all_none_item.setData(Qt.Unchecked, Qt.CheckStateRole)
        all_none_item.setData(ComboBoxHandler.ALL_NONE_TEXT, Qt.UserRole)
        model.appendRow(all_none_item)

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
    def loadDiagramMetricsFromSelectedMetrics(diagram_combobox, selected_metrics):
        previous_checked = {
            metric_name for _, metric_name in ComboBoxHandler.getCheckedItems(diagram_combobox)
        }

        diagram_combobox.clear()
        model = QStandardItemModel(diagram_combobox)

        all_none_item = QStandardItem(ComboBoxHandler.ALL_NONE_TEXT)
        all_none_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        all_none_item.setData(Qt.Unchecked, Qt.CheckStateRole)
        all_none_item.setData(ComboBoxHandler.ALL_NONE_TEXT, Qt.UserRole)
        model.appendRow(all_none_item)

        for calc_func, metric_name in selected_metrics:
            item = QStandardItem(metric_name)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)

            # ✅ Visszaállítjuk a korábban kiválasztottakat
            if metric_name in previous_checked:
                item.setData(Qt.Checked, Qt.CheckStateRole)
            else:
                item.setData(Qt.Unchecked, Qt.CheckStateRole)

            item.setData((calc_func, metric_name), Qt.UserRole)
            model.appendRow(item)

        diagram_combobox.setModel(model)
        ComboBoxHandler.setupCommonFeatures(diagram_combobox)
        return diagram_combobox

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
    def handleAllNoneItem(combobox):
        model = combobox.model()

        model.blockSignals(True)
        combobox.lineEdit().blockSignals(True)

        all_none_item = model.item(0)

        checked_count = 0
        total_items = model.rowCount()

        checkable_items = []
        for i in range(1, total_items):
            item = model.item(i)
            if item and (item.flags() & Qt.ItemIsUserCheckable):
                checkable_items.append(item)
                if item.checkState() == Qt.Checked:
                    checked_count += 1

        checkable_count = len(checkable_items)

        if checked_count == checkable_count:
            target_state = Qt.Unchecked
        else:
            target_state = Qt.Checked

        for item in checkable_items:
            if item.checkState() != target_state:
                item.setCheckState(target_state)

        all_none_item.setCheckState(Qt.Unchecked)

        ComboBoxHandler.updateLineEditText(combobox)

        combobox.lineEdit().blockSignals(False)
        model.blockSignals(False)

    @staticmethod
    def keepPopupOpenOnClick(combobox):
        view = combobox.view()

        def handle_press(index):
            item = combobox.model().itemFromIndex(index)
            if item and item.isEnabled():
                if item.text() == ComboBoxHandler.ALL_NONE_TEXT:
                    new_state = Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
                    item.setCheckState(new_state)

                    ComboBoxHandler.handleAllNoneItem(combobox)

                elif item.flags() & Qt.ItemIsUserCheckable:
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
            if item and item.checkState() == Qt.Checked and item.text() != ComboBoxHandler.ALL_NONE_TEXT:
                checked_items.append(item.text())

        combobox.lineEdit().blockSignals(True)
        combobox.lineEdit().setText(", ".join(checked_items))
        combobox.lineEdit().blockSignals(False)

    @staticmethod
    def filterModel(combobox, text):
        model = combobox.model()
        search_term = text.lower().strip()

        # Store which items are checked so filtering doesn't hide them
        checked_items = [
            model.item(i).text() for i in range(model.rowCount())
            if model.item(i) and model.item(i).checkState() == Qt.Checked
            and model.item(i).text() != ComboBoxHandler.ALL_NONE_TEXT
        ]

        # Avoid interfering with typing when the text is equal to checked items string
        joined_checked = ", ".join(checked_items).lower()
        if search_term == "" or search_term == joined_checked:
            for i in range(model.rowCount()):
                combobox.view().setRowHidden(i, False)
            return  # 🔸 don't reopen popup or rewrite text

        # Filtering logic
        for i in range(model.rowCount()):
            item = model.item(i)
            if item:
                item_text = item.text().lower()
                if item_text == ComboBoxHandler.ALL_NONE_TEXT.lower():
                    combobox.view().setRowHidden(i, False)
                    continue

                is_hidden = search_term not in item_text and item.checkState() != Qt.Checked
                combobox.view().setRowHidden(i, is_hidden)

        # 🔸 Don't reopen popup while typing, it causes focus loss
        # combobox.showPopup()  # <-- remove this line


    @staticmethod
    def getCheckedItems(combobox):
        checked_items_data = []
        model = combobox.model()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item and item.checkState() == Qt.Checked and item.text() != ComboBoxHandler.ALL_NONE_TEXT:
                checked_items_data.append(item.data(Qt.UserRole))
        return checked_items_data

    @staticmethod
    def updateDiagramMetricSelector(layerSelector, metricSelector, diagramMetricSelector):
        """
        Aktiválja és frissíti a diagramMetricSelector-t, ha legalább két layer ki van választva,
        és frissíti a tartalmát az alapján, hogy a metricSelectorban mik vannak bejelölve.
        """
        selected_layers = ComboBoxHandler.getCheckedItems(layerSelector)
        selected_metrics = ComboBoxHandler.getCheckedItems(metricSelector)

        if len(selected_layers) >= 2 and selected_metrics:
            diagramMetricSelector.setEnabled(True)
            ComboBoxHandler.loadDiagramMetricsFromSelectedMetrics(
                diagramMetricSelector, selected_metrics
            )
        else:
            diagramMetricSelector.setEnabled(False)
            diagramMetricSelector.clear()
