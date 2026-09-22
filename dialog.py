# -*- coding: utf-8 -*-
"""Main dialog: options on the left, kitten logo on the right."""
import os
import tempfile

from qgis.core import QgsProject, QgsRasterLayer, QgsMapLayerProxyModel, Qgis
from qgis.gui import QgsMapLayerComboBox, QgsRasterBandComboBox, QgsFileWidget
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (QDialog, QHBoxLayout, QVBoxLayout, QFormLayout,
                                 QLabel, QRadioButton, QDoubleSpinBox, QComboBox,
                                 QCheckBox, QProgressBar, QPushButton, QMessageBox,
                                 QApplication, QButtonGroup, QWidget)

from .i18n import t
from .inverter import invert_raster
from .styles import PRESETS, apply_color, apply_hillshade, set_multiply, _enum

PLUGIN_DIR = os.path.dirname(__file__)


class DemOGorgonDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle(t("title"))
        self.setWindowIcon(QIcon(os.path.join(PLUGIN_DIR, "icon.svg")))
        self._build()

    # ---------- UI ----------
    def _build(self):
        form = QFormLayout()

        self.layer_combo = QgsMapLayerComboBox()
        raster_filter = _enum(Qgis, "LayerFilter.RasterLayer", "RasterLayer") \
            if hasattr(Qgis, "LayerFilter") else QgsMapLayerProxyModel.RasterLayer
        self.layer_combo.setFilters(raster_filter)
        form.addRow(t("layer"), self.layer_combo)

        self.band_combo = QgsRasterBandComboBox()
        self.band_combo.setLayer(self.layer_combo.currentLayer())
        self.layer_combo.layerChanged.connect(self.band_combo.setLayer)
        form.addRow(t("band"), self.band_combo)

        self.rb_range = QRadioButton(t("mode_range"))
        self.rb_sea = QRadioButton(t("mode_sea"))
        self.rb_custom = QRadioButton(t("mode_custom"))
        self.rb_range.setChecked(True)
        group = QButtonGroup(self)
        for rb in (self.rb_range, self.rb_sea, self.rb_custom):
            group.addButton(rb)
        self.pivot = QDoubleSpinBox()
        self.pivot.setRange(-12000.0, 9000.0)
        self.pivot.setDecimals(2)
        self.pivot.setSuffix(" m")
        self.pivot.setEnabled(False)
        self.rb_custom.toggled.connect(self.pivot.setEnabled)
        custom_row = QHBoxLayout()
        custom_row.addWidget(self.rb_custom)
        custom_row.addWidget(self.pivot)
        modes = QVBoxLayout()
        modes.addWidget(self.rb_range)
        modes.addWidget(self.rb_sea)
        modes.addLayout(custom_row)
        form.addRow(t("mode"), modes)

        self.style_combo = QComboBox()
        self.style_combo.addItems(list(PRESETS.keys()))
        form.addRow(t("style"), self.style_combo)

        self.hs_check = QCheckBox(t("hillshade"))
        self.hs_check.setChecked(True)
        form.addRow("", self.hs_check)

        self.out_widget = QgsFileWidget()
        self.out_widget.setStorageMode(_enum(QgsFileWidget, "StorageMode.SaveFile", "SaveFile"))
        self.out_widget.setFilter("GeoTIFF (*.tif *.tiff)")
        form.addRow(t("output"), self.out_widget)

        hint = QLabel(t("hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray;")

        self.progress = QProgressBar()
        self.progress.setValue(0)

        self.run_btn = QPushButton(t("run"))
        self.run_btn.clicked.connect(self.run)
        close_btn = QPushButton(t("close"))
        close_btn.clicked.connect(self.close)
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(close_btn)
        buttons.addWidget(self.run_btn)

        left = QVBoxLayout()
        left.addLayout(form)
        left.addWidget(hint)
        left.addWidget(self.progress)
        left.addLayout(buttons)
        left_widget = QWidget()
        left_widget.setLayout(left)

        # logo on the right
        logo = QLabel()
        logo.setPixmap(QIcon(os.path.join(PLUGIN_DIR, "icon.svg")).pixmap(180, 180))
        logo.setAlignment(_enum(Qt, "AlignmentFlag.AlignCenter", "AlignCenter"))

        main = QHBoxLayout()
        main.addWidget(left_widget, 1)
        main.addWidget(logo)
        self.setLayout(main)
        self.resize(640, 360)

    def refresh_layers(self):
        self.band_combo.setLayer(self.layer_combo.currentLayer())

    # ---------- logic ----------
    def _on_progress(self, value):
        self.progress.setValue(int(value))
        QApplication.processEvents()

    def run(self):
        layer = self.layer_combo.currentLayer()
        if layer is None or layer.providerType() != "gdal":
            QMessageBox.warning(self, t("title"), t("err_layer"))
            return
        src_path = layer.source().split("|")[0]
        band = self.band_combo.currentBand() or 1

        if self.rb_range.isChecked():
            mode, pivot = "range", 0.0
        elif self.rb_sea.isChecked():
            mode, pivot = "pivot", 0.0
        else:
            mode, pivot = "pivot", self.pivot.value()

        out_path = self.out_widget.filePath().strip()
        if not out_path:
            fd, out_path = tempfile.mkstemp(prefix="dem_o_gorgon_", suffix=".tif")
            os.close(fd)
            os.remove(out_path)
        elif not out_path.lower().endswith((".tif", ".tiff")):
            out_path += ".tif"

        self.run_btn.setEnabled(False)
        self.progress.setValue(0)
        try:
            vmin, vmax = invert_raster(src_path, out_path, mode, pivot, band,
                                       progress=self._on_progress)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, t("title"), t("err_generic", msg=str(exc)))
            self.run_btn.setEnabled(True)
            return
        self.run_btn.setEnabled(True)

        if vmin is None:
            QMessageBox.warning(self, t("title"), t("err_empty"))
            return

        self._add_layers(layer, out_path, vmin, vmax)

    def _add_layers(self, src_layer, out_path, vmin, vmax):
        name = "{} ({})".format(src_layer.name(), t("suffix"))
        project = QgsProject.instance()
        root = project.layerTreeRoot()
        group = root.insertGroup(0, "DEM-o-gorgon: " + src_layer.name())

        color = QgsRasterLayer(out_path, name)
        apply_color(color, self.style_combo.currentText(), vmin, vmax)
        project.addMapLayer(color, False)
        group.addLayer(color)

        if self.hs_check.isChecked():
            hill = QgsRasterLayer(out_path, "{} ({})".format(name, t("suffix_hs")))
            z_factor = 1.0
            if hill.crs().isGeographic():
                z_factor = 1.0 / 111320.0
                self.iface.messageBar().pushWarning(t("title"), t("geo_warn"))
            apply_hillshade(hill, z_factor)
            project.addMapLayer(hill, False)
            group.addLayer(hill)
            set_multiply(color)  # colour on top, multiplied over the hillshade

        color.triggerRepaint()
        self.iface.messageBar().pushSuccess(t("title"), t("done"))
