from qgis.core import QgsProject
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from tisza_to_tajmetria.Metrics.Metrics import Metrics


class ComboBoxHandler:
    """
    Egy segédosztály, amely QComboBox-okat kezel jelölőnégyzetekkel,
    élő kereséssel és a kiválasztott elemek szöveges megjelenítésével.
    """

    @staticmethod
    def addClearButtonToCombobox(combobox):
        """Beállítja a combobox-ot szerkeszthetővé és placeholder szöveget ad hozzá."""
        combobox.setEditable(True)
        combobox.lineEdit().setPlaceholderText("Keresés...")
        # A kurzor pozíciójának beállítása a szöveg elejére kattintáskor
        combobox.lineEdit().setCursorPosition(0)

    @staticmethod
    def loadLayersToCombobox(combobox, layer_types=None):
        """
        Betölti a QGIS rétegeket egy jelölőnégyzetekkel ellátott combobox-ba.
        """
        if layer_types is None:
            layer_types = ['raster']

        combobox.clear()
        layers = QgsProject.instance().mapLayers().values()
        model = QStandardItemModel(combobox)

        for layer in layers:
            if 'raster' in layer_types and layer.type() == layer.RasterLayer:
                item = QStandardItem(layer.name())
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                item.setData(Qt.Unchecked, Qt.CheckStateRole)
                item.setData(layer, Qt.UserRole)
                model.appendRow(item)

        if model.rowCount() == 0:
            item = QStandardItem("Nincsenek elérhető rétegek")
            item.setEnabled(False)
            model.appendRow(item)

        combobox.setModel(model)
        ComboBoxHandler._setup_common_features(combobox)
        return combobox

    @staticmethod
    def loadMetricsToCombobox(combobox):
        """
        Betölti a metrikákat egy jelölőnégyzetekkel ellátott combobox-ba.
        """
        combobox.clear()
        model = QStandardItemModel(combobox)

        for metric in Metrics:
            item = QStandardItem(metric.getMetricName)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item.setData(Qt.Unchecked, Qt.CheckStateRole)
            item.setData((metric.getMetricCalculation(), metric.getMetricName), Qt.UserRole)
            model.appendRow(item)

        combobox.setModel(model)
        ComboBoxHandler._setup_common_features(combobox)
        return combobox

    @staticmethod
    def _setup_common_features(combobox):
        """
        Beállítja a közös funkciókat (szűrés, szövegfrissítés, popup nyitva tartása)
        a combobox-on, miután a modell be lett állítva.
        """
        # A popup nyitva tartása kattintáskor
        ComboBoxHandler._keep_popup_open_on_click(combobox)

        # Szöveg frissítése, amikor egy elem állapota megváltozik
        combobox.model().itemChanged.connect(
            lambda: ComboBoxHandler._update_line_edit_text(combobox)
        )

        # A modell szűrése, amikor a keresési szöveg változik
        combobox.lineEdit().textChanged.connect(
            lambda text: ComboBoxHandler._filter_model(combobox, text)
        )

        # Kezdeti szöveg beállítása (általában üres)
        ComboBoxHandler._update_line_edit_text(combobox)

    @staticmethod
    def _keep_popup_open_on_click(combobox):
        """
        Felülírja a view egéresemény-kezelőjét, hogy a popup ne záródjon be
        egy elemre (szöveg vagy checkbox) való kattintáskor.
        """
        view = combobox.view()
        # Elmentjük az eredeti eseménykezelőt, ha még nem tettük meg
        if not hasattr(view, '_original_mouseReleaseEvent'):
            view._original_mouseReleaseEvent = view.mouseReleaseEvent

        # Új eseménykezelő
        def mouse_release_handler(event):
            index = view.indexAt(event.pos())
            # Csak akkor kezeljük, ha érvényes elemre kattintottak
            if index.isValid():
                item = combobox.model().itemFromIndex(index)
                if item and item.isEnabled():
                    # Állapot váltása
                    new_state = Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
                    item.setCheckState(new_state)
            else:
                # Ha nem elemre kattintottunk (pl. scrollbar), hívjuk az eredeti funkciót
                view._original_mouseReleaseEvent(event)

        view.mouseReleaseEvent = mouse_release_handler

    @staticmethod
    def _update_line_edit_text(combobox):
        """
        Frissíti a combobox lineEdit szövegét a kiválasztott elemek neveivel.
        """
        checked_items = []
        model = combobox.model()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item and item.checkState() == Qt.Checked:
                checked_items.append(item.text())

        # Ideiglenesen blokkoljuk a textChanged szignált, hogy elkerüljük a végtelen ciklust
        combobox.lineEdit().blockSignals(True)
        combobox.lineEdit().setText(", ".join(checked_items))
        combobox.lineEdit().blockSignals(False)

    @staticmethod
    def _filter_model(combobox, text):
        """
        Szűri a combobox legördülő listájának elemeit a lineEdit-be írt szöveg alapján.
        A szűrés figyelmen kívül hagyja a már kiválasztott elemeket, amelyek a szövegben
        vesszővel elválasztva szerepelnek.
        """
        # Ha a szöveg megegyezik a kipipált elemek listájával, ne szűrjünk.
        # Ez akkor fordul elő, amikor programból állítjuk be a szöveget.
        checked_texts = []
        model = combobox.model()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item and item.checkState() == Qt.Checked:
                checked_texts.append(item.text())

        if text == ", ".join(checked_texts):
            # Minden elemet mutassunk, ha a szöveg a kiválasztottak listája
            for i in range(model.rowCount()):
                combobox.view().setRowHidden(i, False)
            return

        # Valós felhasználói keresés
        search_term = text.lower()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item:
                item_text = item.text().lower()
                # Az elemet elrejtjük, ha a keresési kifejezés nem szerepel benne
                is_hidden = search_term not in item_text
                combobox.view().setRowHidden(i, is_hidden)

    @staticmethod
    def getCheckedItems(combobox):
        """
        Visszaadja a kiválasztott elemekhez tartozó adatokat (UserRole).
        """
        checked_items_data = []
        model = combobox.model()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item and item.checkState() == Qt.Checked:
                checked_items_data.append(item.data(Qt.UserRole))
        return checked_items_data