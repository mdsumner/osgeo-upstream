"""Repro for notes/2026-11-05-overview-colour-interp.md.

WMS and WMTS overview bands report GCI_Undefined for every band, so a
dataset opened at an overview (OVERVIEW_LEVEL=k) has no alpha band, and a
warp of it treats alpha as data. GeoTIFF overviews keep their colour
interpretation (item 1, the control).

    python3 notes/2026-11-05-overview-colour-interp-repro.py           # items 1-2, offline
    python3 notes/2026-11-05-overview-colour-interp-repro.py --online  # also 3-4
"""
import os, subprocess, sys, tempfile
import numpy as np
from osgeo import gdal

gdal.UseExceptions()
print("GDAL", gdal.VersionInfo("RELEASE_NAME"))
name = gdal.GetColorInterpretationName
tmp = tempfile.mkdtemp()

def report(label, dsn, k):
    d = gdal.Open(dsn)
    nb = d.RasterCount
    full = [name(d.GetRasterBand(b).GetColorInterpretation()) for b in range(1, nb + 1)]
    ovr = [name(d.GetRasterBand(b).GetOverview(k).GetColorInterpretation()) for b in range(1, nb + 1)]
    o = gdal.OpenEx(dsn, open_options=[f"OVERVIEW_LEVEL={k} only"])
    lvl = [name(o.GetRasterBand(b).GetColorInterpretation()) for b in range(1, nb + 1)]
    print(f"\n{label} ({d.GetDriver().ShortName}, {nb} bands)")
    print(f"   full resolution            {full}  mask flags {d.GetRasterBand(1).GetMaskFlags()}")
    print(f"   band.GetOverview({k})       {ovr}")
    print(f"   OVERVIEW_LEVEL={k} only     {lvl}  mask flags {o.GetRasterBand(1).GetMaskFlags()}")

# 1. Control: GeoTIFF RGBA with overviews keeps Alpha at every overview.
src = os.path.join(tmp, "rgba.tif")
ds = gdal.GetDriverByName("GTiff").Create(src, 64, 64, 4, gdal.GDT_Byte, ["PHOTOMETRIC=RGB", "ALPHA=YES"])
ds.SetGeoTransform([0, 1, 0, 64, 0, -1]); ds.SetProjection("EPSG:32755")
for b in (1, 2, 3):
    ds.GetRasterBand(b).WriteArray(np.full((64, 64), 200, np.uint8))
ds.GetRasterBand(4).WriteArray(np.full((64, 64), 255, np.uint8))
ds.BuildOverviews("NEAREST", [2, 4]); ds = None
report("1. GeoTIFF, the control", src, 0)

# 2. WMS (GDAL_WMS TMS): opening a TMS description does not contact the
#    server, so this is offline. Overview bands are created in
#    GDALWMSRasterBand::AddOverview() with m_color_interp = GCI_Undefined; the
#    loop in GDALWMSDataset (gdalwmsdataset.cpp ~L655) re-sets the full
#    resolution band's colour interpretation instead of the overview's.
wms = """<GDAL_WMS>
  <Service name="TMS"><ServerUrl>http://127.0.0.1:9/${z}/${x}/${y}.png</ServerUrl></Service>
  <DataWindow><UpperLeftX>-20037508.34</UpperLeftX><UpperLeftY>20037508.34</UpperLeftY>
    <LowerRightX>20037508.34</LowerRightX><LowerRightY>-20037508.34</LowerRightY>
    <TileLevel>10</TileLevel><TileCountX>1</TileCountX><TileCountY>1</TileCountY><YOrigin>top</YOrigin></DataWindow>
  <Projection>EPSG:3857</Projection><BlockSizeX>256</BlockSizeX><BlockSizeY>256</BlockSizeY>
  <BandsCount>4</BandsCount>
</GDAL_WMS>"""
report("2. WMS, GDAL_WMS TMS with 4 bands (offline)", wms, 3)

