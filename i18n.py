# -*- coding: utf-8 -*-
"""Tiny ES/EN translation helper based on the QGIS user locale."""
from qgis.PyQt.QtCore import QSettings

_LANG = None

STRINGS = {
    "tooltip": {"en": "DEM-o-gorgon: flip a DEM into the upside down",
                "es": "DEM-o-gorgon: dale la vuelta a un DEM"},
    "title": {"en": "DEM-o-gorgon", "es": "DEM-o-gorgon"},
    "layer": {"en": "DEM layer", "es": "Capa DEM"},
    "band": {"en": "Band", "es": "Banda"},
    "mode": {"en": "Flip around", "es": "Dar la vuelta respecto a"},
    "mode_range": {"en": "Min + max (keeps the value range)",
                   "es": "Mínimo + máximo (mantiene el rango de valores)"},
    "mode_sea": {"en": "Sea level (0): land becomes sea and vice versa",
                 "es": "Nivel del mar (0): la tierra pasa a mar y al revés"},
    "mode_custom": {"en": "Custom elevation", "es": "Cota personalizada"},
    "style": {"en": "Style", "es": "Estilo"},
    "hillshade": {"en": "Add hillshade", "es": "Añadir sombreado"},
    "output": {"en": "Output (empty = temporary file)",
               "es": "Salida (vacío = archivo temporal)"},
    "run": {"en": "Flip it!", "es": "¡Dale la vuelta!"},
    "close": {"en": "Close", "es": "Cerrar"},
    "hint": {"en": "Flipping the result again with the same settings gives back the original DEM.",
             "es": "Si vuelves a dar la vuelta al resultado con los mismos ajustes, recuperas el DEM original."},
    "err_layer": {"en": "Pick a raster layer read from a file (GDAL).",
                  "es": "Elige una capa ráster leída desde archivo (GDAL)."},
    "err_empty": {"en": "The band has no valid values.",
                  "es": "La banda no tiene valores válidos."},
    "err_generic": {"en": "Something went wrong: {msg}", "es": "Algo ha fallado: {msg}"},
    "done": {"en": "Done. Welcome to the upside down.",
             "es": "Hecho. Bienvenido al mundo del revés."},
    "suffix": {"en": "upside down", "es": "del revés"},
    "suffix_hs": {"en": "hillshade", "es": "sombreado"},
    "geo_warn": {"en": "Geographic CRS: hillshade uses an approximate z factor (1/111320). Reproject to a metric CRS for accurate relief.",
                 "es": "CRS geográfico: el sombreado usa un factor z aproximado (1/111320). Reproyecta a un CRS métrico si quieres un relieve fiel."},
}


def lang():
    global _LANG
    if _LANG is None:
        loc = QSettings().value("locale/userLocale", "en") or "en"
        _LANG = "es" if str(loc).lower().startswith("es") else "en"
    return _LANG


def t(key, **kwargs):
    text = STRINGS.get(key, {}).get(lang(), key)
    return text.format(**kwargs) if kwargs else text
