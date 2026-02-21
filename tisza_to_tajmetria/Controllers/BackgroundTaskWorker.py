# -*- coding: utf-8 -*-
"""
Background task worker for landscape metric calculations
Provides non-blocking computation with progress reporting and cancellation support
"""

from qgis.PyQt.QtCore import QThread, pyqtSignal
import xlsxwriter
import time


class MetricCalculationWorker(QThread):
    """
    Worker thread for calculating landscape metrics in the background.
    
    Signals:
        progress: Emitted when progress updates (int: 0-100, str: status message)
        finished_calculation: Emitted when calculation completes (list: data_to_write, dict: metric_data)
        error: Emitted when an error occurs (str: error message)
    """
    
    progress = pyqtSignal(int, str)  # percentage, message
    finished_calculation = pyqtSignal(list, dict)  # data_to_write, metric_data
    error = pyqtSignal(str)  # error message
    
    def __init__(self, selected_layers, selected_metrics, land_cover_mapping_func, unit_mapping, parent=None):
        """
        Initialize the worker.
        
        Args:
            selected_layers: List of QgsRasterLayer objects
            selected_metrics: List of tuples (metric_func, metric_name)
            land_cover_mapping_func: Function to get land cover mapping from layer
            unit_mapping: Dict mapping metric names to units
            parent: Parent QObject
        """
        super().__init__(parent)
        self.selected_layers = selected_layers
        self.selected_metrics = selected_metrics
        self.land_cover_mapping_func = land_cover_mapping_func
        self.unit_mapping = unit_mapping
        self._is_cancelled = False
        
    def cancel(self):
        """Cancel the running calculation."""
        self._is_cancelled = True

    @staticmethod
    def _format_layer_metric_value(value):
        """Format metric value for simplified per-layer summary output."""
        if isinstance(value, dict):
            for candidate in value.values():
                if isinstance(candidate, (int, float)):
                    return f"{candidate:.2f}"
            return str(value)
        if isinstance(value, (int, float)):
            return f"{value:.2f}"
        return str(value)
        
    def run(self):
        """Execute the calculation in background thread."""
        try:
            data_to_write = []
            metric_data = {}
            
            total_tasks = len(self.selected_layers) * len(self.selected_metrics)
            current_task = 0
            
            for layer in self.selected_layers:
                if self._is_cancelled:
                    self.progress.emit(0, "Cancelled")
                    return
                    
                layer_name = layer.name()
                land_cover_mapping = self.land_cover_mapping_func(layer)
                layer_metrics = {}
                
                for metric_func, metric_name in self.selected_metrics:
                    if self._is_cancelled:
                        self.progress.emit(0, "Cancelled")
                        return
                    
                    current_task += 1
                    progress_percent = int((current_task / total_tasks) * 100)
                    self.progress.emit(progress_percent, f"Calculating {metric_name} for {layer_name}...")
                    
                    default_unit = self.unit_mapping.get(metric_name, "N/A")
                    
                    try:
                        value = metric_func(layer)
                        
                        # Store for GeoJSON export (simplified format)
                        layer_metrics[metric_name] = self._format_layer_metric_value(value)
                        
                        # Process results for Excel export
                        if isinstance(value, dict):
                            if metric_name == "Patch Density":
                                patch_stats = value.get("patch_stats", {})
                                
                                for cls, stats in patch_stats.items():
                                    original_label = land_cover_mapping.get(cls, f"Class {cls}")
                                    
                                    if isinstance(original_label, str) and " - " in original_label:
                                        class_name = original_label.split(" - ", 1)[1].strip()
                                    else:
                                        class_name = str(original_label)
                                    
                                    if class_name.lower().startswith("class "):
                                        continue
                                    
                                    num_patches = stats.get("num_patches", 0)
                                    data_to_write.append([
                                        layer_name,
                                        metric_name,
                                        "Patch Count",
                                        num_patches,
                                        "patches",
                                        cls,
                                        class_name,
                                    ])
                                    
                                    class_patch_density = stats.get("patch_density", 0)
                                    data_to_write.append([
                                        layer_name,
                                        metric_name,
                                        "Patch Density",
                                        class_patch_density,
                                        "patches/km²",
                                        cls,
                                        class_name,
                                    ])
                            
                            elif metric_name == "Land Cover":
                                for cls, percentage in value.items():
                                    original_label = land_cover_mapping.get(cls, f"Class {cls}")
                                    if isinstance(original_label, str) and " - " in original_label:
                                        class_name = original_label.split(" - ", 1)[1].strip()
                                    else:
                                        class_name = str(original_label)
                                    
                                    if class_name.lower().startswith("class "):
                                        continue
                                    
                                    data_to_write.append([
                                        layer_name,
                                        metric_name,
                                        "Percentage",
                                        float(percentage),
                                        "%",
                                        cls,
                                        class_name,
                                    ])
                            
                            elif metric_name in ["Mean Patch Area", "Median Patch Area", "Smallest Patch Area", 
                                                  "Greatest Patch Area"]:
                                for cls, area_value in value.items():
                                    original_label = land_cover_mapping.get(cls, f"Class {cls}")
                                    if isinstance(original_label, str) and " - " in original_label:
                                        class_name = original_label.split(" - ", 1)[1].strip()
                                    else:
                                        class_name = str(original_label)
                                    
                                    if class_name.lower().startswith("class "):
                                        continue
                                    
                                    data_to_write.append([
                                        layer_name,
                                        metric_name,
                                        metric_name,
                                        float(area_value),
                                        self.unit_mapping.get(metric_name, "km²"),
                                        cls,
                                        class_name,
                                    ])
                            
                            elif metric_name == "Nearest Neighbour Distance":
                                for cls, distance in value.items():
                                    original_label = land_cover_mapping.get(cls, f"Class {cls}")
                                    if isinstance(original_label, str) and " - " in original_label:
                                        class_name = original_label.split(" - ", 1)[1].strip()
                                    else:
                                        class_name = str(original_label)
                                    
                                    if class_name.lower().startswith("class "):
                                        continue
                                    
                                    data_to_write.append([
                                        layer_name,
                                        metric_name,
                                        "Nearest Neighbour Distance",
                                        float(distance),
                                        self.unit_mapping.get("Nearest Neighbour Distance", "km"),
                                        cls,
                                        class_name,
                                    ])
                            
                            elif metric_name == "Number of Patches":
                                for cls, count_val in value.items():
                                    original_label = land_cover_mapping.get(cls, f"Class {cls}")
                                    if isinstance(original_label, str) and " - " in original_label:
                                        class_name = original_label.split(" - ", 1)[1].strip()
                                    else:
                                        class_name = str(original_label)
                                    
                                    if class_name.lower().startswith("class "):
                                        continue
                                    
                                    data_to_write.append([
                                        layer_name,
                                        metric_name,
                                        "Patch Count",
                                        int(count_val),
                                        "patches",
                                        cls,
                                        class_name,
                                    ])
                            
                            elif metric_name in ["Patch Cohesion Index", "Splitting Index"]:
                                for cls, index_val in value.items():
                                    original_label = land_cover_mapping.get(cls, f"Class {cls}")
                                    if isinstance(original_label, str) and " - " in original_label:
                                        class_name = original_label.split(" - ", 1)[1].strip()
                                    else:
                                        class_name = str(original_label)
                                    
                                    if class_name.lower().startswith("class "):
                                        continue
                                    
                                    data_to_write.append([
                                        layer_name,
                                        metric_name,
                                        metric_name,
                                        float(index_val),
                                        self.unit_mapping.get(metric_name, "Index"),
                                        cls,
                                        class_name,
                                    ])
                            
                            else:
                                # Generic dict handling
                                data_to_write.append([
                                    layer_name,
                                    metric_name,
                                    "Raw Dict Output",
                                    str(value),
                                    "N/A",
                                    None,
                                    None,
                                ])
                        
                        elif isinstance(value, (int, float)):
                            unit = "patches" if metric_name in ["NumberOfPatches", "Number of Patches"] else default_unit
                            data_to_write.append([
                                layer_name,
                                metric_name,
                                "TOTAL Value",
                                value,
                                unit,
                                None,
                                None,
                            ])
                        
                        else:
                            data_to_write.append([
                                layer_name,
                                metric_name,
                                "Raw Output",
                                str(value),
                                "N/A",
                                None,
                                None,
                            ])
                    
                    except Exception as e:
                        data_to_write.append([
                            layer_name,
                            metric_name,
                            "ERROR",
                            f"Calculation Failed: {str(e)}",
                            "N/A",
                            None,
                            None,
                        ])
                        self.error.emit(f"Error calculating {metric_name} for {layer_name}: {str(e)}")
                
                metric_data[layer_name] = layer_metrics
            
            self.progress.emit(100, "Calculation complete!")
            self.finished_calculation.emit(data_to_write, metric_data)
            
        except Exception as e:
            self.error.emit(f"Fatal error during calculation: {str(e)}")


