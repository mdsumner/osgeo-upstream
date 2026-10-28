# gdalwarp kernel findings, 2026-10-28

Found while bringing hypertidy/rwarp's resampling kernels to parity with
gdalwarp (rwarp branch `kernels/gdal-parity`), and while answering questions
1-4 in charles-turner-bot/arrir#22 (`plans/warp.md`).

GDAL source read at `739fcf03bf` (3.14.0dev); oracle gdalwarp from the same
build. Fixtures: rwarp `tests/fixtures/kernels/gen.py` on that branch.
Line numbers are approximate (`alg/gdalwarpkernel.cpp` unless stated).
Upstream issue text, if any, still to be written (see README, "How
contributions are made").

Status per item: **tested** means a gdalwarp fixture shows it; **code** means
read from source only.

## 1. `MODE_TIES` ignored on a value's first occurrence (wider types) - tested

gdalwarp's mode has two implementations:

- 8/16-bit working types: a histogram, compared against the current mode on
  every pixel (~L8115-8170).
- Int32/UInt32/64-bit/Float: a list of values (`GWKModeRealType`,
  ~L7147-7235; `GWKModeComplexType` ~L7480). A value seen for the first time
  is appended but never compared against the current mode, for count or for
  ties.

Effect: with `-wo MODE_TIES=MIN` or `MAX`, the answer depends on the data
type.

```
2x2 block [[5,3],[7,1]], warped 2:1, -r mode -wo MODE_TIES=MIN
  Byte          -> 1
  Int32/Float32 -> 5
```

Fixture `mode_distinct_*` (every 2x2 block has four distinct values, warped
2:1): Int32 and Float32 differ from Byte on 768 of 1024 pixels for MIN and
for MAX. FIRST agrees.

Related, code only: with fractional weights, a once-seen value with a large
weight can never displace a mode that has a smaller accumulated weight, so
FIRST can also differ between types.

`test_warp_mode_ties` (`autotest/alg/warp.py:1724`) does not cover a tie at
first occurrence.

Possible fix: compare a new list entry against the current mode as the
histogram path does.

## 2. `MODE_TIES=FIRST` documentation - tested

The docs say FIRST keeps "the first value encountered". The code keeps the
value that first *reaches* the winning count: on each increment, a strictly
greater count takes over and an equal count goes to the tie rule, which for
FIRST keeps the current mode.

```
[[5,3],[3,5]], -r mode (default MODE_TIES=FIRST) -> 3
```

5 is encountered first, but 3 reaches a count of 2 first. A docs wording
fix, unless the behaviour is the thing to change.

`MODE_TIES` exists since 3.11 (`gdalwarper.cpp:1524`, `:1549`).

## 3. Scale estimate ignores the chunk offset - code, unverified

`PerformWarp` estimates the source/destination scale (which drives kernel
widening) by sampling destination points `0..nDstXSize` without adding
`nDstXOff`/`nDstYOff` (~L1114-1140). Every resampling thread does add the
offsets. In a multi-chunk warp, each chunk's scale would then be estimated
at the location of the origin chunk rather than its own.

To check: a multi-chunk warp (small `-wm`, or `-wo` chunk size) where the
scale varies strongly across the output, e.g. a polar stereographic target
from a global longitude/latitude source; compare against a single-chunk
warp.

## 4. `average`: edge pixel weight above 1 when the footprint overhangs - code

In `COMPUTE_WEIGHT` (~L6849) the box start is clamped to 0
(`iSrcXMin`) but the partial fraction is not, so when a destination pixel's
footprint overhangs the source buffer edge, the edge pixel gets weight > 1.
Possibly intentional (it extends the edge value). Worth asking.

Context, tested: `average` measures overlap in source pixel space on the
axis-aligned box between the transformed top-left and bottom-right corners
of the destination pixel (`GWKAverageOrModeComputeLineCoords` ~L6873,
`GWKAverageOrModeComputeSourceCoords` ~L6919, which the code calls "an
approximative fix"). With rotation the box can collapse: for a 45 degree
pixel gdalwarp gives 5.0 where the exact area-weighted mean is 4.5.

## 5. Float working type defeats destination nodata avoidance - from fixtures

`AvoidNoData` checks the float value before `GDALCopyWords` rounds it to
the output type. A Float32 working value 0.2 written to Byte with
`-dstnodata 0` passes the check and then rounds to 0, so a valid pixel
silently becomes nodata.

To check: the exact repro command, and whether the rounding happens in
`GDALCopyWords` for every output type.

## Not bugs, recorded for reference

- **Kernel widening.** `-wo XSCALE=1 -wo YSCALE=1` turns it off: those
  override the per-chunk scale estimate (~L1289-1292). The support radius is
  `ceil(radius / scale)` only when scale < 1 (~L1319); the kernel is
  evaluated at `(i - delta) * scale` with scale clamped to at most 1
  (~L4854, ~L4964). Bilinear and cubic widen only once scale <= 0.5 (below
  that GDAL uses the 4-sample point formula, `CanUse4SamplesFormula`
  ~L1041); lanczos widens at any scale below 1.
- **Geolocation arrays.** `GEOREFERENCING_CONVENTION` defaults to
  `TOP_LEFT_CORNER` (`alg/gdalgeoloc.cpp`, `GDALCreateGeoLocTransformerEx`).
  CF-style centre coordinates read through the default land half a cell
  off; `PIXEL_CENTER` places cell edges at midpoints between centres.
  Tested in hypertidy/rwarp#2. The netCDF driver may or may not set
  `PIXEL_CENTER` itself for CF coordinates: to check.
- **Warping to a curvilinear target** works with `DST_METHOD=GEOLOC_ARRAY`
  and a target dataset carrying geolocation arrays (tested in
  hypertidy/rwarp#2, GDAL 3.8.4). Whether a warped VRT can serialise a
  destination geolocation transformer is unchecked.
