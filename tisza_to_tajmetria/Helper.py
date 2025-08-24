from qgis.core import QgsProject

class ComboBoxHandler:
    def add_clear_button_to_combobox(combobox):
        """Add clear button and search functionality to combobox"""
        combobox.setEditable(True)
        combobox.lineEdit().setClearButtonEnabled(True)
        combobox.lineEdit().setPlaceholderText("Search...")
        
    
    def load_layers_to_combobox(combobox, layer_types=None):
        """Load layers to combobox with optional type filtering"""
        
        if layer_types is None:
            layer_types = ['raster', 'vector']
        
        combobox.clear()
        
        layers = QgsProject.instance().mapLayers().values()
        filtered_layers = []
        
        for layer in layers:
            if ('raster' in layer_types and layer.type() == layer.RasterLayer) or \
               ('vector' in layer_types and layer.type() == layer.VectorLayer):
                filtered_layers.append(layer)
        
        for layer in filtered_layers:
            combobox.addItem(layer.name(), layer)
        
        if combobox.count() == 0:
            combobox.addItem("No available layers")
        
        return combobox