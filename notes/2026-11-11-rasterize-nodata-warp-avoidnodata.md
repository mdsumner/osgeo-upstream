# gdal_rasterize sets NoData = 0 on every output it creates (3.10+); warp nodata avoidance meets rasterio 1.5.1, 2026-11-11

Found in geo-stack-alt while porting GA's fast-ice NormCovar processing (abradley60/fast-ice
4694c6c, jlo031/normalized_covariance d6843d2) to osgeo.gdal and gdalraster. Evidence there:
`evidence/normcovar/` and `cleanroom/experiments/normcovar/` (local repo, not yet on GitHub).

- Repro: [2026-11-11-rasterize-nodata-warp-avoidnodata-repro.py](2026-11-11-rasterize-nodata-warp-avoidnodata-repro.py)
  (offline, synthetic). Run under conda-forge GDAL 3.9.3, 3.10.3, 3.11.5, 3.12.3 (with rasterio
  1.5.0) and 3.13.3 (with rasterio 1.5.1 and 1.5.2), pixi, clean ubuntu:24.04 container.
- Source read at master `b81b64991b` (~/gdal, 2026-11-06).
- Relates to [2026-10-28-gdalwarp-kernel-findings.md](2026-10-28-gdalwarp-kernel-findings.md)
  item 5 (float working type defeats the same avoidance) and
  [2026-11-10-warp-4sample-threshold.md](2026-11-10-warp-4sample-threshold.md) (odc-geo always
  sets `XSCALE=1 YSCALE=1`, below).

## A. gdal_rasterize: created outputs get NoData = 0 without -a_nodata (regression, 3.10.0)

**Kind:** regression. The docs say `-a_nodata` "assign[s] a specified nodata value to output
bands". Nothing says a nodata value is set when the option is absent.

| GDAL | nodata on a created output: no `-a_nodata` | ... with `-init 0` | `-a_nodata 255` |
|---|---|---|---|
| 3.9.3 | none | none | 255 |
| 3.10.3, 3.11.5, 3.12.3, 3.13.3 | **0** | **0** | 255 |

**Cause.** `8d9ceabc12` (2024-09-06, "gdal_rasterize: port to argument parser", #10741, first in
3.10.0) replaced `char *pszNoData` (nullptr unless `-a_nodata` was given) with
`std::string osNoData{}`. Both `CreateOutputDataset()` calls pass `osNoData.c_str()`
(`apps/gdal_rasterize_lib.cpp` ~L1307, ~L1383). That pointer is never null, so the test

```c
// CreateOutputDataset(), ~L948
if (pszNoData)
    ... poBand->SetNoDataValue(CPLAtof(pszNoData));   // CPLAtof("") == 0
```

is always true. The `-a_nodata` parsing (~L1555) is fine. Likely fix: pass
`osNoData.empty() ? nullptr : osNoData.c_str()`, or test `pszNoData && pszNoData[0]`.

`gdal vector rasterize` (`apps/gdalalg_vector_rasterize.cpp` ~L264) adds `-a_nodata` only when
`--nodata` is given, then calls the same library function, and does the same. Repro item 1b
(conda-forge 3.11.5, 3.12.3, 3.13.3; the `gdal` CLI is new in 3.11): without `--nodata`, with or
without `--init 0`, the output has NoData = 0; `--nodata 255` gives 255. The burnt cells are
right (5000 of 10000) in every case, so only the nodata flag is wrong. The one fix in
`gdal_rasterize_lib.cpp` covers both front ends; an autotest for `gdal vector rasterize`
(`autotest/utilities/test_gdalalg_vector_rasterize.py`) would pin it there too.

**Why it matters.** Rasterizing a 0/1 mask (`-burn 1 -init 0`, or without `-init`) gives a mask
whose 0s are nodata. Readers that honour nodata then lose every unburnt cell. gdalraster reads
them as NA, and the land/water mask in the NormCovar port came back with water as NA.
Workaround: rasterize into an existing dataset, or `-a_nodata` with a value outside the burn
range, or unset the nodata afterwards.

Possible test: `autotest/utilities/test_gdal_rasterize_lib.py`, create an output with `-ts` and
`-burn` only, and assert `GetNoDataValue() is None`.

## B. Warp nodata avoidance (3.11+) reached odc-geo users through rasterio 1.5.1

**Kind:** intended GDAL behaviour. Recorded because a downstream default now triggers it.

When the destination nodata is set and a valid output value equals it, the warp kernel rewrites
the value to the next representable one and warns once: "Value 0 in the source dataset has been
changed to 1 in the destination dataset to avoid being treated as NoData." `AvoidNoData()` is in
`alg/gdalwarpkernel.cpp` (~L1645). From `17a737fbd7` (2025-01-24, "Warping: fix inconsistent
replacement of valid value that collides with the dstnodata value", #11711, first in 3.11.0) it
applies in every resampling path, nearest included.

| | uint8 0/1 to 1/10, near, dst nodata 0 |
|---|---|
| `gdal.Warp`, GDAL 3.9.3, 3.10.3 | 0s kept |
| `gdal.Warp`, GDAL 3.11.5, 3.12.3, 3.13.3 | **all 0s become 1**, one warning |
| `rasterio.warp.reproject(dst_nodata=0)`, rasterio 1.5.0 (GDAL 3.12.3; also 3.13.3, checked in geo-stack-alt) | 0s kept |
| same, rasterio 1.5.1 and 1.5.2 (GDAL 3.13.3) | **all 0s become 1** |

So rasterio 1.5.0 didn't pass `dst_nodata` to the warp kernel in a way that triggers the
avoidance, and 1.5.1 does. The rasterio change wasn't looked for.

odc-geo `xr_reproject(..., dst_nodata=None)` on an integer array resolves a fill value of 0 and
passes it to rasterio as `dst_nodata` (`odc/geo/_xr_interop.py`, `resolve_fill_value`;
`odc/geo/warp.py`). On rasterio ≥ 1.5.1 every valid 0 in an integer image becomes 1. In fast-ice
NormCovar the 0/1 landmask zoomed to 1/10 came out all 1, so the landmasked RGB passed to SAM is
entirely 0. fast-ice's lock (rasterio 1.5.0) was unaffected; a fresh resolve of its ranges is.

The GDAL side is behaving as designed. What could be asked upstream, if anything, is
documentation: the gdalwarp `-dstnodata` docs could say that colliding valid values are moved,
and from which version. The downstream issue belongs to odc-geo (fill value used as nodata) and
is the user's to raise.

Aside, same path: odc-geo's `_rio_reproject` always adds `XSCALE=1, YSCALE=1` (GDAL #7750
workaround), so its bilinear/cubic "downsample by 10" interpolates from the 2x2 neighbours with
no widening. See the 4-sample note for what XSCALE does and doesn't change on 3.13.
