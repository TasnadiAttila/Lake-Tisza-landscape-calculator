# -*- coding: utf-8 -*-
"""
GeoJSON exporter and web map generator for landscape metrics
"""

import json
import os
import webbrowser
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

try:
    from qgis.core import (
        QgsRasterLayer, 
        QgsProject, 
        QgsVectorLayer,
        QgsProcessingFeedback,
        QgsProcessingContext,
        QgsCoordinateTransform,
        QgsCoordinateReferenceSystem
    )
    import processing
except ImportError:
    # QGIS not available (for testing)
    QgsRasterLayer = object
    QgsProject = object
    QgsVectorLayer = object
    QgsProcessingFeedback = object
    QgsProcessingContext = object
    QgsCoordinateTransform = object
    QgsCoordinateReferenceSystem = object
    processing = None


class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler that suppresses logging"""
    def log_message(self, format, *args):
        pass  # Suppress logging


class GeoJSONExporter:
    """Exports raster data to GeoJSON format and generates interactive web maps"""
    
    _server_thread = None
    _server = None
    _server_port = 8000

    @staticmethod
    def start_local_server(directory):
        """Start a local HTTP server in a background thread to serve map files"""
        try:
            # Change to the target directory
            os.chdir(directory)
            
            # Create server
            GeoJSONExporter._server = HTTPServer(
                ('127.0.0.1', GeoJSONExporter._server_port),
                QuietHTTPRequestHandler
            )
            
            # Start server in background thread
            GeoJSONExporter._server_thread = threading.Thread(
                target=GeoJSONExporter._server.serve_forever,
                daemon=True
            )
            GeoJSONExporter._server_thread.start()
            print(f"Local HTTP server started at http://127.0.0.1:{GeoJSONExporter._server_port}")
            return True
        except OSError as e:
            # Port might be in use, try next port
            if GeoJSONExporter._server_port < 9000:
                GeoJSONExporter._server_port += 1
                return GeoJSONExporter.start_local_server(directory)
            print(f"Could not start local server: {e}")
            return False
        except Exception as e:
            print(f"Error starting local server: {e}")
            return False

    @staticmethod
    def generate_web_map(geojson_path, output_html_path, title="Landscape Metrics Map"):
        """
        Generate an interactive Leaflet web map from GeoJSON
        
        Args:
            geojson_path: Path to GeoJSON file
            output_html_path: Path to save HTML map
            title: Title for the map
        
        Returns:
            tuple: (html_path, port) if successful, (None, None) otherwise
        """
        try:
            print(f"[generate_web_map] Reading GeoJSON from: {geojson_path}")
            print(f"[generate_web_map] Output HTML path: {output_html_path}")
            
            # Read GeoJSON
            with open(geojson_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            print(f"[generate_web_map] GeoJSON loaded successfully")
            
            # Extract properties from first feature for basic logging
            layer_name = ""
            metric_value = ""

            if geojson_data.get("features"):
                props = geojson_data["features"][0].get("properties", {})
                layer_name = props.get("layer_name", "Unknown Layer")
                metric_value = props.get("metrics", "N/A")
                print(f"[generate_web_map] Layer: {layer_name}, Metrics: {metric_value}")
            
            # Convert GeoJSON to JSON string
            print(f"[generate_web_map] Converting GeoJSON to string...")
            geojson_str = json.dumps(geojson_data)
            print(f"[generate_web_map] GeoJSON string length: {len(geojson_str)}")
            
            # Create HTML content with Leaflet map (NOT using f-strings to avoid issues)
            html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>""" + title + """</title>
    
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.min.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.min.js"></script>
    
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background-color: #f5f5f5; 
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        
        /* Sidebar for filters */
        #sidebar {
            width: 350px;
            background: #ffffff;
            border-right: 2px solid #ddd;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        #sidebar-header {
            background: linear-gradient(135deg, #08519c 0%, #3182bd 100%);
            color: white;
            padding: 15px 20px;
            font-size: 18px;
            font-weight: bold;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        #sidebar-content {
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
        }
        
        .filter-section {
            padding: 15px 20px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .filter-section h2 {
            margin: 0 0 10px 0;
            font-size: 14px;
            color: #08519c;
            text-transform: uppercase;
            font-weight: 600;
        }
        
        .filter-section .actions {
            display: flex;
            gap: 6px;
            margin-bottom: 10px;
        }
        
        .filter-section button {
            font-size: 11px;
            padding: 5px 10px;
            border: 1px solid #3182bd;
            background: #ffffff;
            color: #3182bd;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .filter-section button:hover {
            background: #3182bd;
            color: white;
        }
        
        .option {
            display: flex;
            align-items: center;
            margin: 6px 0;
            font-size: 13px;
            color: #333;
            padding: 4px 0;
        }
        
        .option input {
            margin-right: 8px;
            cursor: pointer;
        }
        
        .option:hover {
            background: #f8f9fa;
        }

        .color-select {
            width: 100%;
            padding: 6px 8px;
            border: 1px solid #c9c9c9;
            border-radius: 4px;
            font-size: 12px;
            color: #333;
            background: #ffffff;
        }
        
        .summary {
            margin-top: 10px;
            font-size: 12px;
            color: #666;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        
        .empty {
            font-style: italic;
            color: #999;
            font-size: 12px;
        }
        
        /* Map container */
        #map-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }
        
        #map {
            flex: 1;
            width: 100%;
            height: 100%;
        }
        
        /* Results panel at bottom of map */
        #results-panel {
            background: white;
            border-top: 2px solid #ddd;
            max-height: 40vh;
            overflow: auto;
            display: none;
        }
        
        #results-panel.has-results {
            display: block;
        }
        
        .details {
            padding: 15px 20px;
        }
        
        .details .label {
            font-weight: bold;
            margin-bottom: 10px;
            color: #08519c;
            font-size: 14px;
            text-transform: uppercase;
        }
        
        .details table {
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
        }
        
        .details th,
        .details td {
            border: 1px solid #ddd;
            padding: 6px 8px;
            text-align: left;
        }
        
        .details th {
            background: #f2f6fb;
            color: #08519c;
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        
        .details tbody tr:hover {
            background: #f8f9fa;
        }
        
        /* Popup info */
        .info {
            padding: 8px 10px;
            font: 14px/16px Arial, Helvetica, sans-serif;
            background: rgba(255, 255, 255, 0.95);
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);
            border-radius: 5px;
        }
        
        .info h4 {
            margin: 0 0 8px 0;
            color: #08519c;
            font-weight: bold;
        }
        
        .info p {
            margin: 5px 0;
            font-size: 13px;
            color: #333;
        }
        
        /* Legend */
        .legend {
            line-height: 18px;
            color: #555;
            background: rgba(255, 255, 255, 0.95);
            padding: 8px 10px;
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);
            border-radius: 5px;
        }
        
        .legend h4 {
            margin: 0 0 8px 0;
            color: #08519c;
            font-size: 13px;
            font-weight: bold;
        }
        
        .legend i {
            width: 18px;
            height: 18px;
            float: left;
            margin-right: 8px;
            opacity: 0.8;
        }
        
        .legend .legend-item {
            font-size: 11px;
            margin: 3px 0;
            clear: both;
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
    </style>
</head>
<body>
    <!-- Sidebar for filters -->
    <div id="sidebar">
        <div id="sidebar-header">Lake Tisza Metrics</div>
        <div id="sidebar-content">
            <div class="filter-section">
                <h2>Layers</h2>
                <div class="actions">
                    <button type="button" id="layers-all">Select All</button>
                    <button type="button" id="layers-none">Clear All</button>
                </div>
                <div id="layer-list" class="option-list"></div>
            </div>
            
            <div class="filter-section">
                <h2>Metrics</h2>
                <div class="actions">
                    <button type="button" id="metrics-all">Select All</button>
                    <button type="button" id="metrics-none">Clear All</button>
                </div>
                <div id="metric-list" class="option-list"></div>
            </div>

            <div class="filter-section">
                <h2>Map Coloring</h2>
                <select id="color-metric-select" class="color-select"></select>
            </div>
            
            <div class="filter-section">
                <div class="summary" id="panel-summary"></div>
            </div>
            
            <div class="filter-section" id="layer-summary-section" style="display:none; border-top: 2px solid #08519c;">
                <h2>Selected Layer Metrics</h2>
                <div id="layer-summary-content" style="font-size: 12px;"></div>
            </div>
        </div>
    </div>
    
    <!-- Map container -->
    <div id="map-container">
        <div id="map"></div>
        <div id="results-panel">
            <div class="details">
                <div class="label">Patch Details</div>
                <div class="empty">Select layers to see individual patches.</div>
            </div>
        </div>
    </div>
    
    <script>
        var map = L.map('map').setView([47.5, 19.0], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19,
            minZoom: 2
        }).addTo(map);
        
        var geojsonFeature = GEOJSON_PLACEHOLDER;
        var geojsonLayer = null;
        var legendControl = null;

        function getColor(value, min, max) {
            if (value === null || value === undefined || isNaN(value)) {
                return '#cccccc';
            }
            if (min === max) {
                return '#fee08b';
            }
            var normalized = (value - min) / (max - min);
            var colors = [
                '#ffffcc',
                '#ffeda0',
                '#fed976',
                '#feb24c',
                '#fd8d3c',
                '#fc4e2a',
                '#e31a1c',
                '#bd0026'
            ];
            var index = Math.floor(normalized * (colors.length - 1));
            index = Math.max(0, Math.min(colors.length - 1, index));
            return colors[index];
        }

        function getMetricValueRange(selectedLayers, metricName) {
            var values = [];
            if (!geojsonFeature || !geojsonFeature.features || !metricName) {
                return { min: 0, max: 0 };
            }
            for (var i = 0; i < geojsonFeature.features.length; i++) {
                var feature = geojsonFeature.features[i];
                var props = feature.properties || {};
                if (selectedLayers.length && selectedLayers.indexOf(props.layer_name) === -1) {
                    continue;
                }
                var value = null;
                
                // Check for patch_area first if that's the metric
                if (metricName === 'Patch Area (km²)' && props.patch_area) {
                    value = props.patch_area;
                } else {
                    var metrics = normalizeMetrics(props);
                    if (Object.prototype.hasOwnProperty.call(metrics, metricName)) {
                        value = parseFloat(metrics[metricName]);
                    }
                }
                
                if (value !== null && !isNaN(value)) {
                    values.push(value);
                }
            }
            if (!values.length) {
                return { min: 0, max: 0 };
            }
            return { min: Math.min.apply(null, values), max: Math.max.apply(null, values) };
        }

        function createLegend(metricName, min, max) {
            if (legendControl) {
                map.removeControl(legendControl);
                legendControl = null;
            }
            if (!metricName || min === max) {
                return;
            }
            
            legendControl = L.control({ position: 'bottomright' });
            legendControl.onAdd = function(map) {
                var div = L.DomUtil.create('div', 'legend');
                div.innerHTML = '<h4>' + metricName + '</h4>';
                var steps = 8;
                for (var i = steps - 1; i >= 0; i--) {
                    var value = min + (max - min) * i / (steps - 1);
                    var color = getColor(value, min, max);
                    div.innerHTML +=
                        '<div class="legend-item"><i style="background:' + color + '"></i> ' +
                        value.toFixed(2) + '</div>';
                }
                return div;
            };
            legendControl.addTo(map);
        }

        function normalizeMetrics(props) {
            if (props.metrics_map) {
                return props.metrics_map;
            }
            if (props.metrics) {
                var parsed = {};
                var parts = props.metrics.split(',');
                for (var i = 0; i < parts.length; i++) {
                    var piece = parts[i].trim();
                    if (!piece) { continue; }
                    var kv = piece.split(':');
                    if (kv.length >= 2) {
                        var key = kv[0].trim();
                        var value = kv.slice(1).join(':').trim();
                        parsed[key] = value;
                    }
                }
                return parsed;
            }
            return {};
        }

        function collectUniqueValues(getter) {
            var values = {};
            if (!geojsonFeature || !geojsonFeature.features) { return []; }
            for (var i = 0; i < geojsonFeature.features.length; i++) {
                var value = getter(geojsonFeature.features[i]);
                if (value) { values[value] = true; }
            }
            return Object.keys(values).sort();
        }

        function collectMetricNames() {
            var values = {};
            if (!geojsonFeature || !geojsonFeature.features) { return []; }
            for (var i = 0; i < geojsonFeature.features.length; i++) {
                var metrics = normalizeMetrics(geojsonFeature.features[i].properties || {});
                for (var key in metrics) {
                    if (Object.prototype.hasOwnProperty.call(metrics, key)) {
                        values[key] = true;
                    }
                }
            }
            return Object.keys(values).sort();
        }

        function renderOptions(containerId, values, prefix) {
            var container = document.getElementById(containerId);
            container.innerHTML = '';
            if (!values.length) {
                var empty = document.createElement('div');
                empty.className = 'empty';
                empty.textContent = 'None available';
                container.appendChild(empty);
                return;
            }
            values.forEach(function(value) {
                var wrapper = document.createElement('label');
                wrapper.className = 'option';
                var input = document.createElement('input');
                input.type = 'checkbox';
                input.checked = false;
                input.value = value;
                input.id = prefix + value;
                input.addEventListener('change', updateMap);
                var span = document.createElement('span');
                span.textContent = value;
                wrapper.appendChild(input);
                wrapper.appendChild(span);
                container.appendChild(wrapper);
            });
        }

        function renderColorMetricSelector(values) {
            var select = document.getElementById('color-metric-select');
            if (!select) { return; }
            select.innerHTML = '';

            var options = ['Patch Area (km²)'].concat(values || []);
            for (var i = 0; i < options.length; i++) {
                var option = document.createElement('option');
                option.value = options[i];
                option.textContent = options[i];
                select.appendChild(option);
            }
        }

        function getColorMetric() {
            var select = document.getElementById('color-metric-select');
            if (!select || !select.value) {
                return 'Patch Area (km²)';
            }
            return select.value;
        }

        function setAllOptions(containerId, checked) {
            var container = document.getElementById(containerId);
            if (!container) { return; }
            var inputs = container.querySelectorAll('input[type="checkbox"]');
            for (var i = 0; i < inputs.length; i++) {
                inputs[i].checked = checked;
            }
            updateMap();
        }

        function getSelectedValues(containerId) {
            var container = document.getElementById(containerId);
            var selected = [];
            if (!container) { return selected; }
            var inputs = container.querySelectorAll('input[type="checkbox"]');
            for (var i = 0; i < inputs.length; i++) {
                if (inputs[i].checked) { selected.push(inputs[i].value); }
            }
            return selected;
        }

        function buildFilteredFeatureCollection(selectedLayers) {
            if (!geojsonFeature || !geojsonFeature.features) { return geojsonFeature; }
            var filtered = geojsonFeature.features.filter(function(feature) {
                var name = feature.properties ? feature.properties.layer_name : '';
                return selectedLayers.indexOf(name) !== -1;
            });
            return {
                type: 'FeatureCollection',
                features: filtered,
                crs: geojsonFeature.crs
            };
        }

        function buildMetricsHtml(metrics, selectedMetrics) {
            var items = [];
            for (var key in metrics) {
                if (Object.prototype.hasOwnProperty.call(metrics, key)) {
                    if (!selectedMetrics.length || selectedMetrics.indexOf(key) !== -1) {
                        items.push('<div><strong>' + key + ':</strong> ' + metrics[key] + '</div>');
                    }
                }
            }
            if (!items.length) {
                return '<div class="empty">No metrics selected</div>';
            }
            return items.join('');
        }

        function updateSummary(selectedLayers, selectedMetrics) {
            var layerText = selectedLayers.length ? selectedLayers.length + ' layer(s)' : 'no layers';
            var metricText = selectedMetrics.length ? selectedMetrics.length + ' metric(s)' : 'no metrics';
            var summary = 'Showing ' + layerText + ', ' + metricText + '.';
            
            // Add which metric is being used for coloring
            if (selectedLayers.length > 0) {
                var colorMetric = getColorMetric();
                summary += '<br><strong>Map colors by:</strong> ' + colorMetric;
            }
            
            var panelSummary = document.getElementById('panel-summary');
            if (panelSummary) { panelSummary.innerHTML = summary; }
            
            // Update layer summary section
            var layerSummarySection = document.getElementById('layer-summary-section');
            var layerSummaryContent = document.getElementById('layer-summary-content');
            
            if (selectedLayers.length > 0 && selectedMetrics.length > 0) {
                layerSummarySection.style.display = 'block';
                
                var summaryHtml = '';
                for (var i = 0; i < selectedLayers.length; i++) {
                    var layerName = selectedLayers[i];
                    summaryHtml += '<div style="margin-bottom: 12px; padding: 8px; background: #f8f9fa; border-radius: 4px;">';
                    summaryHtml += '<strong style="color: #08519c;">' + layerName + '</strong><br>';
                    
                    // Find this layer's metrics
                    var layerFound = false;
                    for (var j = 0; j < geojsonFeature.features.length; j++) {
                        var feature = geojsonFeature.features[j];
                        var props = feature.properties || {};
                        if (props.layer_name === layerName) {
                            var metrics = normalizeMetrics(props);
                            
                            for (var k = 0; k < selectedMetrics.length; k++) {
                                var metricName = selectedMetrics[k];
                                if (Object.prototype.hasOwnProperty.call(metrics, metricName)) {
                                    summaryHtml += '<span style="color: #666;">' + metricName + ':</span> <strong>' + metrics[metricName] + '</strong><br>';
                                }
                            }
                            layerFound = true;
                            break;
                        }
                    }
                    
                    if (!layerFound) {
                        summaryHtml += '<span style="color: #999; font-style: italic;">No metrics found</span>';
                    }
                    
                    summaryHtml += '</div>';
                }
                
                layerSummaryContent.innerHTML = summaryHtml;
            } else {
                layerSummarySection.style.display = 'none';
            }
        }

        function updateDetails(selectedLayers, selectedMetrics) {
            var panel = document.getElementById('results-panel');
            if (!panel) { return; }
            if (!selectedLayers.length) {
                panel.innerHTML = '<div class="details"><div class="label">Patch Details</div>' +
                    '<div class="empty">Select at least one layer to see patch details.</div></div>';
                panel.classList.remove('has-results');
                return;
            }

            // Build metrics to display (include Patch Area by default)
            var metricsToShow = ['Patch Area (km²)'];
            for (var m = 0; m < selectedMetrics.length; m++) {
                if (selectedMetrics[m] !== 'Patch Area (km²)') {
                    metricsToShow.push(selectedMetrics[m]);
                }
            }

            var rows = [];
            var headerCells = '<th>Layer</th><th>Patch #</th>';
            for (var h = 0; h < metricsToShow.length; h++) {
                headerCells += '<th>' + metricsToShow[h] + '</th>';
            }

            // Group features by layer
            var layerPatches = {};
            for (var i = 0; i < geojsonFeature.features.length; i++) {
                var feature = geojsonFeature.features[i];
                var props = feature.properties || {};
                var layerName = props.layer_name;
                
                if (selectedLayers.indexOf(layerName) === -1) {
                    continue;
                }
                
                if (!layerPatches[layerName]) {
                    layerPatches[layerName] = [];
                }
                layerPatches[layerName].push(props);
            }

            for (var l = 0; l < selectedLayers.length; l++) {
                var layerName = selectedLayers[l];
                var patches = layerPatches[layerName] || [];
                
                if (patches.length === 0) {
                    continue;
                }

                for (var p = 0; p < patches.length; p++) {
                    var props = patches[p];
                    var metrics = normalizeMetrics(props);
                    
                    var rowCells = '<td>' + layerName + '</td>';
                    rowCells += '<td>' + (p + 1) + '</td>';
                    
                    for (var k = 0; k < metricsToShow.length; k++) {
                        var metricName = metricsToShow[k];
                        var value = '-';
                        
                        if (metricName === 'Patch Area (km²)' && props.patch_area) {
                            value = props.patch_area.toFixed(4);
                        } else if (Object.prototype.hasOwnProperty.call(metrics, metricName)) {
                            value = metrics[metricName];
                        }
                        
                        rowCells += '<td>' + value + '</td>';
                    }
                    rows.push('<tr>' + rowCells + '</tr>');
                }
            }

            if (!rows.length) {
                panel.innerHTML = '<div class="details"><div class="label">Patch Details</div>' +
                    '<div class="empty">No patches found for selected layers.</div></div>';
                panel.classList.remove('has-results');
                return;
            }

            var summary = '<div style="margin-top:10px; padding-top:10px; border-top:1px solid #e0e0e0; font-size:12px; color:#666;">Total: ' + rows.length + ' patch(es)</div>';
            
            panel.innerHTML = '<div class="details"><div class="label">Patch Details</div>' +
                '<table><thead><tr>' + headerCells + '</tr></thead>' +
                '<tbody>' + rows.join('') + '</tbody></table>' + summary + '</div>';
            panel.classList.add('has-results');
        }

        function updateResultsWidth(selectedMetrics) {
            // No longer needed with new layout - results panel takes full width
        }

        function updateUrl(selectedLayers, selectedMetrics) {
            var params = new URLSearchParams();
            if (selectedLayers.length) {
                params.set('layers', selectedLayers.join(','));
            }
            if (selectedMetrics.length) {
                params.set('metrics', selectedMetrics.join(','));
            }
            var query = params.toString();
            var newUrl = window.location.pathname + (query ? '?' + query : '');
            window.history.replaceState({}, '', newUrl);
        }

        function parseSelections(paramValue) {
            if (!paramValue) { return null; }
            try {
                var decoded = decodeURIComponent(paramValue);
                if (!decoded) { return []; }
                return decoded.split(',').filter(function(item) { return item !== ''; });
            } catch (err) {
                return null;
            }
        }

        function applyInitialSelections() {
            var params = new URLSearchParams(window.location.search);
            var layerParam = params.get('layers');
            var metricParam = params.get('metrics');
            var selectedLayers = parseSelections(layerParam);
            var selectedMetrics = parseSelections(metricParam);

            if (selectedLayers !== null) {
                setAllOptions('layer-list', false);
                var layerInputs = document.getElementById('layer-list').querySelectorAll('input[type="checkbox"]');
                for (var i = 0; i < layerInputs.length; i++) {
                    if (selectedLayers.indexOf(layerInputs[i].value) !== -1) {
                        layerInputs[i].checked = true;
                    }
                }
            }

            if (selectedMetrics !== null) {
                setAllOptions('metric-list', false);
                var metricInputs = document.getElementById('metric-list').querySelectorAll('input[type="checkbox"]');
                for (var j = 0; j < metricInputs.length; j++) {
                    if (selectedMetrics.indexOf(metricInputs[j].value) !== -1) {
                        metricInputs[j].checked = true;
                    }
                }
            }
        }

        function updateMap() {
            var selectedLayers = getSelectedValues('layer-list');
            var selectedMetrics = getSelectedValues('metric-list');
            updateSummary(selectedLayers, selectedMetrics);
            updateUrl(selectedLayers, selectedMetrics);
            updateDetails(selectedLayers, selectedMetrics);

            if (geojsonLayer) {
                map.removeLayer(geojsonLayer);
            }

            var filtered = buildFilteredFeatureCollection(selectedLayers);
            
            // Use the selected metric for coloring, or default to Patch Area
            var colorMetric = getColorMetric();
            var range = getMetricValueRange(selectedLayers, colorMetric);
            
            if (range.min !== range.max) {
                createLegend(colorMetric, range.min, range.max);
            } else {
                if (legendControl) {
                    map.removeControl(legendControl);
                    legendControl = null;
                }
            }
            
            geojsonLayer = L.geoJSON(filtered, {
                style: function(feature) {
                    var fillColor = '#08519c';
                    var props = feature.properties || {};
                    var metrics = normalizeMetrics(props);
                    
                    // Try to get the color metric value
                    var value = null;
                    if (Object.prototype.hasOwnProperty.call(metrics, colorMetric)) {
                        value = parseFloat(metrics[colorMetric]);
                    } else if (props.patch_area && colorMetric === 'Patch Area (km²)') {
                        value = props.patch_area;
                    }
                    
                    if (value !== null && !isNaN(value) && range.min !== range.max) {
                        fillColor = getColor(value, range.min, range.max);
                    }
                    
                    return { 
                        color: '#333', 
                        weight: 1.5, 
                        opacity: 0.8, 
                        fillColor: fillColor, 
                        fillOpacity: 0.7 
                    };
                },
                onEachFeature: function(feature, layer) {
                    var props = feature.properties || {};
                    var metrics = normalizeMetrics(props);
                    var metricsHtml = buildMetricsHtml(metrics, selectedMetrics);
                    
                    // Add patch area if available
                    var patchInfo = '';
                    if (props.patch_area) {
                        patchInfo = '<div><strong>Patch Area:</strong> ' + props.patch_area.toFixed(4) + ' km²</div>';
                    }
                    
                    var popupContent = '<div class="info">' +
                        '<h4>' + (props.layer_name || 'Layer') + '</h4>' +
                        '<div><strong>CRS:</strong> ' + (props.crs || '-') + '</div>' +
                        patchInfo +
                        '<div style="margin-top:6px;">' + metricsHtml + '</div></div>';
                    layer.bindPopup(popupContent);
                }
            }).addTo(map);

            if (geojsonLayer.getBounds && geojsonLayer.getBounds().isValid()) {
                map.fitBounds(geojsonLayer.getBounds());
            }
        }

        var layerNames = collectUniqueValues(function(feature) {
            return feature.properties ? feature.properties.layer_name : '';
        });
        var metricNames = collectMetricNames();
        renderOptions('layer-list', layerNames, 'layer_');
        renderOptions('metric-list', metricNames, 'metric_');
        renderColorMetricSelector(metricNames);
        applyInitialSelections();
        document.getElementById('layers-all').addEventListener('click', function() {
            setAllOptions('layer-list', true);
        });
        document.getElementById('layers-none').addEventListener('click', function() {
            setAllOptions('layer-list', false);
        });
        document.getElementById('metrics-all').addEventListener('click', function() {
            setAllOptions('metric-list', true);
        });
        document.getElementById('metrics-none').addEventListener('click', function() {
            setAllOptions('metric-list', false);
        });
        document.getElementById('color-metric-select').addEventListener('change', updateMap);
        updateMap();
        L.control.scale().addTo(map);
    </script>
</body>
</html>
"""
            
            # Replace placeholder with actual GeoJSON
            html_content = html_content.replace('GEOJSON_PLACEHOLDER', geojson_str)
            
            # Write HTML file
            print(f"[generate_web_map] Writing HTML file to: {output_html_path}")
            with open(output_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Verify file exists
            if os.path.exists(output_html_path):
                file_size = os.path.getsize(output_html_path)
                print(f"[generate_web_map] HTML file created successfully, size: {file_size} bytes")
                return output_html_path, GeoJSONExporter._server_port
            else:
                print(f"[generate_web_map] ERROR: HTML file was not created!")
                return None, None
            
        except Exception as e:
            print(f"[generate_web_map] Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None, None

    @staticmethod
    def vectorize_raster_patches(layer):
        """
        Vectorize raster to extract individual patch geometries
        
        Args:
            layer: QgsRasterLayer object
            
        Returns:
            list: List of dictionaries with 'geometry' and 'area' keys
        """
        try:
            if processing is None:
                print("[vectorize_raster_patches] QGIS processing not available")
                return []
            
            feedback = QgsProcessingFeedback()
            context = QgsProcessingContext()
            
            temp_folder = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp")
            if not os.path.exists(temp_folder):
                os.makedirs(temp_folder)
            
            polygon_output = os.path.join(temp_folder, f"temp_vectorize_{layer.name()}.gpkg")
            
            print(f"[vectorize_raster_patches] Vectorizing layer: {layer.name()}")
            
            # Vectorize raster to polygons
            processing.run(
                "gdal:polygonize",
                {
                    'INPUT': layer.source(),
                    'BAND': 1,
                    'FIELD': 'VALUE',
                    'EIGHT_CONNECTEDNESS': False,
                    'OUTPUT': polygon_output
                },
                feedback=feedback,
                context=context
            )
            
            polygon_layer = QgsVectorLayer(polygon_output, "temp_polygons", "ogr")
            if not polygon_layer.isValid():
                print(f"[vectorize_raster_patches] Invalid polygon layer")
                return []
            
            # Get nodata value
            provider = layer.dataProvider()
            nodata = provider.sourceNoDataValue(1)
            
            # Extract patches with their geometries
            patches = []
            source_crs = polygon_layer.crs()
            target_crs = QgsCoordinateReferenceSystem("EPSG:4326")
            transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())
            
            for feature in polygon_layer.getFeatures():
                value = feature["VALUE"]
                
                # Skip nodata and background (0 or negative)
                if nodata is not None and value == nodata:
                    continue
                if value <= 0:
                    continue
                
                geom = feature.geometry()
                if geom and not geom.isEmpty():
                    # Transform to WGS84
                    geom.transform(transform)
                    area_km2 = feature.geometry().area() / 1e6  # Original area in km²
                    
                    # Convert geometry to GeoJSON format
                    geom_json = json.loads(geom.asJson())
                    
                    patches.append({
                        'geometry': geom_json,
                        'area': area_km2,
                        'class_value': value
                    })
            
            print(f"[vectorize_raster_patches] Extracted {len(patches)} patches from {layer.name()}")
            
            # Clean up temp file
            try:
                if os.path.exists(polygon_output):
                    os.remove(polygon_output)
            except:
                pass
            
            return patches
            
        except Exception as e:
            print(f"[vectorize_raster_patches] Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def export_and_generate_map(layers, metric_data, output_dir):
        """
        Export layers with metric data to GeoJSON and generate web map
        
        Args:
            layers: List of QgsRasterLayer objects
            metric_data: Dictionary with metric information
            output_dir: Output directory for GeoJSON and HTML files
        
        Returns:
            tuple: (geojson_path, html_url) if successful, (None, None) otherwise
        """
        try:
            print(f"[export_and_generate_map] Starting export to: {output_dir}")
            
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Create GeoJSON file
            base_name = f"landscape_metrics_{len(layers)}_layers"
            geojson_path = os.path.join(output_dir, f"{base_name}.geojson")
            html_path = os.path.join(output_dir, f"{base_name}_map.html")
            html_filename = os.path.basename(html_path)
            
            # Combine all layers and metrics into one GeoJSON
            features = []
            crs_info = "EPSG:4326"
            
            for layer in layers:
                print(f"[export_and_generate_map] Processing layer: {layer.name()}")
                
                crs = layer.crs()
                if crs:
                    crs_info = crs.authid() if crs.authid() else "EPSG:4326"
                
                # Get metric info for this layer
                layer_metrics = metric_data.get(layer.name(), {})
                
                # Vectorize raster to get patch geometries
                patches = GeoJSONExporter.vectorize_raster_patches(layer)
                
                if patches:
                    # Create a feature for each patch
                    for patch in patches:
                        # Create metrics map for this patch
                        patch_metrics = {
                            "Patch Area (km²)": round(patch['area'], 4)
                        }
                        # Add layer-level metrics for reference
                        for metric_name, metric_value in layer_metrics.items():
                            patch_metrics[f"Layer {metric_name}"] = metric_value
                        
                        metric_desc = ", ".join([f"{k}: {v}" for k, v in patch_metrics.items()])
                        
                        feature = {
                            "type": "Feature",
                            "geometry": patch['geometry'],
                            "properties": {
                                "layer_name": layer.name(),
                                "patch_area": patch['area'],
                                "class_value": patch['class_value'],
                                "metrics": metric_desc,
                                "metrics_map": patch_metrics,
                                "metrics_list": list(patch_metrics.keys()),
                                "crs": crs_info
                            }
                        }
                        features.append(feature)
                else:
                    # Fallback to bounding box if vectorization fails
                    print(f"[export_and_generate_map] No patches extracted, using bounding box for {layer.name()}")
                    extent = layer.extent()
                    metric_desc = ", ".join([f"{k}: {v}" for k, v in layer_metrics.items()])
                    
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [extent.xMinimum(), extent.yMinimum()],
                                [extent.xMaximum(), extent.yMinimum()],
                                [extent.xMaximum(), extent.yMaximum()],
                                [extent.xMinimum(), extent.yMaximum()],
                                [extent.xMinimum(), extent.yMinimum()]
                            ]]
                        },
                        "properties": {
                            "layer_name": layer.name(),
                            "metrics": metric_desc,
                            "metrics_map": layer_metrics,
                            "metrics_list": list(layer_metrics.keys()),
                            "crs": crs_info
                        }
                    }
                    features.append(feature)
            
            # Create FeatureCollection
            geojson_data = {
                "type": "FeatureCollection",
                "features": features,
                "crs": {
                    "type": "name",
                    "properties": {"name": crs_info}
                }
            }
            
            # Write GeoJSON
            print(f"[export_and_generate_map] Writing GeoJSON...")
            with open(geojson_path, 'w', encoding='utf-8') as f:
                json.dump(geojson_data, f, indent=2)
            
            # Generate web map
            print(f"[export_and_generate_map] Generating web map...")
            html_result = GeoJSONExporter.generate_web_map(
                geojson_path,
                html_path,
                "Lake Tisza Landscape Metrics"
            )
            
            if html_result[0]:
                # Start local server if not already running
                if GeoJSONExporter._server is None:
                    GeoJSONExporter.start_local_server(output_dir)
                
                # Return HTML URL for local server
                html_url = f"http://127.0.0.1:{GeoJSONExporter._server_port}/{html_filename}"
                print(f"[export_and_generate_map] Success! URL: {html_url}")
                return geojson_path, html_url
            
            return None, None
            
        except Exception as e:
            print(f"[export_and_generate_map] Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None, None
