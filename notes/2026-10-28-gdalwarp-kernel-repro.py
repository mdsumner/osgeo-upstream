"""Repros for notes/2026-10-28-gdalwarp-kernel-findings.md, items 1, 2, 3, 5, 6, 7.

Assembled from the rwarp kernel-parity notes (hypertidy/rwarp#3). The
cases were checked with gdalwarp 3.14.0dev-739fcf03bf. This script was run
on GDAL 3.8.4 (Ubuntu 24.04), where items 2, 3, 5 and 6 reproduce; item 1
needs GDAL >= 3.11 (MODE_TIES is ignored before that, so all types print
5 5 5). Item 7 was added later and checked on 3.14.0dev only.

    python notes/2026-10-28-gdalwarp-kernel-repro.py

Item 4 has no standalone repro here; see rwarp tests/fixtures/kernels/gen.py,
case average_overhang.
"""

import numpy as np
from osgeo import gdal, osr

gdal.UseExceptions()


def mem(arr, dt, gt=None):
    a = np.asarray(arr)
    h, w = a.shape
    ds = gdal.GetDriverByName("MEM").Create("", w, h, 1, dt)
    ds.SetGeoTransform(gt or [0, 1, 0, h, 0, -1])
    ds.GetRasterBand(1).WriteArray(a)
    return ds


def mode_one_pixel(arr, dt, ties):
    ds = mem(arr, dt)
    h, w = np.asarray(arr).shape
    o = gdal.Warp("", ds, format="MEM", resampleAlg="mode", xRes=w, yRes=h,
                  warpOptions={"MODE_TIES": ties})
    return o.GetRasterBand(1).ReadAsArray()[0, 0]


def item1():
    print("1. MODE_TIES on first occurrence, [[5,3],[7,1]] -> 1 pixel")
    print("   expect Byte FIRST 5 MIN 1 MAX 7; Int32/Float32 give 5 5 5")
    for dt in (gdal.GDT_Byte, gdal.GDT_Int32, gdal.GDT_Float32):
        got = {t: int(mode_one_pixel([[5, 3], [7, 1]], dt, t)) for t in ("FIRST", "MIN", "MAX")}
        print("  ", gdal.GetDataTypeName(dt), got)


def item2():
    print("2. MODE_TIES=FIRST, [[5,3],[3,5]] -> 1 pixel; docs imply 5, code gives 3")
    for dt in (gdal.GDT_Byte, gdal.GDT_Int32, gdal.GDT_Float32):
        print("  ", gdal.GetDataTypeName(dt), int(mode_one_pixel([[5, 3], [3, 5]], dt, "FIRST")))


def item3():
    print("3. Scale estimate in chunked warps (watch CPL_DEBUG 'dfYScale' lines)")
    w, h = 3600, 1600
    src = mem(np.random.default_rng(0).random((h, w), dtype=np.float32), gdal.GDT_Float32,
              gt=[-180, 0.1, 0, 80, 0, -0.1])
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    src.SetProjection(srs.ExportToWkt())
    out = {}
    gdal.SetConfigOption("CPL_DEBUG", "ON")
    try:
        for memlimit in (2000, 1):
            o = gdal.Warp("", src, format="MEM", dstSRS="EPSG:3857", width=400, height=800,
                          resampleAlg="cubic", warpMemoryLimit=memlimit, errorThreshold=0)
            out[memlimit] = o.GetRasterBand(1).ReadAsArray()
    finally:
        gdal.SetConfigOption("CPL_DEBUG", None)
    a, b = out[2000], out[1]
    diff = np.abs(a - b)
    print(f"   single vs chunked: {int((diff > 0).sum())} of {a.size} pixels differ, max {diff.max():.3f}")
    print("   (observed on 3.14.0dev: 319985 to 320000 of 320000 across runs, max 0.113)")


def item5():
    print("5. Float working type, -dstnodata 0, -ot Byte: [[0.2, 1.0]] -> expect [[1, 1]], observed [[0, 1]]")
    ds = mem([[0.2, 1.0]], gdal.GDT_Float32)
    o = gdal.Warp("", ds, format="MEM", resampleAlg="near", width=2, height=1,
                  dstNodata=0, outputType=gdal.GDT_Byte)
    print("  ", o.GetRasterBand(1).ReadAsArray().tolist())


def item6():
    print("6. Rounding -2.5 into Int16: Int16 source (half up) -> -2, Float32 source (half away) -> -3")
    for dt in (gdal.GDT_Int16, gdal.GDT_Float32):
        ds = mem([[-2, -3]], dt)
        o = gdal.Warp("", ds, format="MEM", resampleAlg="average", width=1, height=1,
                      outputType=gdal.GDT_Int16)
        print("  ", gdal.GetDataTypeName(dt), int(o.GetRasterBand(1).ReadAsArray()[0, 0]))


def item7():
    print("7. cubicspline downsampling a symmetric source 64 -> 23 columns: output should be mirror-symmetric")
    print("   (observed on 3.14.0dev: cubicspline 5.83e-05, cubic and lanczos 0)")
    n, m = 64, 23
    x = np.arange(n)
    v = np.exp(-((x - (n - 1) / 2) / 6.0) ** 2).astype(np.float32)
    ds = mem(np.tile(v, (4, 1)), gdal.GDT_Float32)
    for alg in ("cubicspline", "cubic", "lanczos"):
        o = gdal.Warp("", ds, format="MEM", resampleAlg=alg, width=m, height=4,
                      outputBounds=[0, 0, n, 4])
        r = o.GetRasterBand(1).ReadAsArray()[1]
        print(f"   {alg:12s} max |out - mirror(out)| = {np.abs(r - r[::-1]).max():.3g}")


if __name__ == "__main__":
    print("GDAL", gdal.__version__)
    item1()
    item2()
    item3()
    item5()
    item6()
    item7()
