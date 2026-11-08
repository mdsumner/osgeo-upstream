# Plans and status

One table of everything in flight or proposed: open tracker issues, live fork
branches and new items from the 2026-10-25 sweep. Status words match the
`status:` labels. Priorities are provisional; see PRIORITIES.md for the order.

Last updated 2026-11-05.

## Multidim, byte references and Zarr

| Item | Where | Status | P | Next step |
|---|---|---|---|---|
| `gdal mdim get-refs` algorithm | [#36](https://github.com/mdsumner/osgeo-upstream/issues/36), PR [OSGeo/gdal#14677](https://github.com/OSGeo/gdal/pull/14677), branches feature/mdim-get-refs, mdim-helpers, stage1-mvp, fast-path-h5-chunk-refs-iter | upstream (PR closed unmerged, 2026-07-11) | P1 | Decide the route (see STRATEGY.md) |
| Zarr V3 `scale_offset` and `cast_value` read (GDAL issue 15170) | [#59](https://github.com/mdsumner/osgeo-upstream/issues/59), PR [OSGeo/gdal#15305](https://github.com/OSGeo/gdal/pull/15305) (open, unreviewed) | ready | P1 | Build the PR, test with a zarr-python store, comment |
| Zarr and multidim bugs from closed PRs 15388-15398 | [#39](https://github.com/mdsumner/osgeo-upstream/issues/39) | investigating | P1 | WP2 and WP1: confirm on master, write repros here |
| Zarr V3 fill_value vs nodata survey (WP7a of #39) | [#41](https://github.com/mdsumner/osgeo-upstream/issues/41) | idea | P1 | Survey note in notes/, with small stores from zarr-python, xarray, GDAL |
| Expose ReadCompressedData() to Python | [#35](https://github.com/mdsumner/osgeo-upstream/issues/35) | idea | P2 | Check what SWIG has now; C API exists since 2023 (#7081) |
| Pick up `mdim info --detailed` default limit | [#34](https://github.com/mdsumner/osgeo-upstream/issues/34), PR OSGeo/gdal#13723 (another contributor, unmerged) | idea | P2 | Check #13723 review state; `mdim info` changed since (text/json, 2026-06) |
| Zarr V3 `numcodecs.*` names: `numcodecs.zstd`, `numcodecs.zlib`, `numcodecs.shuffle` (blocks `/vsiicechunk/` on BRAN) | [#42](https://github.com/mdsumner/osgeo-upstream/issues/42), [notes/2026-11-03-zarr-codec-gaps.md](notes/2026-11-03-zarr-codec-gaps.md) C1-C3; upstream: GDAL issue 14917 (open since 2026-07) | ready | P1 | Run the repro on master, comment on GDAL 14917, then one PR |
| TIFF predictors as `imagecodecs_delta` (PREDICTOR=2) and `imagecodecs_floatpred` (PREDICTOR=3), Zarr V2 filter and V3 codec (blocks kerchunk and `/vsiicechunk/` on GHRSST MUR COGs; would allow predictor-3 Float32 COGs such as ESA CCI chl-a) | [#42](https://github.com/mdsumner/osgeo-upstream/issues/42), branch zarr-tiff-predictor-DRAFT (its predictor 3 byte order is wrong on little endian), notes C4-C6 | ready | P1 | Issue asking about the name, after the numcodecs one |
| Zarr JPEG codec draft | [#42](https://github.com/mdsumner/osgeo-upstream/issues/42), branch zarr-jpeg | idea | P3 | No store needs it yet |
| `/vsikerchunk_parquet_ref/`: row with null `path` and null `raw` read as a path, not a missing chunk ("Too large tile") | `frmts/zarr/vsikerchunk_parquet_ref.cpp` Open(), else branch after the `raw` check (master 5906ed4) | investigating | P2 | Small repro (one null row in refs.0.parq); fsspec treats it as missing |
| HDF5 `GetRawBlockInfo()` on sparse files | fixed upstream by OSGeo/gdal PR 15423 (Dan Baston, 2026-10-29) | done | - | Close my upstream issue if still open |
| `test_hdf5_multidim_getrawblockinfo_chunked` never runs: `@pytest.mark.require_driver("use_optim", [True, False])` instead of `parametrize` | `autotest/gdrivers/hdf5multidim.py:845` (master 5906ed4) | ready | P2 | One-line test fix; good warm-up PR |
| HDF5 group variant (sinusoidal) | [#24](https://github.com/mdsumner/osgeo-upstream/issues/24) | idea | P3 | Re-read |
| Kerchunk support | [#23](https://github.com/mdsumner/osgeo-upstream/issues/23) | done? | - | GDAL reads Kerchunk JSON and Parquet refs, and has an Icechunk driver (2026-06). Close if nothing is left |
| Nulls in Parquet domain (implicit zero) | [#38](https://github.com/mdsumner/osgeo-upstream/issues/38) | idea | P3 | Re-read |
| Eager configure pyarrow/sedonadb | [#37](https://github.com/mdsumner/osgeo-upstream/issues/37) | idea | P3 | Re-read |

## Multidim VRT (found 2026-10-28, parked)

Repro and findings: [notes/2026-10-28-mdim-vrt-findings.md](notes/2026-10-28-mdim-vrt-findings.md).
No tracker issues yet.

| Item | Where | Status | P | Next step |
|---|---|---|---|---|
| Strided read across VRT sources fails; `gdal mdim convert` exits 0 and writes fill values | notes, item 1 | parked | P2 | Check on master; locate the strided path in the VRT mdim source read |
| mdim `<BlockSize>`: XSD integerList (spaces) vs driver (commas only) | notes, item 2 | parked | P3 | Check master's gdalvrt.xsd and parser |
| `dataAxisToSRSAxisMapping`: identity default on (t, y, x), 0 in slice mappings | notes, item 3 | parked | P3 | Check master; read mapping set-up and GetView remap |

## Warp kernels (found 2026-10-28, drafts ready to file)

Findings: [notes/2026-10-28-gdalwarp-kernel-findings.md](notes/2026-10-28-gdalwarp-kernel-findings.md),
repro [notes/2026-10-28-gdalwarp-kernel-repro.py](notes/2026-10-28-gdalwarp-kernel-repro.py).
Fixtures in hypertidy/rwarp#3 (branch `kernels/gdal-parity`). No tracker issues yet.
All confirmed on master as of 2026-10-28 (`3.14.0dev-739fcf03bf`).

Upstream todos, in filing order. Issue drafts from the rwarp sprint are in
[notes/2026-10-28-gdalwarp-issue-drafts/](notes/2026-10-28-gdalwarp-issue-drafts/README.md):
rewrite each in my own words, keep it short, declare tool use. One at a
time, not a burst (STRATEGY.md); a PR with a test only after the issue has
a response.

| Item | Where | Status | P | Next step |
|---|---|---|---|---|
| Kernel scale estimate ignores the chunk's destination offset; chunked warps widen by the wrong amount (also on 3.8.4; real-data case 2026-11-06: COP90 over Tasmania, up to 2.37 m) | notes, item 3; draft 01 | ready | P1 | File first. Fix candidate: add nDstXOff/nDstYOff to the sample points. The COP90 case makes a good motivating example |
| `MODE_TIES=MIN/MAX` ignored on a value's first occurrence for 32/64-bit and float types, plus the `MODE_TIES=FIRST` docs wording (first to reach the count, not first encountered) | notes, items 1 and 2; draft 02 | ready | P2 | File second, one issue for both |
| Float working type defeats dst nodata avoidance (0.2 -> Byte 0 = nodata, no warning; also on 3.8.4), with the two rounding rules into integer outputs as context | notes, items 5 and 6; draft 03 | ready | P2 | File third; the rounding point may only need a docs sentence for `-ot`/`-wt` |
| `cubicspline` weight not zero beyond \|x\| = 2; downsampled output asymmetric (~1e-4) | notes, item 7; draft 04 | ready | P3 | File fourth. Fix: return 0 for \|x\| >= 2 in GWKBSpline and GWKBSpline4Values |
| `average`/`mode` edge weight above 1 when the footprint overhangs the source | notes, item 4; draft 05 | ready | P3 | File last, as a question; maybe a discussion or gdal-dev post instead |

## WMS/WMTS overview colour interpretation (found 2026-11-05)

Findings: [notes/2026-11-05-overview-colour-interp.md](notes/2026-11-05-overview-colour-interp.md),
repro [notes/2026-11-05-overview-colour-interp-repro.py](notes/2026-11-05-overview-colour-interp-repro.py).
Found in mdsumner/warp-sandbox. Confirmed on `3.14.0dev-739fcf03bf`; not yet
checked on master after that, or on older releases.

| Item | Where | Status | P | Next step |
|---|---|---|---|---|
| WMS overview bands report `GCI_Undefined`; the overview loop re-sets the base band instead | notes, item 1 | ready | P2 | Check master, then one small PR: copy `m_color_interp` in `AddOverview`, with a test opening a TMS description (offline) |
| WMTS overview bands (VRT over WMS) report `GCI_Undefined` | notes, item 2 | ready | P2 | Same PR or a second one: set colour interpretation on the VRT bands |
| `OVERVIEW_LEVEL` opens lose the alpha band, so warps treat alpha as data | notes, item 3 | follows | P3 | Mention as the motivation in the PR; nothing separate to file |

## Warp at the antimeridian, GTiff prefetch (found 2026-11-08)

Drafts: [notes/2026-11-08-warp-sandbox-drafts/](notes/2026-11-08-warp-sandbox-drafts/README.md),
from mdsumner/warp-sandbox (`notes/`, evidence in `bench/README.md` sections 4-5).
Written against `3.14.0dev-fa1fc3c77e`. Starting points, not text to paste.

| Item | Where | Status | P | Next step |
|---|---|---|---|---|
| gdalwarp reads a full-width source strip when the target crosses the antimeridian of a global lon/lat source; two edge windows need 11.3x fewer pixels | [#62](https://github.com/mdsumner/osgeo-upstream/issues/62), draft 01; rwarp fix hypertidy/rwarp#57; related [#28](https://github.com/mdsumner/osgeo-upstream/issues/28) | ready | P2 | Re-run on master, settle the pixel count, rewrite short and file. Ask whether a split in `CollectChunkList()` (behind a warp option) is welcome |
| GTiff `AdviseRead()` is a no-op, so separate windows over /vsicurl/ queue one round trip each | [#63](https://github.com/mdsumner/osgeo-upstream/issues/63), draft 02; overlaps [#39](https://github.com/mdsumner/osgeo-upstream/issues/39) WP3 | ready | P3 | After 01 has a response. Check `GDAL_NUM_THREADS` paths first; frame as a question (accumulating `AdviseRead()` vs multi-window `RasterIO()`) |

## vrt:// connection

| Item | Where | Status | P | Next step |
|---|---|---|---|---|
| Further vrt:// options | [#1](https://github.com/mdsumner/osgeo-upstream/issues/1) | done mostly | P3 | 22 options merged; keep #1 for the two below or close |
| Flags without `=value`; strict key=value check | branches vrtcon-no-value-options2, vrtcon-key-value-required | parked | P3 | Check current master parsing first |

## Warp, geolocation, extents

| Item | Where | Status | P | Next step |
|---|---|---|---|---|
| Remaining longitude wrap problems | [#28](https://github.com/mdsumner/osgeo-upstream/issues/28) | idea | P2 | Repro script per case; good figure material |
| wgs84Extent should densify edges | [#30](https://github.com/mdsumner/osgeo-upstream/issues/30) | idea | P2 | Small, clear; repro with a polar CRS |
| Warp from unscaled geolocation arrays | [#16](https://github.com/mdsumner/osgeo-upstream/issues/16) | idea | P2 | Re-read |
| gdalwarp -tap with -ts | [#7](https://github.com/mdsumner/osgeo-upstream/issues/7), branch warp-tap-with-ts | parked | P2 | Check whether `gdal raster reproject` covers it |
| Footprint from geolocation arrays | [#15](https://github.com/mdsumner/osgeo-upstream/issues/15) | idea | P3 | |
| Sum resampling for overviews | [#17](https://github.com/mdsumner/osgeo-upstream/issues/17) | idea | P3 | gdalwarp has sum (sum-preserving since 2022, #6560); overviews do not |
| gdalwarp CRS-only heuristics | [#10](https://github.com/mdsumner/osgeo-upstream/issues/10) | idea | P3 | |
| Warp disparate inputs | [#26](https://github.com/mdsumner/osgeo-upstream/issues/26) | idea | P3 | |

## Drivers, netCDF, other

| Item | Where | Status | P | Next step |
|---|---|---|---|---|
| netCDF vector timeseries | [#43](https://github.com/mdsumner/osgeo-upstream/issues/43), branch netcdf-vector-timeseries | parked | P3 | wip since 2024 |
| GNM crash and failures | [#32](https://github.com/mdsumner/osgeo-upstream/issues/32) | idea | P3 | |
| TIFF explore | [#27](https://github.com/mdsumner/osgeo-upstream/issues/27) | idea | P3 | |
| Rogues gallery from raad | [#13](https://github.com/mdsumner/osgeo-upstream/issues/13) | idea | P2 | Good source of repros and figures |
| Kernel, zonal stats, rasterize, raster to points | [#29](https://github.com/mdsumner/osgeo-upstream/issues/29) | idea | P3 | Strategy note rather than code |

## Docs and housekeeping

| Item | Where | Status | P | Next step |
|---|---|---|---|---|
| Two unsent doc fixes | [#44](https://github.com/mdsumner/osgeo-upstream/issues/44), branches patch-15, mdsumner-patch-1 | ready | P3 | Check still needed, then send |
| PROJ: unsent "param arg form" commit | [#45](https://github.com/mdsumner/osgeo-upstream/issues/45), mdsumner/PROJ patch-1 | parked | P3 | Check still relevant |
| Capture upstream issues I opened | [#40](https://github.com/mdsumner/osgeo-upstream/issues/40) | idea | P2 | Fill gap in CONTRIBUTIONS.md |
| Delete 65 merged or superseded fork branches | [#46](https://github.com/mdsumner/osgeo-upstream/issues/46), notes/2026-10-25-branch-sweep.md | ready | P3 | Michael deletes; list is in the sweep |
