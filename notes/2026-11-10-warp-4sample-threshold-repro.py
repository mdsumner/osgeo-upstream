"""Repro for notes/2026-11-10-warp-4sample-threshold.md.

Offline, synthetic. Run it under GDAL 3.12 and 3.13 (or master) and compare.

1. Same-CRS bilinear downsampling of random Float32 data by factors 1.25 .. 4: is the output
   identical to `-wo XSCALE=1 -wo YSCALE=1` (no kernel widening)?
   3.12: False for every factor. 3.13 / 3.14.0dev: True for 1.25, 1.5, 1.75; False from 2.
2. Explicit XSCALE/YSCALE for a 1.75x downsample (scale 0.571): do different values change the
   output? 3.12: yes. 3.13+: no, every value > 0.5 gives the same (4-sample) output.
3. Same for cubic, and lanczos as a control (lanczos widens at any scale < 1 in both).

    python notes/2026-11-10-warp-4sample-threshold-repro.py

Clean-room versions used (conda-forge via pixi, ubuntu:24.04 container):
    pixi init g && cd g && pixi add python numpy "gdal=3.12" && pixi run python <this>
"""

import numpy as np
from osgeo import gdal, osr

gdal.UseExceptions()
print("GDAL", gdal.__version__)

arr = np.random.default_rng(1).uniform(0, 200, (1000, 1000)).astype("float32")
srs = osr.SpatialReference()
srs.ImportFromEPSG(3577)
src = gdal.GetDriverByName("MEM").Create("", 1000, 1000, 1, gdal.GDT_Float32)
src.SetGeoTransform((0, 10, 0, 10000, 0, -10))
src.SetSpatialRef(srs)
src.GetRasterBand(1).WriteArray(arr)


def warp(res, alg, wo=()):
    return gdal.Warp("", src, format="MEM", xRes=res, yRes=res, resampleAlg=alg,
                     warpOptions=list(wo)).ReadAsArray().astype("f8")


print("\n1. default output identical to XSCALE=1 (i.e. no widening)?")
for alg in ["bilinear", "cubic", "lanczos"]:
    row = []
    for res in [12.5, 15, 17.5, 20, 25, 40]:
        same = np.array_equal(warp(res, alg), warp(res, alg, ["XSCALE=1", "YSCALE=1"]))
        row.append(f"{10 / res:.3f}:{'SAME' if same else 'diff'}")
    print(f"   {alg:9s}", "  ".join(row))

print("\n2. 1.75x downsample (scale 0.571), explicit XSCALE=YSCALE values, bilinear")
base = warp(17.5, "bilinear", ["XSCALE=1", "YSCALE=1"])
for s in [1, 0.9, 0.7, 0.571, 0.51, 0.5, 0.4]:
    out = warp(17.5, "bilinear", [f"XSCALE={s}", f"YSCALE={s}"])
    print(f"   XSCALE={s:<6} max |out - XSCALE=1 out| = {abs(out - base).max():.3f}")
