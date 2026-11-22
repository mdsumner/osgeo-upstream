#!/usr/bin/env python3
"""Offline repro for notes/2026-11-11-rasterize-nodata-warp-avoidnodata.md (no network, synthetic data).

  1. gdal_rasterize creating its output, without -a_nodata: is a nodata value set on the bands?
     (with and without -init; and with -a_nodata 255 as the control)
  1b. the same through the `gdal vector rasterize` CLI (GDAL >= 3.11), which builds gdal_rasterize
     options and calls GDALRasterize(): no --nodata, --init 0, and --nodata 255 as the control
  2. warp with destination nodata 0 of a uint8 0/1 image: valid 0s rewritten as 1 (AvoidNoData)
  3. if rasterio is importable: rasterio.warp.reproject(..., dst_nodata=0), what odc-geo's
     xr_reproject asks for a uint8 array with dst_nodata=None (it passes its fill value 0)

  python 2026-11-11-rasterize-nodata-warp-avoidnodata-repro.py
"""
import json
import os
import shutil
import subprocess
import tempfile

import numpy as np
from osgeo import gdal, ogr, osr

gdal.UseExceptions()
out = {"gdal": gdal.__version__}

# a square polygon covering the left half of a 100 x 100 grid
srs = osr.SpatialReference()
srs.ImportFromEPSG(3031)
vds = gdal.GetDriverByName("Memory").Create("", 0, 0, 0, gdal.GDT_Unknown) if int(gdal.__version__.split(".")[1]) < 11 \
    else gdal.GetDriverByName("MEM").CreateVector("")
lyr = vds.CreateLayer("p", srs, ogr.wkbPolygon)
f = ogr.Feature(lyr.GetLayerDefn())
f.SetGeometry(ogr.CreateGeometryFromWkt("POLYGON ((0 0, 50 0, 50 100, 0 100, 0 0))"))
lyr.CreateFeature(f)
kw = dict(outputBounds=(0, 0, 100, 100), width=100, height=100, outputType=gdal.GDT_Byte, burnValues=[1])

# 1. nodata on a created output
item1 = {}
for label, extra in (("no -a_nodata, no -init", {}), ("no -a_nodata, -init 0", {"initValues": [0]}),
                     ("-a_nodata 255 (control)", {"noData": 255})):
    ds = gdal.Rasterize("/vsimem/r.tif", vds, **kw, **extra)
    item1[label] = ds.GetRasterBand(1).GetNoDataValue()
    mask = ds.ReadAsArray()
    ds = None
    gdal.Unlink("/vsimem/r.tif")
out["1_rasterize_created_output_nodata"] = item1
out["1_burnt_cells"] = int((mask == 1).sum())

# 1b. gdal vector rasterize (the gdal CLI, 3.11+)
gdal_cli = shutil.which("gdal")
if gdal_cli and int(gdal.__version__.split(".")[1]) >= 11:
    tmp = tempfile.mkdtemp()
    shp = os.path.join(tmp, "p.geojson")
    gdal.VectorTranslate(shp, vds, format="GeoJSON")
    item1b = {}
    for label, extra in (("no --nodata, no --init", []), ("no --nodata, --init 0", ["--init", "0"]),
                         ("--nodata 255 (control)", ["--nodata", "255"])):
        tif = os.path.join(tmp, "r.tif")
        if os.path.exists(tif):
            os.remove(tif)
        cmd = [gdal_cli, "vector", "rasterize", "--burn", "1", "--extent", "0,0,100,100", "--size", "100,100",
               "--ot", "Byte", *extra, shp, tif]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode:
            item1b[label] = "error: " + p.stderr.strip()[-300:]
            continue
        ds = gdal.Open(tif)
        item1b[label] = dict(nodata=ds.GetRasterBand(1).GetNoDataValue(),
                             burnt=int((ds.ReadAsArray() == 1).sum()))
        ds = None
    out["1b_gdal_vector_rasterize_nodata"] = item1b
    shutil.rmtree(tmp)
else:
    out["1b_gdal_vector_rasterize_nodata"] = "no gdal CLI (GDAL < 3.11)"

# 2. warp, destination nodata 0
src = gdal.GetDriverByName("MEM").Create("", 100, 100, 1, gdal.GDT_Byte)
src.SetGeoTransform((0, 1, 0, 100, 0, -1))
src.SetSpatialRef(srs)
a = np.zeros((100, 100), "uint8")
a[:, 50:] = 1
src.GetRasterBand(1).WriteArray(a)
msgs = []
gdal.PushErrorHandler(lambda cls, no, msg: msgs.append(msg))
item2 = {}
for nd in (None, 0):
    msgs.clear()
    r = gdal.Warp("", src, format="MEM", width=10, height=10, resampleAlg="near", dstNodata=nd,
                  warpOptions=["XSCALE=1", "YSCALE=1"]).ReadAsArray()
    item2[f"dstNodata={nd}"] = dict(zeros=int((r == 0).sum()), ones=int((r == 1).sum()), warnings=list(msgs))
gdal.PopErrorHandler()
out["2_warp_dst_nodata_0"] = item2

# 3. rasterio, if present
try:
    import rasterio
    import rasterio.warp
    from rasterio.transform import from_origin
    item3 = {"rasterio": rasterio.__version__, "rasterio_gdal": rasterio.__gdal_version__}
    for nd in (None, 0):
        dst = np.zeros((10, 10), "uint8")
        rasterio.warp.reproject(a, dst, src_transform=from_origin(0, 100, 1, 1), dst_transform=from_origin(0, 100, 10, 10),
                                src_crs="EPSG:3031", dst_crs="EPSG:3031", resampling=rasterio.warp.Resampling.nearest,
                                src_nodata=None, dst_nodata=nd, XSCALE=1, YSCALE=1)
        item3[f"dst_nodata={nd}"] = dict(zeros=int((dst == 0).sum()), ones=int((dst == 1).sum()))
    out["3_rasterio_reproject"] = item3
except ImportError:
    out["3_rasterio_reproject"] = "rasterio not installed"
print(json.dumps(out, indent=1))
