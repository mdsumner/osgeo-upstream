"""BRAN temp: GDAL's numcodecs.shuffle + numcodecs.zlib decode vs icechunk-python.

One 300 x 300 chunk (Time 0 = 1993-01-01, st_ocean 0, lat -15..15,
lon 150..180) of the BRAN2023 daily-temp Icechunk repo on source.coop, whose
virtual chunks live on NCI THREDDS. Read once through GDAL (/vsiicechunk/)
and once through icechunk-python + zarr-python; the int16 values must be
identical.

    python3 bran_crosscheck.py     # osgeo.gdal (build under test), icechunk, zarr
"""

import numpy as np
from osgeo import gdal

import icechunk as ic
import zarr

PREFIX = "ausantarctic/ausantarctic-scratch/bluelink/bluelink-daily-temp/icechunk"
START, COUNT = [0, 0, 600, 1500], [1, 1, 300, 300]

gdal.UseExceptions()
print(gdal.VersionInfo("--version"))
rg = gdal.OpenEx(
    "/vsiicechunk/{/vsicurl/https://data.source.coop/%s}" % PREFIX,
    gdal.OF_MULTIDIM_RASTER,
).GetRootGroup()
t = rg.OpenMDArray("temp")
a = t.ReadAsArray(array_start_idx=START, count=COUNT)

zarr.config.set({"async.concurrency": 4})  # THREDDS resets at the default 10
repo = ic.Repository.open(
    ic.s3_storage(bucket="us-west-2.opendata.source.coop", prefix=PREFIX,
                  region="us-west-2", anonymous=True),
    authorize_virtual_chunk_access={"https://thredds.nci.org.au/": None},
)
z = zarr.open_array(repo.readonly_session(branch="main").store, path="temp", mode="r")
b = z[tuple(slice(s, s + c) for s, c in zip(START, COUNT))]

print("identical:", np.array_equal(a, b), "differing cells:", int((a != b).sum()))
v = a[a != -32768].astype("f8") * t.GetScale() + t.GetOffset()
print("temp degC min/mean/max %.3f %.3f %.3f, fill cells %d"
      % (v.min(), v.mean(), v.max(), int((a == -32768).sum())))
