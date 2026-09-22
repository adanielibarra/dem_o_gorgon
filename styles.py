# -*- coding: utf-8 -*-
"""Colour presets and renderers."""
from qgis.core import (QgsColorRampShader, QgsRasterShader,
                       QgsSingleBandPseudoColorRenderer, QgsHillshadeRenderer)
from qgis.PyQt.QtGui import QColor, QPainter

# (fraction of the value range, colour)
PRESETS = {
    "1983": [(0.00, "#07070b"), (0.35, "#3a0a12"), (0.70, "#b3122a"),
             (0.90, "#ff3b4f"), (1.00, "#4b6a8a")],
    "Laboratorio / Lab": [(0.00, "#050a14"), (0.40, "#123a5a"),
                          (0.75, "#3f8fb5"), (1.00, "#d8f1ff")],
    "Walkie": [(0.00, "#020803"), (0.50, "#0f3d17"),
               (0.85, "#39d353"), (1.00, "#c8ffcf")],
}


def _enum(owner, scoped, flat):
    """Return an enum value that works on both Qt5 and Qt6 builds."""
    obj = owner
    try:
        for part in scoped.split("."):
            obj = getattr(obj, part)
        return obj
    except AttributeError:
        return getattr(owner, flat)


def apply_color(layer, preset, vmin, vmax):
    if vmax == vmin:
        vmax = vmin + 1.0
    items = [QgsColorRampShader.ColorRampItem(vmin + f * (vmax - vmin), QColor(c), "")
             for f, c in PRESETS[preset]]
    fn = QgsColorRampShader(vmin, vmax)
    fn.setColorRampType(_enum(QgsColorRampShader, "Type.Interpolated", "Interpolated"))
    fn.setColorRampItemList(items)
    shader = QgsRasterShader()
    shader.setRasterShaderFunction(fn)
    renderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader)
    renderer.setClassificationMin(vmin)
    renderer.setClassificationMax(vmax)
    layer.setRenderer(renderer)


def apply_hillshade(layer, z_factor=1.0):
    renderer = QgsHillshadeRenderer(layer.dataProvider(), 1, 315.0, 35.0)
    renderer.setZFactor(z_factor)
    renderer.setMultiDirectional(True)
    layer.setRenderer(renderer)


def set_multiply(layer):
    layer.setBlendMode(_enum(QPainter, "CompositionMode.CompositionMode_Multiply",
                             "CompositionMode_Multiply"))
