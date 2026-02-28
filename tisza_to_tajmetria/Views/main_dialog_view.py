# -*- coding: utf-8 -*-

from ..tisza_to_tajmetria_dialog import TiszaToTajmetriaDialog


class MainDialogView:
    def __init__(self):
        self.dialog = None

    def create_dialog(self):
        self.dialog = TiszaToTajmetriaDialog()

    def bind_actions(self, on_calculate, on_export, on_cancel):
        self.dialog.calculateButton.clicked.connect(on_calculate)
        self.dialog.exportButton.clicked.connect(on_export)
        self.dialog.cancelButton.pressed.connect(on_cancel)

    def configure_save_dialog(self):
        self.dialog.saveFileDialog.setFilter("Excel files (*.xlsx);")

    def set_output_path(self, file_path):
        self.dialog.saveFileDialog.setFilePath(file_path)

    def get_output_path(self):
        return self.dialog.saveFileDialog.filePath()

    def show_modal(self):
        self.dialog.show()
        self.dialog.exec_()

    def show_progress(self):
        self.dialog.progressBar.setVisible(True)
        self.dialog.progressLabel.setVisible(True)
        self.dialog.cancelButton.setVisible(True)
        self.dialog.cancelButton.setEnabled(True)
        self.dialog.progressBar.raise_()
        self.dialog.progressLabel.raise_()
        self.dialog.cancelButton.raise_()

    def hide_progress(self):
        self.dialog.progressBar.setVisible(False)
        self.dialog.progressLabel.setVisible(False)
        self.dialog.cancelButton.setVisible(False)
        self.dialog.cancelButton.setEnabled(False)
        self.dialog.progressBar.setValue(0)
        self.dialog.progressLabel.setText("Ready")

    def update_progress(self, percent, message):
        self.dialog.progressBar.setValue(percent)
        self.dialog.progressLabel.setText(message)

    def set_buttons_enabled(self, calculate_enabled, export_enabled):
        self.dialog.calculateButton.setEnabled(calculate_enabled)
        self.dialog.exportButton.setEnabled(export_enabled)

    def set_export_enabled(self, enabled):
        self.dialog.exportButton.setEnabled(enabled)

    def set_cancelling_state(self):
        self.dialog.progressLabel.setText("Cancelling...")
        self.dialog.cancelButton.setEnabled(False)

    def selected_export_formats(self):
        return (
            self.dialog.exportExcelCheckbox.isChecked(),
            self.dialog.exportCsvCheckbox.isChecked(),
            self.dialog.exportMapCheckbox.isChecked(),
        )

    @property
    def layer_selector(self):
        return self.dialog.layerSelector

    @property
    def metric_selector(self):
        return self.dialog.metricSelector
