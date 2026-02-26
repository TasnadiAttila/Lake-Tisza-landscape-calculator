# -*- coding: utf-8 -*-

import logging
import os

from qgis.core import Qgis

from .background_task_worker import MetricCalculationWorker, ExcelExportWorker
from ..Models.plugin_model import PluginModel
from ..Services.dependency_service import DependencyService
from ..Services.export_service import ExportService
from ..Views.combo_box_view_helper import ComboBoxViewHelper
from ..Views.main_dialog_view import MainDialogView

LOGGER = logging.getLogger(__name__)


class PluginController:
    def __init__(self, iface):
        self.iface = iface
        self.model = PluginModel()
        self.view = MainDialogView()

        self._initialized = False
        self.calculation_worker = None
        self.export_worker = None

    def run(self):
        DependencyService.ensure_xlsxwriter_installed(self.iface)

        if not self._initialized:
            self._initialize_view()
            self._initialized = True

        self.view.show_modal()

    def _initialize_view(self):
        self.view.create_dialog()
        self.view.bind_actions(self.on_calculate_clicked, self.on_export_clicked, self.on_cancel_clicked)
        self.view.configure_save_dialog()

        ComboBoxViewHelper.make_combobox_editable(self.view.layer_selector)
        ComboBoxViewHelper.make_combobox_editable(self.view.metric_selector)

        ComboBoxViewHelper.load_layers_to_combobox(self.view.layer_selector, ['raster'])
        ComboBoxViewHelper.load_metrics_to_combobox(self.view.metric_selector)

        self.view.set_output_path("")

        self.view.layer_selector.model().dataChanged.connect(self.update_export_button_state)
        self.view.layer_selector.model().rowsInserted.connect(self.update_export_button_state)
        self.view.layer_selector.model().rowsRemoved.connect(self.update_export_button_state)

        self.view.metric_selector.model().dataChanged.connect(self.update_export_button_state)
        self.view.metric_selector.model().rowsInserted.connect(self.update_export_button_state)
        self.view.metric_selector.model().rowsRemoved.connect(self.update_export_button_state)

        self.update_export_button_state()

    def show_progress(self):
        self.view.show_progress()

    def hide_progress(self):
        self.view.hide_progress()

    def on_progress_update(self, percent, message):
        self.view.update_progress(percent, message)

    def on_calculate_clicked(self):
        selected_layers = ComboBoxViewHelper.get_checked_items(self.view.layer_selector)
        if not selected_layers:
            self.iface.messageBar().pushMessage(
                "Error",
                "No layer selected!",
                level=Qgis.Warning,
                duration=3,
            )
            return

        selected_metrics = ComboBoxViewHelper.get_checked_items(self.view.metric_selector)
        if not selected_metrics:
            self.iface.messageBar().pushMessage(
                "Error",
                "No metric selected!",
                level=Qgis.Warning,
                duration=3,
            )
            return

        self.view.set_buttons_enabled(False, False)
        self.show_progress()

        self.calculation_worker = MetricCalculationWorker(
            selected_layers,
            selected_metrics,
            self.model.get_land_cover_mapping_from_layer,
            self.model.UNIT_MAPPING,
        )

        self.calculation_worker.progress.connect(self.on_progress_update)
        self.calculation_worker.finished_calculation.connect(self.on_calculation_finished)
        self.calculation_worker.error.connect(self.on_calculation_error)
        self.calculation_worker.start()

    def on_calculation_finished(self, data_to_write, metric_data):
        self.hide_progress()
        self.model.set_calculation_results(data_to_write, metric_data)
        self.view.set_buttons_enabled(True, True)

        self.iface.messageBar().pushMessage(
            "Success",
            f"Calculation complete! {len(data_to_write)} metrics calculated.",
            level=Qgis.Success,
            duration=5,
        )

        self._cleanup_calculation_worker()

    def on_calculation_error(self, error_message):
        self.hide_progress()
        self.view.set_buttons_enabled(True, False)

        self.iface.messageBar().pushMessage(
            "Error",
            error_message,
            level=Qgis.Critical,
            duration=10,
        )

        self._cleanup_calculation_worker()

    def on_export_finished(self, output_path):
        self.hide_progress()
        self.view.set_buttons_enabled(True, True)

        self.iface.messageBar().pushMessage(
            "Success",
            f"Data exported successfully to: {output_path}",
            level=Qgis.Success,
            duration=5,
        )

        self._cleanup_export_worker()

    def on_export_error(self, error_message):
        self.hide_progress()
        self.view.set_buttons_enabled(True, True)

        self.iface.messageBar().pushMessage(
            "Error",
            error_message,
            level=Qgis.Critical,
            duration=10,
        )

        self._cleanup_export_worker()

    def on_cancel_clicked(self):
        if self.calculation_worker and self.calculation_worker.isRunning():
            self.calculation_worker.cancel()
            self.view.set_cancelling_state()

        if self.export_worker and self.export_worker.isRunning():
            self.export_worker.cancel()
            self.view.set_cancelling_state()

    def update_export_button_state(self):
        selected_layers = ComboBoxViewHelper.get_checked_items(self.view.layer_selector)
        selected_metrics = ComboBoxViewHelper.get_checked_items(self.view.metric_selector)

        is_enabled = len(selected_layers) > 0 and len(selected_metrics) > 0
        self.view.set_export_enabled(is_enabled)

    def on_export_clicked(self):
        if not self.model.has_calculation_results():
            self.iface.messageBar().pushMessage(
                "Error",
                "Please run Calculate first before exporting!",
                level=Qgis.Warning,
                duration=5,
            )
            return

        output_path = self.view.get_output_path()
        if not output_path:
            self.iface.messageBar().pushMessage(
                "Error",
                "Please select an output file path first!",
                level=Qgis.Warning,
                duration=5,
            )
            return

        export_excel, export_csv, export_map = self.view.selected_export_formats()
        if not (export_excel or export_csv or export_map):
            self.iface.messageBar().pushMessage(
                "Warning",
                "Please select at least one export format!",
                level=Qgis.Warning,
                duration=5,
            )
            return

        self.view.set_buttons_enabled(False, False)
        self.show_progress()

        headers = self.model.EXPORT_HEADERS

        if export_excel:
            excel_path = output_path if output_path.lower().endswith('.xlsx') else output_path + '.xlsx'

            self.export_worker = ExcelExportWorker(
                self.model.last_calculation_data,
                headers,
                excel_path,
            )

            self.export_worker.progress.connect(self.on_progress_update)
            self.export_worker.finished_export.connect(
                lambda path: self.on_format_export_finished(path, export_csv, export_map, output_path, headers)
            )
            self.export_worker.error.connect(self.on_export_error)
            self.export_worker.start()
        else:
            self.on_format_export_finished(None, export_csv, export_map, output_path, headers)

    def on_format_export_finished(self, excel_path, export_csv, export_map, base_output_path, headers):
        export_paths = []

        if excel_path:
            export_paths.append(f"Excel: {os.path.basename(excel_path)}")

        if export_csv:
            try:
                self.view.update_progress(60, "Exporting to CSV...")
                export_paths.extend(
                    ExportService.export_csv_bundle(
                        self.model.last_calculation_data,
                        self.model.last_metric_data,
                        base_output_path,
                        headers,
                    )
                )

            except Exception as e:
                LOGGER.exception("CSV export error")
                self.iface.messageBar().pushMessage(
                    "Warning",
                    f"CSV export failed: {str(e)}",
                    level=Qgis.Warning,
                    duration=5,
                )

        if export_map:
            try:
                selected_layers = ComboBoxViewHelper.get_checked_items(self.view.layer_selector)

                self.view.update_progress(80, "Generating GeoJSON and web map...")
                export_paths.extend(
                    ExportService.export_map_bundle(
                        selected_layers,
                        self.model.last_metric_data,
                        self.model.last_calculation_data,
                        base_output_path,
                        open_in_browser=True,
                    )
                )

            except Exception as e:
                LOGGER.exception("GeoJSON/Map export error")
                self.iface.messageBar().pushMessage(
                    "Warning",
                    f"GeoJSON/Map export failed: {str(e)}",
                    level=Qgis.Warning,
                    duration=5,
                )

        self.hide_progress()
        self.view.set_buttons_enabled(True, True)

        if export_paths:
            message = "Data exported successfully!\\n" + "\\n".join(export_paths)
            self.iface.messageBar().pushMessage(
                "Success",
                message,
                level=Qgis.Success,
                duration=10,
            )

        self._cleanup_export_worker()

    def _cleanup_calculation_worker(self):
        if self.calculation_worker:
            self.calculation_worker.deleteLater()
            self.calculation_worker = None

    def _cleanup_export_worker(self):
        if self.export_worker:
            self.export_worker.deleteLater()
            self.export_worker = None
