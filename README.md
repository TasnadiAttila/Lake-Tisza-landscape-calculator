OSGeo4W Shell -> python -m pip install xlsxwriter
OSGeo4W is installed alongside QGIS

## Architecture

The plugin now follows a lightweight MVC split:

- Model: `tisza_to_tajmetria/Models/plugin_model.py`
	- Stores calculation state and domain constants (units, export headers)
	- Provides layer renderer/land cover mapping extraction
- View: `tisza_to_tajmetria/Views/main_dialog_view.py`
	- Owns Qt dialog widget interactions and UI state updates
	- Combobox-specific UI behavior is in `tisza_to_tajmetria/Views/combo_box_view_helper.py`
- Controller: `tisza_to_tajmetria/Controllers/plugin_controller.py`
	- Handles user actions, background workers, and message flow
- Services: `tisza_to_tajmetria/Services/`
	- `dependency_service.py`: runtime dependency checks/install helpers
	- `export_service.py`: CSV/GeoJSON/map export orchestration APIs
	- `csv_exporter.py` and `geojson_exporter.py`: exporter implementations
- App entry: `tisza_to_tajmetria/tisza_to_tajmetria.py`
	- Keeps only QGIS plugin lifecycle and delegates runtime logic to controller
