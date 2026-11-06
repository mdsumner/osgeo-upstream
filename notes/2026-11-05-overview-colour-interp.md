# WMS/WMTS overview bands lose their colour interpretation, 2026-11-05

Found while building a warp comparison sandbox (mdsumner/warp-sandbox): the
same request through gdalwarp, `gdal raster reproject` and rwarp, with every
engine reading the same overview level. On a WMS tile cache with an alpha
band, the engines that opened the overview with `OVERVIEW_LEVEL=k only` kept
the colour under fully transparent pixels; gdalwarp `-ovr k` wrote 0 there.

- GDAL source read at `739fcf03bf` (3.14.0dev), `frmts/wms/`, `frmts/wmts/`.
  Line numbers are approximate.
- Behaviour checked with the Python bindings, `gdalwarp` and `gdal raster
  reproject` from the same build (`3.14.0dev-739fcf03bf`).
- Repro: [2026-11-05-overview-colour-interp-repro.py](2026-11-05-overview-colour-interp-repro.py).
  Items 1-2 offline (a GDAL_WMS TMS description opens without contacting its
  server); `--online` adds 3 (WMTS) and 4 (the warp consequence).
- Not yet checked on older releases.

| # | Finding | Status | Kind |
|---|---|---|---|
| 1 | WMS overview bands report `GCI_Undefined` for every band | confirmed + code reading | bug, small |
| 2 | WMTS overview bands report `GCI_Undefined` for every band | confirmed + code reading | bug, small |
| 3 | Consequence: a dataset opened with `OVERVIEW_LEVEL=k` has no alpha band, so a warp of it treats alpha as data | confirmed | follows from 1-2 |

## 1. WMS overview bands: `GCI_Undefined` - confirmed, bug

**What:** a 4-band GDAL_WMS (TMS) dataset reports Red, Green, Blue, Alpha at
full resolution and `Undefined` for all four bands of every overview, whether
read as `band.GetOverview(k)` or by opening with `OVERVIEW_LEVEL=k`. The mask
flags go from 6 (`GMF_ALPHA | GMF_PER_DATASET`) to 1 (`GMF_ALL_VALID`). A
3-band source (OSM) shows the same: Blue becomes Undefined. GeoTIFF overviews
keep their colour interpretation (repro item 1, the control).

**Where:** `GDALWMSDataset::Initialize` (`gdalwmsdataset.cpp` ~L638-660)
builds each band and its overviews:

```cpp
GDALWMSRasterBand *band = new GDALWMSRasterBand(this, i, 1.0);
band->m_color_interp = color_interp;
SetBand(i + 1, band);
double scale = 0.5;
for (int j = 0; j < nOverviews; ++j)
{
    if (!band->AddOverview(scale))
        break;
    band->m_color_interp = color_interp;   // sets the full-resolution band again
    scale *= 0.5;
}
```

The line in the loop re-sets the full-resolution band's colour
interpretation; it looks meant for the overview just added.
`GDALWMSRasterBand::AddOverview` (`gdalwmsrasterband.cpp` ~L405) creates the
overview with the constructor default, `m_color_interp(GCI_Undefined)` (~L27).

**Fix candidate:** in `AddOverview`, `overview->m_color_interp =
m_color_interp;` (then the line in the loop can go), or set it on the new
overview in the loop.

## 2. WMTS overview bands: `GCI_Undefined` - confirmed, bug

**What:** the same as 1 for WMTS (Esri World Imagery, 4 bands): full
resolution Red, Green, Blue, Alpha; every overview Undefined; mask flags 6 to 1.

**Where:** WMTS overviews are VRT datasets over WMS datasets
(`wmtsdataset.cpp` ~L2345, `VRTCreate` / `VRTAddBand` / `VRTAddSimpleSource`),
and nothing sets the colour interpretation of those VRT bands.
`WMTSBand::GetOverview` (~L287) returns `apoDatasets[nLevel + 1]->GetRasterBand(nBand)`,
one of those VRT bands. Only the top-level `WMTSBand::GetColorInterpretation()`
(~L305) reports Gray or R/G/B/Alpha, from the band count.

**Fix candidate:** set the colour interpretation on each VRT band when the
overview datasets are built (the same rule as `WMTSBand::GetColorInterpretation`),
e.g. `GDALSetRasterColorInterpretation(hVRTBand, ...)` next to `VRTAddBand`.

## 3. Consequence for warping at an overview - confirmed

**What (repro item 4):** the WA GSD basemap (an ArcGIS tile cache with
transparent areas, as a GDAL_WMS TMS), warped `-r near` at overview 8 to
EPSG:28350, 256 x 256:

| route | pixels with alpha 0 | max colour under alpha 0 |
|---|---|---|
| `gdalwarp -ovr 8` | 20975 | 0 |
| `gdalwarp -oo 'OVERVIEW_LEVEL=8 only' -ovr NONE` | 20975 | 253 |
| `gdal raster reproject --oo 'OVERVIEW_LEVEL=8 only'` | 20975 | 253 |

The alpha band itself is identical in all three. `gdalwarp -ovr k` finds the
alpha band on the full-resolution dataset (where it is labelled) before
choosing the overview, so it masks; the `OVERVIEW_LEVEL` routes open the
overview bands, where it isn't. `gdal raster reproject` has no `-ovr` or
`-srcalpha` argument, so opening the overview is the only way to pin a level
there. Visually it's the same image; values differ under alpha 0, and a warp
with an interpolating kernel would blend the masked colour into its
neighbours.

**Workaround (in warp-sandbox):** read the colour interpretation from the
full-resolution dataset and pass the alpha band explicitly.