class ExcelExportWorker(QThread):
    """
    Worker thread for exporting data to Excel in the background.
    
    Signals:
        progress: Emitted when progress updates (int: 0-100, str: status message)
        finished_export: Emitted when export completes (str: output path)
        error: Emitted when an error occurs (str: error message)
    """
    
    progress = pyqtSignal(int, str)
    finished_export = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, data_to_write, headers, output_path, parent=None):
        """
        Initialize the worker.
        
        Args:
            data_to_write: List of data rows to write
            headers: List of column headers
            output_path: Path to save Excel file
            parent: Parent QObject
        """
        super().__init__(parent)
        self.data_to_write = data_to_write
        self.headers = headers
        self.output_path = output_path
        self._is_cancelled = False
        
    def cancel(self):
        """Cancel the running export."""
        self._is_cancelled = True
        
    def run(self):
        """Execute the export in background thread."""
        try:
            self.progress.emit(10, "Creating Excel workbook...")
            
            if self._is_cancelled:
                return
            
            workbook = xlsxwriter.Workbook(self.output_path)
            worksheet = workbook.add_worksheet("Metric Results")
            
            self.progress.emit(20, "Formatting Excel worksheet...")
            
            # Create formats
            header_format = workbook.add_format({
                "bold": True,
                "border": 1,
                "bg_color": "#AEC6E3",
                "align": "center",
                "valign": "vcenter"
            })
            numeric_format = workbook.add_format({"num_format": "0.00", "align": "left"})
            general_format = workbook.add_format({"align": "left"})
            
            # Set column widths
            worksheet.set_column("A:A", 25)
            worksheet.set_column("B:B", 25)
            worksheet.set_column("C:C", 35)
            worksheet.set_column("D:D", 15, numeric_format)
            worksheet.set_column("E:E", 15)
            worksheet.set_column("F:F", 12)
            worksheet.set_column("G:G", 30)
            
            self.progress.emit(30, "Writing headers...")
            worksheet.write_row("A1", self.headers, header_format)
            
            if self._is_cancelled:
                workbook.close()
                return
            
            # Write data rows with progress updates
            total_rows = len(self.data_to_write)
            for idx, row_data in enumerate(self.data_to_write):
                if self._is_cancelled:
                    workbook.close()
                    return
                
                # Update progress every 10% of rows
                if idx % max(1, total_rows // 10) == 0:
                    progress_percent = 30 + int((idx / total_rows) * 60)
                    self.progress.emit(progress_percent, f"Writing row {idx + 1} of {total_rows}...")
                
                row_num = idx + 1
                layer_name, metric_name, detail, value, unit, class_id, class_name = row_data
                
                worksheet.write(row_num, 0, layer_name)
                worksheet.write(row_num, 1, metric_name)
                worksheet.write(row_num, 2, detail)
                worksheet.write(row_num, 4, unit)
                
                if class_id is not None:
                    try:
                        worksheet.write(row_num, 5, int(class_id))
                    except Exception:
                        worksheet.write(row_num, 5, str(class_id))
                        
                if class_name is not None:
                    worksheet.write(row_num, 6, class_name)
                
                if isinstance(value, (int, float)):
                    worksheet.write(row_num, 3, value, numeric_format)
                else:
                    worksheet.write(row_num, 3, str(value), general_format)
            
            self.progress.emit(95, "Finalizing Excel file...")
            workbook.close()
            
            self.progress.emit(100, "Export complete!")
            self.finished_export.emit(self.output_path)
            
        except xlsxwriter.exceptions.FileCreateError as e:
            self.error.emit(f"Cannot create Excel file. Please close the file if it is open: {self.output_path}")
        except Exception as e:
            self.error.emit(f"Unexpected error during Excel export: {str(e)}")