if "--online" not in sys.argv:
    print("\n(run with --online for 3. WMTS and 4. the warp consequence)")
    sys.exit(0)

# 3. WMTS: overviews are VRT datasets over WMS datasets (wmtsdataset.cpp
#    ~L2345, VRTCreate/VRTAddBand); nothing sets their colour interpretation.
#    Only WMTSBand::GetColorInterpretation() (~L305) reports R/G/B/Alpha.
wmts = ("WMTS:https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/"
        "WMTS/1.0.0/WMTSCapabilities.xml,layer=World_Imagery")
report("3. WMTS, Esri World Imagery (online)", wmts, 8)

# 4. Consequence: warp a WMS source with an alpha band at overview 8.
#    gdalwarp -ovr 8 detects the alpha band on the full dataset and masks;
#    opening the overview as a dataset (OVERVIEW_LEVEL) loses it, so alpha
#    is warped as data and colour under alpha 0 is kept.
#    The WA GSD basemap is an ArcGIS tile cache in EPSG:7844 with transparent
#    areas (as a TMS description; its WMTS capabilities don't open in GDAL).
r0 = 0.08798912593428897; ts = 256 * r0
wa = f"""<GDAL_WMS>
  <Service name="TMS"><ServerUrl>https://gissdi.dmp.wa.gov.au/gisexternal/rest/services/External/GSD_Basemap_External/MapServer/tile/${{z}}/${{y}}/${{x}}</ServerUrl></Service>
  <DataWindow><UpperLeftX>-400</UpperLeftX><UpperLeftY>399.9999999999998</UpperLeftY>
    <LowerRightX>{-400 + 24 * ts:.12f}</LowerRightX><LowerRightY>{400 - 20 * ts:.12f}</LowerRightY>
    <TileLevel>15</TileLevel><TileCountX>24</TileCountX><TileCountY>20</TileCountY><YOrigin>top</YOrigin></DataWindow>
  <Projection>EPSG:7844</Projection><BlockSizeX>256</BlockSizeX><BlockSizeY>256</BlockSizeY>
  <BandsCount>4</BandsCount><ZeroBlockHttpCodes>204,404</ZeroBlockHttpCodes>
</GDAL_WMS>"""
wa_xml = os.path.join(tmp, "wa.xml"); open(wa_xml, "w").write(wa)
te = ["-te", "370000", "6440000", "420000", "6490000", "-ts", "256", "256", "-t_srs", "EPSG:28350", "-r", "near"]

def warped(args, label):
    out = os.path.join(tmp, label.replace(" ", "_").replace("=", "") + ".tif")
    subprocess.run(args + [out], check=True, capture_output=True)
    w = gdal.Open(out)
    a = np.stack([w.GetRasterBand(b).ReadAsArray() for b in range(1, 5)])
    under = (a[3] == 0)
    print(f"   {label:46s} alpha 0 at {under.sum():6d} px; max colour there: {a[:3, under].max() if under.any() else '-'}")
    return a

print("\n4. Warp at overview 8, colour under alpha 0 (online)")
g = warped(["gdalwarp", "-q", "-ovr", "8"] + te + [wa_xml], "gdalwarp -ovr 8")
o = warped(["gdalwarp", "-q", "-oo", "OVERVIEW_LEVEL=8 only", "-ovr", "NONE"] + te + [wa_xml],
           "gdalwarp -oo 'OVERVIEW_LEVEL=8 only'")
r = warped(["gdal", "raster", "reproject", "-q", "--oo", "OVERVIEW_LEVEL=8 only", "--dst-crs", "EPSG:28350",
            "--bbox", "370000,6440000,420000,6490000", "--size", "256,256", "-r", "near", "--of", "GTiff", wa_xml],
           "gdal raster reproject --oo 'OVERVIEW_LEVEL=8 only'")
print("   alpha bands identical across the three:", bool((g[3] == o[3]).all() and (g[3] == r[3]).all()))
