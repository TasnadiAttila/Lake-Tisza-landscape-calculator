import xlsxwriter
import subprocess
import sys

class ExcelHelper:
    #TODO: Remove or update messageBar
    @staticmethod
    def ensureXlsxwriterInstalled(self):
        try:
            import xlsxwriter
        except ModuleNotFoundError:
            self.iface.messageBar().pushMessage(
                "Info",
                "xlsxwriter nincs telepítve, telepítés...",
                level=Qgis.Info,
                duration=5
            )
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "xlsxwriter"])
            import xlsxwriter

    @staticmethod
    def createOutputExcelFile(filePath):
        wb = xlsxwriter.Workbook(filePath)
        ws = wb.add_worksheet()
        wb.close()
