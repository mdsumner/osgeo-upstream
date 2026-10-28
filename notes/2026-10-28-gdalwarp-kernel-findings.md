# gdalwarp kernel findings, 2026-10-28

Found while bringing hypertidy/rwarp's resampling kernels to parity with
gdalwarp (hypertidy/rwarp#3, branch `kernels/gdal-parity`), and while
answering questions 1-4 in charles-turner-bot/arrir#22 (`plans/warp.md`).

- GDAL source read at `739fcf03bf` (3.14.0dev). Line numbers are approximate
  and refer to `alg/gdalwarpkernel.cpp` unless a file is given.
- Behaviour checked with `gdalwarp` / `gdal.Warp` from the same build
  (`3.14.0dev-739fcf03bf`).
- Fixture generator: rwarp `tests/fixtures/kernels/gen.py`.
- Repro script: [2026-10-28-gdalwarp-kernel-repro.py](2026-10-28-gdalwarp-kernel-repro.py)
  (items 1, 2, 3, 5, 6, 7). Run on GDAL 3.8.4: items 2, 3, 5 and 6 reproduce
  there too, so they are long-standing; item 1 needs GDAL >= 3.11
  (`MODE_TIES`). Item 7 checked on 3.14.0dev only.
- All repros re-run on 2026-10-28 with `3.14.0dev-739fcf03bf`, which was
  OSGeo master that day.

Issue drafts from the rwarp sprint, one per upstream ticket, are in
[2026-10-28-gdalwarp-issue-drafts/](2026-10-28-gdalwarp-issue-drafts/README.md).
They are starting points; the upstream text is still to be written by me
(see README, "How contributions are made"). Filing order and todos are in
PLANS.md, "Warp kernels".

Status key: **confirmed** = reproduced with gdalwarp; **code reading** = from
the source only, not yet reproduced.

| # | Finding | Status | Kind |
|---|---|---|---|
| 1 | `MODE_TIES=MIN/MAX` ignored on a value's first occurrence (32/64-bit, float) | confirmed | likely bug |
| 2 | `MODE_TIES=FIRST` docs don't match behaviour | confirmed | docs |
| 3 | Kernel scale estimate ignores the chunk's destination offset | confirmed | likely bug |
| 4 | `average`/`mode` weight an edge pixel above 1 when the footprint overhangs | confirmed behaviour | may be intentional |
| 5 | Float working type defeats destination-nodata avoidance for integer outputs | confirmed | bug |
| 6 | Two rounding rules into integer outputs, depending on working type | confirmed | docs |
| 7 | `cubicspline` weight not zero beyond \|x\| = 2, so downsampled output is asymmetric | confirmed | minor bug |

## 1. `MODE_TIES=MIN|MAX` ignored on a value's first occurrence - confirmed, likely bug

**Where:** `GWKModeRealType<T>` (~L7147-7235) and `GWKModeComplexType`
(~L7409-7500). The histogram path in `GWKAverageOrModeThread`
(~L8115-8170) is used instead for Byte/Int8/UInt16/Int16.

**What:**

- In the list-of-values path, a value seen for the first time is appended
  with its weight, and becomes the mode only if there is no mode yet
  (`if (iModeIndex < 0) iModeIndex = i;`).
- It is never compared against the current mode, by count or by the tie
  rule. The histogram path compares on every increment, first occurrence
  included.
- So the same data gives different modes depending on the working data type.

```
[[5, 3], [7, 1]] warped to 1 pixel, -r mode
  Byte    FIRST 5  MIN 1  MAX 7
  Int32   FIRST 5  MIN 5  MAX 5
  Float32 FIRST 5  MIN 5  MAX 5
```

Larger fixture: a 64x64 source with four distinct values in every 2x2
block, warped 2:1 (rwarp `mode_distinct_*`). For both MIN and MAX, Int32 and
Float32 differ from Byte on 768 of 1024 pixels. FIRST agrees.

Related, code reading only: with fractional weights (partial source pixels
at window edges), a value seen once with a weight larger than the current
mode's accumulated count never becomes the mode in the list path, where the
histogram path would pick it. So FIRST can also differ by type when weights
are fractional.

**Tests:** `test_warp_mode_ties` (`autotest/alg/warp.py:1724`) covers ties
at a count of 3 in Int16/Int32 only.

**Suggested fix:** in the "add to arr" branch, compare the new entry against
the current mode the same way the increment branch does.

## 2. `MODE_TIES=FIRST` documentation doesn't match behaviour - confirmed, docs

**Where:** `alg/gdalwarper.cpp:1524`: "By default, the first value
encountered will be used."

**What:** ties are re-decided on every count increment, in scan order. So
FIRST keeps the tied value that first *reached* the winning count, which is
not necessarily the first value encountered.

```
[[5, 3], [3, 5]] warped to 1 pixel, MODE_TIES=FIRST -> 3, for every type
```

5 is encountered first, but 3 reaches a count of 2 first.

**Suggested fix:** reword, e.g. "the value that first reaches the maximum
count, in scan order".

## 3. Kernel scale estimate ignores the chunk's destination offset - confirmed, likely bug

**Where:** `GDALWarpKernel::PerformWarp` (~L1092-1295).

**What:**

- The sample points for estimating `dfXScale`/`dfYScale` are
  `dfX = iX * nDstXSize / (nPointsX - 1)` (and `dfY` likewise), in
  `0..nDst?Size`, passed to `pfnTransformer` without adding
  `nDstXOff`/`nDstYOff`.
- Every resampling thread does add the offsets
  (`padfX[iDstX] = iDstX + 0.5 + nDstXOff`).
- So in a multi-chunk warp each chunk estimates its scale over a region the
  size of the chunk at the top-left of the whole output. The estimate
  depends on the chunk's size, never on its position.

**Repro:** a lon/lat source (3600 x 1600, 0.1 degree, 80N to 80S) warped to
EPSG:3857 (400 x 800, cubic, `-et 0`), where the y scale varies with
latitude, once with a large warp memory limit and once with 1 MB to force
chunking. `CPL_DEBUG=ON` logs `dfXScale = ...` and each chunk's Src/Dst
windows.

Observed with `3.14.0dev-739fcf03bf`:

- Every 100x100 chunk logs `dfYScale = 1.244978`, at destination rows 0,
  100 and 200 alike. Every 100x50 chunk logs `1.424308`.
- The chunks' source windows show the true local y scale differs: rows
  100-199 have 100 destination rows per 154 source rows (about 0.65); rows
  200-299 have 100 per 252 (about 0.40).
- So those chunks are treated as upsampling (no widening) when they are
  downsampling. The single-chunk run logs `dfYScale = 0.778956`.
- Chunked output differs from single-chunk output in 319,985 to 320,000
  of 320,000 pixels (varies by run), by up to 0.113 on data in [0, 1].
- Also present on GDAL 3.8.4: 319,999 of 320,000 pixels differ, by up to
  0.196 (repro script).

**Effect:** in any multi-chunk warp whose scale varies over the output (most
reprojections of large rasters), bilinear, cubic, cubicspline and lanczos
are widened by the wrong amount away from the output's top-left. Average
and mode use the scale only for their corner-range margin.

**Suggested fix:** add `nDstXOff`/`nDstYOff` to the sample points, or wrap
the transformer the way the threads do.

**Note:** the `XSCALE`/`YSCALE` docs already warn that the per-chunk
estimate can vary between chunks. This is about it being taken at the wrong
place. rwarp's `estimate_scale` adds the offset.

## 4. `average`/`mode` weight an edge pixel above 1 when the footprint overhangs - confirmed behaviour, may be intentional

**Where:** `COMPUTE_WEIGHT_Y` / `COMPUTE_WEIGHT` (~L6849) with
`GWKAverageOrModeComputeSourceCoords` (~L6919).

**What:**

- `iSrcXMin = max(floor(dfXMin + eps), 0)`.
- When the transformed box starts left of the source (`dfXMin < 0`), the
  first column's weight is `1 - (dfXMin - iSrcXMin) = 1 - dfXMin`, which is
  greater than 1. The last column and the rows behave the same at the far
  edges.
- So source edge pixels are overweighted, roughly in proportion to how far
  the destination pixel hangs off the source.

**Repro:** rwarp fixture `average_overhang`: a 20x20 destination of 4-unit
pixels over [-8, 72] squared, against a 64x64 source. rwarp matches GDAL
exactly only when it applies the same >1 weights.

**Question for upstream:** intended (extrapolating the edge value into the
missing area) or not? A clipped footprint would use
`1 - (max(dfXMin, 0) - iSrcXMin)`.

Context: `average` measures overlap in source pixel space, on the
axis-aligned box between the transformed top-left and bottom-right corners
of the destination pixel (`GWKAverageOrModeComputeLineCoords` ~L6873; the
code calls it "an approximative fix"). With rotation the box can collapse:
for a 45 degree pixel gdalwarp gives 5.0 where the exact area-weighted mean
is 4.5.

## 5. Float working type defeats destination-nodata avoidance for integer outputs - confirmed

**Where:** `AvoidNoData` (~L1613) runs in the kernel on the working-type
value. Conversion to the output type happens afterwards, in `GDALCopyWords`
(`gcore/gdal_priv_templates.hpp`; float to int rounds half away from zero).

**What:**

- With a float working type (e.g. a Float32 source warped to `-ot Byte`),
  the kernel compares the float result with the destination nodata. 0.2 is
  not equal to nodata 0, so it isn't adjusted.
- It is then rounded to 0 on write, which is nodata. A valid pixel silently
  becomes nodata, with no warning.
- With an integer working type, the same case is adjusted to 1, with a
  warning.

```
Float32 1x2 [[0.2, 1.0]], -r near, -dstnodata 0, -ot Byte -> [[0, 1]]
```

**Suggested fix:** when the destination band is an integer type and differs
from the working type, also apply the avoidance check to the value after
rounding to the destination type; or check at write time.

## 6. (Minor) Two rounding rules into integer outputs - confirmed, docs

Rounding into an integer output depends on the working type, i.e. on the
source type:

- **Integer working type:** the kernel rounds half up (`floor(x + 0.5)`,
  `ClampRoundAndAvoidNoData` ~L1856), so -2.5 becomes -2.
- **Float working type:** `GDALCopyWords` rounds half away from zero, so
  -2.5 becomes -3.

So an Int16 source and a Float32 source with the same values, both averaged
into Int16, can differ by 1 on negative halves. Probably not worth changing;
worth a sentence in the gdalwarp docs (`-ot`, `-wt`).

## 7. `cubicspline` weight not zero beyond |x| = 2 - confirmed, minor bug

**Where:** `GWKBSpline()` and `GWKBSpline4Values()` (~L3461-3510 in a 2024
checkout; the functions are unchanged in shape).

**What:**

- The cubic B-spline is evaluated as a sum of truncated cubics,
  `(x+2)^3_+ - 4(x+1)^3_+ + 6x^3_+ - 4(x-1)^3_+`, leaving out the last term
  `+(x-2)^3_+`.
- For x < -2 the function returns 0, but for x > 2 the four terms sum to
  `-(x-2)^3` (unnormalised) instead of 0.
- At scale 1 the window never reaches |x| > 2. When downsampling, the window
  is widened to `ceil(2 / scale)` and evaluated at `(i - delta) * scale`,
  which goes past 2, so taps on the positive side only get small negative
  weights.

**Repro:** a source symmetric about its centre, downsampled 64 -> 23 columns
over the same bounds (repro script, item 7):

```
cubicspline  max |out - mirror(out)| = 5.83e-05
cubic        max |out - mirror(out)| = 0
lanczos      max |out - mirror(out)| = 0
```

**Suggested fix:** return 0 for |x| >= 2 (or add the missing term) in both
functions. Small effect (about 1e-4 relative here) but a systematic
one-sided bias. rwarp already clips.

## Not bugs, recorded for reference

- **Kernel widening.** `-wo XSCALE=1 -wo YSCALE=1` turns it off: those
  override the per-chunk scale estimate (~L1289-1292). The support radius is
  `ceil(radius / scale)` only when scale < 1 (~L1319); the kernel is
  evaluated at `(i - delta) * scale` with scale clamped to at most 1
  (~L4854, ~L4964). Bilinear and cubic widen only once scale <= 0.5 (above
  that GDAL uses the 4-sample point formula, `CanUse4SamplesFormula`
  ~L1041); lanczos widens at any scale below 1.
- **Geolocation arrays.** `GEOREFERENCING_CONVENTION` defaults to
  `TOP_LEFT_CORNER` (`alg/gdalgeoloc.cpp`, `GDALCreateGeoLocTransformerEx`).
  CF-style centre coordinates read through the default land half a cell
  off; `PIXEL_CENTER` places cell edges at midpoints between centres.
  Tested in hypertidy/rwarp#2 (GDAL 3.8.4). Whether the netCDF driver sets
  `PIXEL_CENTER` itself for CF coordinates: to check.
- **Warping to a curvilinear target** works with `DST_METHOD=GEOLOC_ARRAY`
  and a target dataset carrying geolocation arrays (hypertidy/rwarp#2,
  GDAL 3.8.4). Whether a warped VRT can serialise a destination geolocation
  transformer is unchecked.
