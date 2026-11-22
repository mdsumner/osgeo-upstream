# Warp: bilinear/cubic stopped widening for downsampling < 2x in GDAL 3.13, 2026-11-10

Found in geo-stack-alt (clean-room comparison of a pip/rasterio stack with a pixi/osgeo.gdal + R
stack), where the same warp gave two answers. Evidence there: `evidence/warp-*/` and
`findings/2026-11-10-gdal-3.13-warp.md` (local repo, not yet on GitHub).

- Repro: [2026-11-10-warp-4sample-threshold-repro.py](2026-11-10-warp-4sample-threshold-repro.py)
  (offline, synthetic). Run under conda-forge GDAL 3.12.4 and 3.13.3 (pixi, clean ubuntu:24.04
  container) and local `3.14.0dev-fa1fc3c77e`.
- Source read at tags v3.12.4 and v3.13.3, `alg/gdalwarpkernel.cpp`.
- Relates to [2026-10-28-gdalwarp-kernel-findings.md](2026-10-28-gdalwarp-kernel-findings.md):
  its "Not bugs" bullet on kernel widening describes the 3.13+ rule; this note dates it and
  measures it.

**Kind:** intentional behaviour change, under-described in NEWS. Not a bug as such.

## What changed

OSGeo/gdal `7e18bd36cf` (2026-01-29, first in 3.13.0), "Warper: improve XSCALE/YSALE
computation logic when the target shape is quite different from the source shape". Besides
the new scale estimate, it moved the switch between the 4-sample point formula and the
generalized (widened) kernel for bilinear and cubic:

```c
// v3.12.4, PerformWarp()
const int bUse4SamplesFormula = dfXScale >= 0.95 && dfYScale >= 0.95;
// v3.13.3 and master, CanUse4SamplesFormula() ~L1041
if (poWK->dfXScale > 0.5 && poWK->dfYScale > 0.5) return true;
```

Commit message: "Previously we only used the 4-sample formula if not downsampling (with a margin
error of 5%). Increase that tolerance to allow up to a 50% downsampling." NEWS (3.13.0,
Algorithms) has only the first line of the commit, which mentions the scale computation, not
this.

## Effects (repro output)

1. Bilinear and cubic downsampling by factors in (1, 2) is now bit-identical to
   `-wo XSCALE=1 -wo YSCALE=1`. 3.12 widened. From 2x on, both widen. Lanczos (control) widens
   at any scale < 1 in both.
2. On that 4-sample path XSCALE/YSCALE are not read: for a 1.75x downsample, explicit values
   1, 0.9, 0.7, 0.571, 0.51 all give the same output on 3.13+ (3.12: up to 87 apart on data in
   [0, 200]). Only <= 0.5 switches to the widened kernel, at a different width from 3.12's. So
   there is no warp option that reproduces 3.12 output in this range.
3. Real data: Copernicus DEM 30 m COG (`Copernicus_DSM_COG_10_S43_00_E146_00_DEM`, /vsicurl/)
   to a 40 km EPSG:3577 box at 40 m, bilinear (source ~23 x 31 m, so 1.3-1.75x). 3.10, 3.11 and
   3.12 identical; 3.13 differs in 99.6% of cells, median 0.32 m, max 10.9 m, ~4% rougher.
   `CPL_DEBUG` on 3.13 logs `dfXScale = 0.588881, dfYScale = 0.746642` for this warp, then
   uses the 4-sample formula, which ignores them.
4. Same-CRS integer 2x downsampling is unaffected for Byte/Int16/Float32/Float64.

Packaging consequence: rasterio 1.5.2 wheels bundle GDAL 3.12.2 and pyogrio 0.13.0 bundles
3.12.4, so pip users get the old behaviour today and the new one silently on upgrade.

## Interaction with kernel findings item 3

Item 3 (chunk scale estimate ignores the destination offset) matters for bilinear/cubic only
where the estimate decides between 4-sample and widened. In 3.13+ that switch is at 0.5, not
0.95, so a wrong per-chunk estimate in (0.5, 1) no longer changes bilinear/cubic output, while
one crossing 0.5 does. The COP90 Tasmania case (2.37 m) was on 3.14.0dev, so already under the
new rule. Lanczos and cubicspline are unaffected by this change.

## Possible upstream asks (decide; text to be written by me)

- A NEWS / migration note for 3.13 saying bilinear/cubic results change for downsampling
  factors below 2.
- Doc sentence in gdalwarp `-r` / `XSCALE` that values > 0.5 are ignored by bilinear/cubic.
- Optionally a warp option to require the generalized kernel (the 3.12 behaviour).
- Which output is "right" is a design choice: 3.12 is smoother (less aliasing), 3.13 is
  closer to point interpolation (sharper). Frame as documentation, not as a regression.
