# -*- coding: utf-8 -*-

from ..Controllers.excel_helper import ExcelHelper


class DependencyService:
    @staticmethod
    def ensure_xlsxwriter_installed(iface=None):
        class _Ctx:
            def __init__(self, qgis_iface):
                self.iface = qgis_iface

        ExcelHelper.ensure_xlsxwriter_installed(_Ctx(iface))
