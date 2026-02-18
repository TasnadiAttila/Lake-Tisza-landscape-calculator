import xlsxwriter
import subprocess
import sys

try:
    from qgis.core import Qgis
except ImportError:
    # QGIS not available (for testing)
    Qgis = None


class ExcelHelper:
    @staticmethod
    def ensureXlsxwriterInstalled(self):
        try:
            import xlsxwriter
        except ModuleNotFoundError:
            if hasattr(self, 'iface') and self.iface:
                self.iface.messageBar().pushMessage(
                    "Info",
                    "xlsxwriter nincs telepítve, telepítés...",
                    level=Qgis.Info if Qgis else 1,
                    duration=5
                )
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "xlsxwriter"])
            import xlsxwriter

    @staticmethod
    def createOutputExcelFile(filePath):
        wb = xlsxwriter.Workbook(filePath)
        ws = wb.add_worksheet()
        wb.close()
