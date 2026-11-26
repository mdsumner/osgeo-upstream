"""Repro for notes/2026-11-26-mdim-classic-strided-read.md.

MDArrays backed by classic RasterIO (Band.AsMDArray(), Dataset.AsMDArray(),
GetResampled(), multidim VRT <SourceBand> sources) read a window of
count * |step| per axis. An index view gets step 0, so a zero-size window
that RasterIO skips without error (items 1, 5, 6); a step that does not
divide the extent overruns it (2, 6, 7); a valid strided window is
decimated by nearest, not picked at start + i * step (3), and can be
served from overviews (4).

Every read goes into a buffer pre-filled with -999, so "-999" means
nothing was written.

    python3 notes/2026-11-26-mdim-classic-strided-read-repro.py
"""
import numpy as np
from osgeo import gdal, osr

gdal.UseExceptions()
print(gdal.VersionInfo("--version"))


def tif(name, n, bands=1, ovr=False, georef=False):
    ds = gdal.GetDriverByName("GTiff").Create(f"/vsimem/{name}", n, n, bands, gdal.GDT_Int16)
    for b in range(bands):
        ds.GetRasterBand(b + 1).WriteArray(
            (np.arange(n * n) + 100 * b).astype(np.int16).reshape(n, n))
    if georef:
        ds.SetGeoTransform([0, 1, 0, n, 0, -1])
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3857)
        ds.SetSpatialRef(srs)
    if ovr:
        ds.BuildOverviews("AVERAGE", [2])
    return ds


def check(item, label, arr, view, expected):
    v = arr.GetView(view)
    buf = np.full([d.GetSize() for d in v.GetDimensions()], -999, dtype=np.int16)
    try:
        got = v.ReadAsArray(buf_obj=buf)
    except Exception as e:
        print(f"{item}. {label} {view}: ERROR {e}".replace("\n", " "))
        return
    word = "ok" if np.array_equal(got, expected) else "WRONG"
    print(f"{item}. {label} {view}: {word}; row 0 expected {np.atleast_2d(expected)[0].tolist()} "
          f"got {np.atleast_2d(got)[0].tolist()}")


ds5 = tif("a5.tif", 5)
a5 = ds5.ReadAsArray()
ds6 = tif("a6.tif", 6)
a6 = ds6.ReadAsArray()

# 1. index view: step 0 on the indexed axis, window (0,0)x5x0, RasterIO skipped
check(1, "Band.AsMDArray() 5x5", ds5.GetRasterBand(1).AsMDArray(), "[0]", a5[0])

# 2. step 2 on 5 pixels: count 3, window 6
check(2, "Band.AsMDArray() 5x5", ds5.GetRasterBand(1).AsMDArray(), "[::2,::2]", a5[::2, ::2])

# 3. step 2 on 6 pixels: window 6 fits; nearest decimation picks 1, 3, 5
check(3, "Band.AsMDArray() 6x6", ds6.GetRasterBand(1).AsMDArray(), "[::2,::2]", a6[::2, ::2])

# 4. as 3, with an AVERAGE overview: served from the overview
ds6o = tif("a6o.tif", 6, ovr=True)
check(4, "Band.AsMDArray() 6x6 + overview", ds6o.GetRasterBand(1).AsMDArray(), "[::2,::2]", a6[::2, ::2])

# 5. Dataset.AsMDArray(): same window computation, GDALMDArrayFromDataset::ReadWrite()
dsb = tif("b5.tif", 5, bands=2)
yxb = dsb.AsMDArray()  # (Y, X, Band) for pixel-interleaved GTiff
check(5, "Dataset.AsMDArray() (Y,X,Band)", yxb, "[0]", np.moveaxis(dsb.ReadAsArray(), 0, -1)[0])
bxy = dsb.AsMDArray(["DIM_ORDER=Band,Y,X"])
check(5, "Dataset.AsMDArray() (Band,Y,X)", bxy, "[0,::2,::2]", a5[::2, ::2])

# 6. GetResampled(): also reads through GDALMDRasterIOFromBand()
dsr = tif("r5.tif", 5, georef=True)
res = dsr.GetRasterBand(1).AsMDArray().GetResampled([None, None], gdal.GRIORA_NearestNeighbour,
                                                    dsr.GetSpatialRef())
full = res.ReadAsArray()
check(6, "GetResampled()", res, "[0]", full[0])
check(6, "GetResampled()", res, "[::2,::2]", full[::2, ::2])

# 7. multidim VRT with a <SourceBand> source (how this was found: BedMachine
#    v4.1, 13333 x 13333 GeoTIFF, view [::14,::14] asks for 13342 x 13342)
vrt = """<VRTDataset><Group name="/">
  <Dimension name="y" size="5"/><Dimension name="x" size="5"/>
  <Array name="a"><DataType>Int16</DataType>
    <DimensionRef ref="y"/><DimensionRef ref="x"/>
    <Source><SourceFilename>/vsimem/a5.tif</SourceFilename><SourceBand>1</SourceBand></Source>
  </Array></Group></VRTDataset>"""
md = gdal.OpenEx(vrt, gdal.OF_MULTIDIM_RASTER).GetRootGroup().OpenMDArray("a")
check(7, "mdim VRT <SourceBand>", md, "[0]", a5[0])
check(7, "mdim VRT <SourceBand>", md, "[::2,::2]", a5[::2, ::2])

# 8. control: plain Read() with count 1 (step 1) is fine
b = ds5.GetRasterBand(1).AsMDArray()
got = b.ReadAsArray(array_start_idx=[0, 0], count=[1, 5])
print(f"8. control Read(count=[1,5]): {'ok' if np.array_equal(got[0], a5[0]) else 'WRONG'}")
