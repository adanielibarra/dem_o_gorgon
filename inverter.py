# -*- coding: utf-8 -*-
"""Raster inversion with GDAL + numpy, processed in row blocks."""
import numpy as np

OUT_NODATA = float(np.finfo(np.float32).min)
BLOCK_ROWS = 512


def invert_values(arr, mode, pivot=0.0, vmin=None, vmax=None):
    """Mirror elevations.

    mode "range": z' = min + max - z (keeps the same value range).
    mode "pivot": z' = 2 * pivot - z (mirror around one elevation; pivot 0 = sea level).
    Both are their own inverse: applying them twice returns the original values.
    """
    if mode == "range":
        return (vmin + vmax) - arr
    return 2.0 * pivot - arr


def invert_raster(src_path, dst_path, mode, pivot=0.0, band_index=1, progress=None):
    """Write the inverted band to a Float32 GeoTIFF. Returns (min, max) of the output."""
    from osgeo import gdal

    src = gdal.Open(src_path, gdal.GA_ReadOnly)
    if src is None:
        raise RuntimeError("GDAL cannot open: " + src_path)
    band = src.GetRasterBand(band_index)
    nodata = band.GetNoDataValue()

    vmin = vmax = None
    if mode == "range":
        vmin, vmax = band.ComputeRasterMinMax(False)

    xs, ys = src.RasterXSize, src.RasterYSize
    drv = gdal.GetDriverByName("GTiff")
    dst = drv.Create(dst_path, xs, ys, 1, gdal.GDT_Float32,
                     options=["COMPRESS=LZW", "TILED=YES", "BIGTIFF=IF_SAFER"])
    dst.SetGeoTransform(src.GetGeoTransform())
    dst.SetProjection(src.GetProjection())
    out_band = dst.GetRasterBand(1)
    out_band.SetNoDataValue(OUT_NODATA)

    out_min, out_max = np.inf, -np.inf
    for y0 in range(0, ys, BLOCK_ROWS):
        rows = min(BLOCK_ROWS, ys - y0)
        a = band.ReadAsArray(0, y0, xs, rows).astype(np.float64)
        mask = np.isnan(a)
        if nodata is not None and not np.isnan(nodata):
            mask |= (a == nodata)
        out = invert_values(a, mode, pivot, vmin, vmax)
        valid = out[~mask]
        if valid.size:
            out_min = min(out_min, float(valid.min()))
            out_max = max(out_max, float(valid.max()))
        out[mask] = OUT_NODATA
        out_band.WriteArray(out.astype(np.float32), 0, y0)
        if progress:
            progress(100.0 * (y0 + rows) / ys)

    out_band.FlushCache()
    dst = None
    src = None
    if not np.isfinite(out_min):
        return None, None
    return out_min, out_max
