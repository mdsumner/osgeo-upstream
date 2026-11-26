# Index and strided MDArray reads of classic rasters, 2026-11-26

Found with gdalraster on the BedMachine v4.1 multidim VRT published by
raad.virtualize. Each of its arrays is a `<SourceBand>` over a 13333 x 13333
GeoTIFF. `getView("[::14,::14]")` failed with "Requested (0,0) of size
13342x13342 on raster of 13333x13333". The same window computation also
breaks index views, which fail silently.

- Source read at master `948f102a` (2026-11-25). No commits touch
  `gcore/gdalrasterband.cpp`, `gcore/gdaldataset.cpp` or `gcore/multidim/`
  since 2026-11-01.
- Repro: [2026-11-26-mdim-classic-strided-read-repro.py](2026-11-26-mdim-classic-strided-read-repro.py).
  Output is identical on 3.12.3, 3.13.3, `3.14.0dev-9c765f0bdd` (the
  osgeo/gdal ubuntu-small-latest image, 2026-11-07) and the local build
  `3.14.0dev-fedfd3ec89-dirty`. That version string dates from configure time,
  and the build tree had the numcodecs PR 1 branch (LEDGER 2026-11-22), so
  quote the image upstream, not this build.
- No matching upstream issue or PR. Searched 2026-11-26 with `gh search` for
  "AsMDArray", "GDALMDRasterIOFromBand", "GDALMDArrayFromRasterBand",
  "GetView strided", "Access window out of range AsMDArray".
- Issue draft: [2026-11-26-mdim-classic-strided-read-issue.md](2026-11-26-mdim-classic-strided-read-issue.md).

| # | Request | Result | Kind |
|---|---|---|---|
| 1 | Index view, e.g. `GetView("[0]")` | Read() succeeds without writing the buffer; a VRT returns its fill value (0) | silent wrong values |
| 2 | Step that does not divide the extent, e.g. `[::2,::2]` on 5 x 5 | "Access window out of range": requests 6 x 6 | error |
| 3 | Step that divides the extent, e.g. `[::2,::2]` on 6 x 6 | nearest decimation: columns 1, 3, 5, not 0, 2, 4 | silent wrong values |
| 4 | As 3, on a band with overviews | values from the overview (AVERAGE: 4 = mean of 0, 1, 6, 7, rounded) | silent wrong values |

Affected: `GDALRasterBand::AsMDArray()`, `GDALDataset::AsMDArray()`,
`GDALMDArray::GetResampled()`, and multidim VRT sources that use the first
two (repro items 1-7). A plain `Read()` with step 1 is correct (item 8).

## Cause

Two `ReadWrite()` implementations compute the RasterIO window per axis as
`count * |step|`:

- `GDALMDRasterIOFromBand()`, `gcore/gdalrasterband.cpp:11424`. Used by
  `GDALMDArrayFromRasterBand` (`Band::AsMDArray()`, VRT `<SourceBand>`) and
  by `GDALMDArrayResampled` (`gcore/multidim/gdalmultidim_array_resampled.cpp:841`).
- `GDALMDArrayFromDataset::ReadWrite()`, `gcore/gdaldataset.cpp:12408`.
  Used by `Dataset::AsMDArray()`, and by a VRT source with neither
  `<SourceArray>` nor `<SourceBand>` (`frmts/vrt/vrtmultidim.cpp`, around
  line 2152).

The extent a strided request covers is `(count - 1) * |step| + 1`, as in
`GDALMDArray::ReadUsingContiguousIRead()`
(`gcore/multidim/gdalmultidim_array.cpp:1277`).

Index views: `GDALSlicedMDArray` (`gcore/multidim/gdalmultidim_array_view.cpp:250`)
sets the parent step only for the dimensions it keeps. A dimension removed by
an index keeps the 0 from the constructor
(`m_parentStep(m_poParent->GetDimensionCount())`, line 68), with count 1. The
window is then `1 * 0 = 0` rows, and `GDALRasterBand::RasterIO()` returns
`CE_None` without reading. With `CPL_DEBUG=ON` it logs "RasterIO() skipped
for odd window or buffer size. Window = (0,0)x5x0, Buffer = 5x1"
(`gcore/gdalrasterband.cpp:378`).

Decimation: a `count * step` window read into `count` cells is a resampled
RasterIO (nearest, since `psExtraArg` is null). When the buffer is smaller
than the window the band can serve it from an overview (observed in item 4;
the overview selection code was not read).

## Fix considerations (for the PR, if one follows)

- A window of `(count - 1) * |step| + 1` fixes 1 and 2, and is exact for
  step 1 and for count 1.
- For step > 1 that is not enough. A RasterIO of that window into `count`
  cells is still a nearest resample, with a ratio that is not the step.
  Checked with MEM: 20 pixels, step 3 gives 1, 4, 6, 9 (expected 0, 3, 6, 9);
  13333 pixels, step 14 gives 6, 20, 34, 48. Overviews would still apply.
- Exact picks need full-resolution reads. Two options, neither tried:
  - Read the covering window into a temporary buffer and pick from it, as
    `ReadUsingContiguousIRead()` does. Memory is the whole covering window:
    about 710 MB for the BedMachine case (13329 x 13329 Float32).
  - Read row by row: for each output row, one full-resolution row of
    `(count_x - 1) * step_x + 1` pixels, then copy every `step_x`-th value.
- How to fix it is the maintainers' call; the issue reports and links this.

## Side finding

`AsMDArray()` on a second MEM dataset created with an empty name fails with
"An existing shared dataset already has this description. This should not
happen." `AsMDArray()` marks the dataset as shared, and two unnamed MEM
datasets collide. Named ones work. Seen while writing the issue snippet on
`3.14.0dev-9c765f0bdd`; not investigated.

## Downstream: raad.virtualize

Every published mdim.vrt uses `<SourceBand>` sources: BedMachine 60, Bedmap3
42, GEBCO 2026 8, IBCSO v2 28, GHRSST MUR 53604 (counts from the 2026-11-26
re-renders). So with any GDAL up to current master:

- an index view such as `[0]` returns the fill value;
- a strided view fails or returns decimated or overview values;
- contiguous slices are correct.

Workaround: read a contiguous window and subsample it in the client. For
display, use the declared overviews (raad.virtualize PR #122) through
`AsClassicDataset()`.

## Related

[2026-10-28-mdim-vrt-findings.md](2026-10-28-mdim-vrt-findings.md) item 1
covers strided reads across VRT sources ("arrayStartIdx[0] = N >= 1"). That
is a different path (VRT source selection), but its repro also uses
`<SourceBand>`, so recheck it after this is fixed.
