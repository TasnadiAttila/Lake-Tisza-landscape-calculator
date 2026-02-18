# -*- coding: utf-8 -*-
"""
CSV exporter for landscape metrics
Exports calculation results in tidy data format for easy analysis
"""

import csv
import os


class CSVExporter:
    """Exports landscape metrics to CSV format in tidy data structure"""
    
    @staticmethod
    def export_to_csv(data_to_write, output_path, headers):
        """
        Export metric data to CSV file in tidy format
        
        Args:
            data_to_write: List of row data (list of lists)
            output_path: Path to save CSV file
            headers: List of column headers
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure .csv extension
            if not output_path.lower().endswith('.csv'):
                output_path = output_path.replace('.xlsx', '.csv')
                if not output_path.lower().endswith('.csv'):
                    output_path += '.csv'
            
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(headers)
                
                # Write data rows
                for row in data_to_write:
                    # Convert any non-string values to strings
                    cleaned_row = []
                    for cell in row:
                        if cell is None or cell == '':
                            cleaned_row.append('')
                        elif isinstance(cell, (int, float)):
                            # Format numbers with reasonable precision
                            if isinstance(cell, float):
                                cleaned_row.append(f"{cell:.6f}".rstrip('0').rstrip('.'))
                            else:
                                cleaned_row.append(str(cell))
                        else:
                            cleaned_row.append(str(cell))
                    
                    writer.writerow(cleaned_row)
            
            return True
            
        except Exception as e:
            print(f"[CSVExporter] Error exporting to CSV: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def export_summary_csv(metric_data, output_path):
        """
        Export a summary CSV with layer-level metrics (aggregated view)
        
        Args:
            metric_data: Dictionary with structure {layer_name: {metric_name: value}}
            output_path: Path to save summary CSV file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create summary filename
            base_path = output_path.replace('.csv', '_summary.csv')
            if not base_path.lower().endswith('.csv'):
                base_path += '_summary.csv'
            
            # Collect all unique metrics across layers
            all_metrics = set()
            for layer_metrics in metric_data.values():
                all_metrics.update(layer_metrics.keys())
            
            all_metrics = sorted(all_metrics)
            
            with open(base_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header: Layer Name, Metric1, Metric2, ...
                headers = ['Layer Name'] + all_metrics
                writer.writerow(headers)
                
                # Write one row per layer
                for layer_name in sorted(metric_data.keys()):
                    row = [layer_name]
                    layer_metrics = metric_data[layer_name]
                    
                    for metric_name in all_metrics:
                        value = layer_metrics.get(metric_name, '')
                        row.append(value)
                    
                    writer.writerow(row)
            
            return True
            
        except Exception as e:
            print(f"[CSVExporter] Error exporting summary CSV: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def export_wide_format_csv(data_to_write, output_path):
        """
        Export metrics in wide format (one row per layer, metrics as columns)
        Useful for statistical analysis and data visualization
        
        Args:
            data_to_write: List of row data from metric calculations
            output_path: Path to save wide-format CSV file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create wide format filename
            base_path = output_path.replace('.csv', '_wide.csv')
            if not base_path.lower().endswith('.csv'):
                base_path += '_wide.csv'
            
            # Parse data into structured format
            # Expected structure: [Layer, Metric, Detail, Value, Unit, ClassID, ClassName]
            layer_data = {}
            
            for row in data_to_write:
                if len(row) < 7:
                    continue
                
                layer_name = row[0]
                metric_name = row[1]
                detail = row[2]
                value = row[3]
                unit = row[4]
                class_id = row[5] if len(row) > 5 else ''
                class_name = row[6] if len(row) > 6 else ''
                
                # Create unique column name
                if class_name:
                    col_name = f"{metric_name}_{class_name}"
                elif detail and detail != '-':
                    col_name = f"{metric_name}_{detail}"
                else:
                    col_name = metric_name
                
                # Initialize layer if not exists
                if layer_name not in layer_data:
                    layer_data[layer_name] = {}
                
                # Store value with unit
                display_value = f"{value} {unit}" if unit and unit != 'N/A' else str(value)
                layer_data[layer_name][col_name] = display_value
            
            # Collect all columns
            all_columns = set()
            for layer_metrics in layer_data.values():
                all_columns.update(layer_metrics.keys())
            
            all_columns = sorted(all_columns)
            
            with open(base_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                headers = ['Layer Name'] + all_columns
                writer.writerow(headers)
                
                # Write data rows
                for layer_name in sorted(layer_data.keys()):
                    row = [layer_name]
                    metrics = layer_data[layer_name]
                    
                    for col in all_columns:
                        value = metrics.get(col, '')
                        row.append(value)
                    
                    writer.writerow(row)
            
            return True
            
        except Exception as e:
            print(f"[CSVExporter] Error exporting wide-format CSV: {e}")
            import traceback
            traceback.print_exc()
            return False
