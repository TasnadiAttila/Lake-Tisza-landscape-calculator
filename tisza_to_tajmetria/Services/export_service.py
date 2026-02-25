# -*- coding: utf-8 -*-

import os
import webbrowser

from .csv_exporter import CSVExporter
from .geojson_exporter import GeoJSONExporter


class ExportService:
    @staticmethod
    def export_csv_bundle(calculation_data, metric_data, base_output_path, headers):
        export_paths = []

        csv_path = (
            base_output_path.replace('.xlsx', '')
            if base_output_path.lower().endswith('.xlsx')
            else base_output_path
        )
        csv_path = csv_path + '.csv' if not csv_path.lower().endswith('.csv') else csv_path

        success = CSVExporter.export_to_csv(calculation_data, csv_path, headers)
        if success:
            export_paths.append(f"CSV: {os.path.basename(csv_path)}")

        CSVExporter.export_summary_csv(metric_data, csv_path)
        summary_csv = csv_path.replace('.csv', '_summary.csv')
        if os.path.exists(summary_csv):
            export_paths.append(f"Summary CSV: {os.path.basename(summary_csv)}")

        CSVExporter.export_wide_format_csv(calculation_data, csv_path)
        wide_csv = csv_path.replace('.csv', '_wide.csv')
        if os.path.exists(wide_csv):
            export_paths.append(f"Wide CSV: {os.path.basename(wide_csv)}")

        return export_paths

    @staticmethod
    def export_map_bundle(selected_layers, metric_data, base_output_path, open_in_browser=True):
        export_paths = []
        output_dir = os.path.dirname(base_output_path) or "."

        geojson_path, html_url = GeoJSONExporter.export_and_generate_map(
            selected_layers,
            metric_data,
            output_dir,
        )

        if geojson_path:
            export_paths.append(f"GeoJSON: {os.path.basename(geojson_path)}")

        if geojson_path and html_url:
            export_paths.append(f"Map: {html_url}")
            if open_in_browser:
                webbrowser.open(html_url)

        return export_paths
