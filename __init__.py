# -*- coding: utf-8 -*-
"""DEM-o-gorgon: QGIS plugin entry point."""


def classFactory(iface):
    from .dem_o_gorgon import DemOGorgon
    return DemOGorgon(iface)
