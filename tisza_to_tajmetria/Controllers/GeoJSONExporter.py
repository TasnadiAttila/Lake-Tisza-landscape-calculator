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
    from qgis.core import QgsRasterLayer, QgsProject
except ImportError:
    # QGIS not available (for testing)
    QgsRasterLayer = object
    QgsProject = object


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
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; }
        #map { position: absolute; top: 0; bottom: 0; width: 100%; height: 100vh; }
        .info { padding: 6px 8px; font: 14px/16px Arial, Helvetica, sans-serif; background: rgba(255,255,255,0.8); box-shadow: 0 0 15px rgba(0,0,0,0.2); border-radius: 5px; }
        .info h4 { margin: 0 0 5px 0; color: #08519c; font-weight: bold; }
        .info p { margin: 5px 0; font-size: 13px; color: #333; }
        .panel-wrap { position: fixed; top: 10px; left: 10px; right: 10px; z-index: 1000; display: flex; gap: 12px; align-items: flex-start; }
        .panel { padding: 12px 14px; background: rgba(255,255,255,0.95); box-shadow: 0 0 15px rgba(0,0,0,0.2); border-radius: 5px; width: 320px; max-height: 80vh; overflow: auto; }
        .panel.results { width: 520px; overflow-x: auto; overflow-y: auto; }
        .panel h2 { margin: 10px 0 6px 0; font-size: 14px; color: #08519c; }
        .panel .actions { display: flex; gap: 6px; margin-bottom: 6px; }
        .panel button { font-size: 11px; padding: 4px 8px; border: 1px solid #c9c9c9; background: #f7f7f7; border-radius: 4px; cursor: pointer; }
        .panel button:hover { background: #efefef; }
        .panel .option { display: flex; align-items: center; margin: 4px 0; font-size: 12px; color: #333; }
        .panel .option input { margin-right: 6px; }
        .panel .summary { margin-top: 8px; font-size: 12px; color: #666; border-top: 1px solid #ddd; padding-top: 6px; }
        .panel .empty { font-style: italic; color: #888; }
        .panel .details { margin-top: 8px; font-size: 12px; color: #333; border-top: 1px solid #ddd; padding-top: 6px; }
        .panel .details .label { font-weight: bold; margin-bottom: 4px; color: #08519c; }
        .panel .details table { width: 100%; border-collapse: collapse; font-size: 11px; }
        .panel .details th, .panel .details td { border: 1px solid #ddd; padding: 4px 6px; text-align: left; }
        .panel .details th { background: #f2f6fb; color: #08519c; }
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="panel-wrap">
        <div class="panel">
            <h2>Layers</h2>
            <div class="actions">
                <button type="button" id="layers-all">Select all</button>
                <button type="button" id="layers-none">Clear all</button>
            </div>
            <div id="layer-list" class="option-list"></div>
            <h2>Metrics</h2>
            <div class="actions">
                <button type="button" id="metrics-all">Select all</button>
                <button type="button" id="metrics-none">Clear all</button>
            </div>
            <div id="metric-list" class="option-list"></div>
            <div class="summary" id="panel-summary"></div>
        </div>

        <div class="panel results" id="selection-details">
            <div class="details">
                <div class="label">Selected values</div>
                <div class="empty">Select at least one layer and one metric.</div>
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
            var summary = layerText + ', ' + metricText;
            var panelSummary = document.getElementById('panel-summary');
            if (panelSummary) { panelSummary.textContent = 'Showing ' + summary + '.'; }
        }

        function updateDetails(selectedLayers, selectedMetrics) {
            var details = document.getElementById('selection-details');
            if (!details) { return; }
            if (!selectedLayers.length || !selectedMetrics.length) {
                details.innerHTML = '<div class="details"><div class="label">Selected values</div>' +
                    '<div class="empty">Select at least one layer and one metric.</div></div>';
                return;
            }

            var rows = [];
            var headerCells = '<th>Layer</th>';
            for (var m = 0; m < selectedMetrics.length; m++) {
                headerCells += '<th>' + selectedMetrics[m] + '</th>';
            }

            for (var i = 0; i < selectedLayers.length; i++) {
                var layerName = selectedLayers[i];
                var match = null;
                for (var j = 0; j < geojsonFeature.features.length; j++) {
                    var feature = geojsonFeature.features[j];
                    var props = feature.properties || {};
                    if (props.layer_name === layerName) {
                        match = props;
                        break;
                    }
                }

                if (!match) { continue; }
                var metrics = normalizeMetrics(match);
                var rowCells = '<td>' + layerName + '</td>';
                for (var k = 0; k < selectedMetrics.length; k++) {
                    var metricName = selectedMetrics[k];
                    var hasMetric = Object.prototype.hasOwnProperty.call(metrics, metricName);
                    var value = hasMetric ? metrics[metricName] : '-';
                    rowCells += '<td>' + value + '</td>';
                }
                rows.push('<tr>' + rowCells + '</tr>');
            }

            if (!rows.length) {
                details.innerHTML = '<div class="details"><div class="label">Selected values</div>' +
                    '<div class="empty">No matching layer found.</div></div>';
                return;
            }

            details.innerHTML = '<div class="details"><div class="label">Selected values</div>' +
                '<table><thead><tr>' + headerCells + '</tr></thead>' +
                '<tbody>' + rows.join('') + '</tbody></table></div>';
        }

        function updateResultsWidth(selectedMetrics) {
            var panel = document.getElementById('selection-details');
            if (!panel) { return; }
            var count = selectedMetrics.length || 0;
            var baseWidth = 360;
            var perMetric = 120;
            var desired = baseWidth + (count * perMetric);
            var maxWidth = Math.max(360, window.innerWidth - 380);
            var width = Math.min(desired, maxWidth);
            panel.style.width = width + 'px';
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
            updateResultsWidth(selectedMetrics);

            if (geojsonLayer) {
                map.removeLayer(geojsonLayer);
            }

            var filtered = buildFilteredFeatureCollection(selectedLayers);
            geojsonLayer = L.geoJSON(filtered, {
                style: function(feature) {
                    return { color: '#08519c', weight: 2, opacity: 0.65, fillColor: '#08519c', fillOpacity: 0.1 };
                },
                onEachFeature: function(feature, layer) {
                    var props = feature.properties || {};
                    var metrics = normalizeMetrics(props);
                    var metricsHtml = buildMetricsHtml(metrics, selectedMetrics);
                    var popupContent = '<div class="info">' +
                        '<h4>' + (props.layer_name || 'Layer') + '</h4>' +
                        '<div><strong>CRS:</strong> ' + (props.crs || '-') + '</div>' +
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
                extent = layer.extent()
                crs = layer.crs()
                if crs:
                    crs_info = crs.authid() if crs.authid() else "EPSG:4326"
                
                # Get metric info for this layer
                layer_metrics = metric_data.get(layer.name(), {})
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
