"""Repros for three multidimensional VRT findings (2026-10-28).

Run: python notes/2026-10-28-mdim-vrt-repro.py
Needs GDAL Python bindings (osgeo), numpy, xarray, netCDF4, and the `gdal`
CLI on PATH. Writes into a temporary directory.

1. Strided read across sources fails ("arrayStartIdx[0] = N >= 1"); the CLI
   prints ERROR, exits 0 and writes fill values.
2. gdalvrt.xsd types mdim <BlockSize> as a space-separated integerList; the
   driver only parses comma-separated.
3. dataAxisToSRSAxisMapping: absent means identity (1,2), which on a
   (time, y, x) array maps an SRS axis to time; a 2D slice of such an array
   then reports a mapping containing 0.
"""

import subprocess
import tempfile
from pathlib import Path

import numpy as np
import xarray as xr
from osgeo import gdal, osr

gdal.UseExceptions()
tmp = Path(tempfile.mkdtemp(prefix="mdim-vrt-repro-"))
print("GDAL", gdal.__version__, "| workdir", tmp)


def try_print(label, f):
    try:
        print(f"  {label}: {f()}")
    except Exception as e:  # noqa: BLE001
        print(f"  {label}: ERROR {e}")


# -- 1. strided read across sources ------------------------------------------

print("\n1. strided read across sources")
n = 6
paths = []
for i in range(n):
    p = tmp / f"d{i}.nc"
    xr.Dataset({"v": (("t", "y", "x"), np.full((1, 3, 4), i, "int16"))}).to_netcdf(p)
    paths.append(p)
srcs = "".join(
    f'<Source><SourceFilename>{p}</SourceFilename><SourceArray>/v</SourceArray>'
    f'<DestSlab offset="{i},0,0"/></Source>'
    for i, p in enumerate(paths)
)
vrt = tmp / "a.vrt"
vrt.write_text(
    f'<VRTDataset><Group name="/"><Dimension name="t" size="{n}"/>'
    '<Dimension name="y" size="3"/><Dimension name="x" size="4"/>'
    '<Array name="v"><DataType>Int16</DataType><DimensionRef ref="t"/>'
    f'<DimensionRef ref="y"/><DimensionRef ref="x"/>{srcs}</Array></Group></VRTDataset>'
)
ds = gdal.OpenEx(str(vrt), gdal.OF_MULTIDIM_RASTER)
a = ds.GetRootGroup().OpenMDArray("v")


def read(start, count, step):
    return a.ReadAsArray(array_start_idx=[start, 0, 0], count=[count, 1, 1],
                         array_step=[step, 1, 1]).ravel().tolist()


try_print("step 1 across sources (expect [0..5])", lambda: read(0, 6, 1))
try_print("step 2 across sources (expect [0, 2, 4])", lambda: read(0, 3, 2))
try_print("step 3 across sources (expect [0, 3])", lambda: read(0, 2, 3))

one = tmp / "one.nc"
xr.Dataset({"v": (("t", "y", "x"),
                  (np.arange(6, dtype="int16")[:, None, None] * np.ones((1, 3, 4), "int16")))}).to_netcdf(one)
b = gdal.OpenEx(str(one), gdal.OF_MULTIDIM_RASTER).GetRootGroup().OpenMDArray("v")
try_print("step 2 within one source (expect [0, 2, 4])",
          lambda: b.ReadAsArray(array_start_idx=[0, 0, 0], count=[3, 1, 1],
                                array_step=[2, 1, 1]).ravel().tolist())

print("  CLI: gdal mdim convert --array 'name=v,view=[::2,...]' a.vrt o.nc")
out = tmp / "o.nc"
r = subprocess.run(["gdal", "mdim", "convert", "--overwrite", "--array",
                    "name=v,view=[::2,...]", str(vrt), str(out)],
                   capture_output=True, text=True)
print(f"    exit code {r.returncode}; stderr: {r.stderr.strip()[:80]!r}")
o = gdal.OpenEx(str(out), gdal.OF_MULTIDIM_RASTER).GetRootGroup().OpenMDArray("v")
print(f"    written values along t: {o.ReadAsArray()[:, 0, 0].tolist()} (expect [0, 2, 4])")

# -- 2. BlockSize: schema says spaces, driver wants commas ---------------------

print("\n2. mdim <BlockSize> separator")
for bs in ("1,3,4", "1 3 4"):
    txt = vrt.read_text().replace(
        '<DimensionRef ref="x"/><Source>',
        f'<DimensionRef ref="x"/><BlockSize>{bs}</BlockSize><Source>', 1)
    p = tmp / "bs.vrt"
    p.write_text(txt)
    try_print(f"<BlockSize>{bs}</BlockSize>",
              lambda: gdal.OpenEx(str(p), gdal.OF_MULTIDIM_RASTER)
              .GetRootGroup().OpenMDArray("v").GetBlockSize())
xsd = gdal.FindFile("gdal", "gdalvrt.xsd")
if xsd:
    import re
    text = Path(xsd).read_text()
    blocks = sorted(set(re.findall(r'name="BlockSize" type="(\w+)"', text)))
    lst = re.search(r'name="integerList">\s*<xs:list itemType="([^"]+)"', text)
    print(f"  {xsd}: BlockSize types {blocks}; integerList = xs:list of "
          f"{lst.group(1) if lst else '?'} (whitespace-separated)")
else:
    print("  gdalvrt.xsd not found in GDAL_DATA")

# -- 3. dataAxisToSRSAxisMapping on (time, y, x) -------------------------------

print("\n3. SRS axis mapping on a (t, y, x) array, EPSG:4326 WKT (lat first)")
srs = osr.SpatialReference()
srs.SetFromUserInput("EPSG:4326")
wkt = srs.ExportToWkt().replace('"', "&quot;")
for label, attr in (("absent", ""), ("'2,1'", ' dataAxisToSRSAxisMapping="2,1"'),
                    ("'2,3'", ' dataAxisToSRSAxisMapping="2,3"')):
    txt = vrt.read_text().replace(
        '<DimensionRef ref="x"/><Source>',
        f'<DimensionRef ref="x"/><SRS{attr}>{wkt}</SRS><Source>', 1)
    p = tmp / "srs.vrt"
    p.write_text(txt)
    d = gdal.OpenEx(str(p), gdal.OF_MULTIDIM_RASTER)
    arr = d.GetRootGroup().OpenMDArray("v")
    m3 = arr.GetSpatialRef().GetDataAxisToSRSAxisMapping()
    m2 = arr.GetView("[0,:,:]").AsClassicDataset(1, 0).GetSpatialRef().GetDataAxisToSRSAxisMapping()
    print(f"  attribute {label:7s}: 3D mapping {m3}, 2D slice mapping {m2}")
