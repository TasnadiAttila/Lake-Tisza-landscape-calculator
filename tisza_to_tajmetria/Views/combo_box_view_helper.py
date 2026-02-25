from qgis.core import QgsProject
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from tisza_to_tajmetria.Metrics.metric_collector import Metrics


class ComboBoxViewHelper:
    ALL_NONE_TEXT = "All / None"
    DEFAULT_FILTER_DELAY_MS = 400
    DEFAULT_MAX_SELECTED_LABELS = 3

    @staticmethod
    def make_combobox_editable(combobox):
        combobox.setEditable(True)
        combobox.lineEdit().setPlaceholderText("Search...")

    @staticmethod
    def load_layers_to_combobox(combobox, layer_types=None):
        if layer_types is None:
            layer_types = ['raster']

        combobox.clear()
        layers = QgsProject.instance().mapLayers().values()
        model = QStandardItemModel(combobox)

        all_none_item = QStandardItem(ComboBoxViewHelper.ALL_NONE_TEXT)
        all_none_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        all_none_item.setData(Qt.Unchecked, Qt.CheckStateRole)
        all_none_item.setData(ComboBoxViewHelper.ALL_NONE_TEXT, Qt.UserRole)
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
        ComboBoxViewHelper.setup_common_features(combobox)
        return combobox

    @staticmethod
    def load_metrics_to_combobox(combobox):
        combobox.clear()
        model = QStandardItemModel(combobox)

        all_none_item = QStandardItem(ComboBoxViewHelper.ALL_NONE_TEXT)
        all_none_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        all_none_item.setData(Qt.Unchecked, Qt.CheckStateRole)
        all_none_item.setData(ComboBoxViewHelper.ALL_NONE_TEXT, Qt.UserRole)
        model.appendRow(all_none_item)

        for metric in Metrics:
            item = QStandardItem(metric.metric_name)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item.setData(Qt.Unchecked, Qt.CheckStateRole)
            item.setData((metric.get_metric_calculation(), metric.metric_name), Qt.UserRole)
            model.appendRow(item)

        combobox.setModel(model)
        ComboBoxViewHelper.setup_common_features(combobox)
        return combobox

    @staticmethod
    def load_diagram_metrics_from_selected_metrics(diagram_combobox, selected_metrics):
        previous_checked = {
            metric_name for _, metric_name in ComboBoxViewHelper.get_checked_items(diagram_combobox)
        }

        diagram_combobox.clear()
        model = QStandardItemModel(diagram_combobox)

        all_none_item = QStandardItem(ComboBoxViewHelper.ALL_NONE_TEXT)
        all_none_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        all_none_item.setData(Qt.Unchecked, Qt.CheckStateRole)
        all_none_item.setData(ComboBoxViewHelper.ALL_NONE_TEXT, Qt.UserRole)
        model.appendRow(all_none_item)

        for calc_func, metric_name in selected_metrics:
            item = QStandardItem(metric_name)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)

            if metric_name in previous_checked:
                item.setData(Qt.Checked, Qt.CheckStateRole)
            else:
                item.setData(Qt.Unchecked, Qt.CheckStateRole)

            item.setData((calc_func, metric_name), Qt.UserRole)
            model.appendRow(item)

        diagram_combobox.setModel(model)
        ComboBoxViewHelper.setup_common_features(diagram_combobox)
        return diagram_combobox

    @staticmethod
    def setup_common_features(combobox, filter_delay_ms=None, max_selected_labels=None):
        ComboBoxViewHelper.make_combobox_editable(combobox)
        ComboBoxViewHelper.keep_popup_open_on_click(combobox)

        if filter_delay_ms is None:
            filter_delay_ms = ComboBoxViewHelper.DEFAULT_FILTER_DELAY_MS
        if max_selected_labels is None:
            max_selected_labels = ComboBoxViewHelper.DEFAULT_MAX_SELECTED_LABELS

        combobox.setProperty("maxSelectedLabels", max_selected_labels)
        combobox.setProperty("filterDelayMs", filter_delay_ms)

        previous_model = combobox.property("itemChangedModel")
        previous_handler = combobox.property("itemChangedHandler")
        if previous_model is not None and previous_handler is not None:
            try:
                previous_model.itemChanged.disconnect(previous_handler)
            except Exception:
                pass

        def on_item_changed():
            ComboBoxViewHelper.update_line_edit_text(combobox)

        combobox.model().itemChanged.connect(on_item_changed)
        combobox.setProperty("itemChangedModel", combobox.model())
        combobox.setProperty("itemChangedHandler", on_item_changed)

        previous_text_handler = combobox.property("filterTextChangedHandler")
        if previous_text_handler is not None:
            try:
                combobox.lineEdit().textChanged.disconnect(previous_text_handler)
            except Exception:
                pass

        filter_timer = combobox.property("filterTimer")
        if filter_timer is None:
            filter_timer = QTimer(combobox)
            filter_timer.setSingleShot(True)

            def on_filter_timeout():
                pending_text = combobox.property("pendingFilterText") or ""
                ComboBoxViewHelper.filter_model(combobox, pending_text)

            filter_timer.timeout.connect(on_filter_timeout)
            combobox.setProperty("filterTimer", filter_timer)

        def on_text_changed(text):
            combobox.setProperty("pendingFilterText", text)
            filter_timer.stop()
            filter_timer.start(filter_delay_ms)

        combobox.lineEdit().textChanged.connect(on_text_changed)
        combobox.setProperty("filterTextChangedHandler", on_text_changed)

        ComboBoxViewHelper.update_line_edit_text(combobox)

    @staticmethod
    def handle_all_none_item(combobox):
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

        ComboBoxViewHelper.update_line_edit_text(combobox)

        combobox.lineEdit().blockSignals(False)
        model.blockSignals(False)

        if model.rowCount() > 0:
            model.dataChanged.emit(model.index(0, 0), model.index(model.rowCount() - 1, 0))

    @staticmethod
    def keep_popup_open_on_click(combobox):
        view = combobox.view()

        def handle_press(index):
            item = combobox.model().itemFromIndex(index)
            if item and item.isEnabled():
                if item.text() == ComboBoxViewHelper.ALL_NONE_TEXT:
                    new_state = Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
                    item.setCheckState(new_state)

                    ComboBoxViewHelper.handle_all_none_item(combobox)

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
    def update_line_edit_text(combobox):
        checked_items = []
        model = combobox.model()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item and item.checkState() == Qt.Checked and item.text() != ComboBoxViewHelper.ALL_NONE_TEXT:
                checked_items.append(item.text())

        filter_timer = combobox.property("filterTimer")
        if filter_timer is not None:
            filter_timer.stop()
            combobox.setProperty("pendingFilterText", "")

        max_selected_labels = combobox.property("maxSelectedLabels")
        if max_selected_labels is None:
            max_selected_labels = ComboBoxViewHelper.DEFAULT_MAX_SELECTED_LABELS

        if len(checked_items) == 0:
            display_text = ""
        elif len(checked_items) <= max_selected_labels:
            display_text = ", ".join(checked_items)
        else:
            display_text = f"{len(checked_items)} selected"

        combobox.lineEdit().blockSignals(True)
        combobox.lineEdit().setText(display_text)
        combobox.lineEdit().blockSignals(False)

    @staticmethod
    def filter_model(combobox, text):
        model = combobox.model()
        search_term = text.lower().strip()

        checked_items = [
            model.item(i).text() for i in range(model.rowCount())
            if model.item(i) and model.item(i).checkState() == Qt.Checked
            and model.item(i).text() != ComboBoxViewHelper.ALL_NONE_TEXT
        ]

        joined_checked = ", ".join(checked_items).lower()
        if search_term == "" or search_term == joined_checked:
            for i in range(model.rowCount()):
                combobox.view().setRowHidden(i, False)
            return

        for i in range(model.rowCount()):
            item = model.item(i)
            if item:
                item_text = item.text().lower()
                if item_text == ComboBoxViewHelper.ALL_NONE_TEXT.lower():
                    combobox.view().setRowHidden(i, False)
                    continue

                is_hidden = search_term not in item_text and item.checkState() != Qt.Checked
                combobox.view().setRowHidden(i, is_hidden)

    @staticmethod
    def get_checked_items(combobox):
        checked_items_data = []
        model = combobox.model()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item and item.checkState() == Qt.Checked and item.text() != ComboBoxViewHelper.ALL_NONE_TEXT:
                checked_items_data.append(item.data(Qt.UserRole))
        return checked_items_data
