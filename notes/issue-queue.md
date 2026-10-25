# Issue queue (2026-10-25)

Tracker issues and labels to apply once write access to this repo works.
Delete this file after it has been applied.

## New issues

| Title | Labels |
|---|---|
| Capture upstream issues I opened (GDAL, PROJ, GEOS) | status:idea, P2 |
| Zarr V3 fill_value vs nodata: survey of writers and readers (from #39 WP7a) | gdal:zarr, status:investigating, P1, wxylib |
| Zarr codec drafts: JPEG and TIFF predictor (branches zarr-jpeg, zarr-tiff-predictor-DRAFT) | gdal:zarr, status:idea, P2 |
| netCDF vector timeseries draft (branch netcdf-vector-timeseries) | gdal:netcdf, status:parked, P3 |
| Two unsent doc fixes: mdim mosaic typos, gdal_footprint.rst (patch-15, mdsumner-patch-1) | gdal:docs, status:ready, P3 |
| PROJ: unsent "param arg form" commit on patch-1 | proj, status:parked, P3 |
| Delete 65 merged or superseded GDAL fork branches | status:ready, P3 |

## Comments on existing issues

- #36: branch and PR status of the get-refs cluster (feature/mdim-get-refs =
  PR #14677 unmerged; mdim-helpers, stage1-mvp, fast-path-h5-chunk-refs-iter
  have no PR); link STRATEGY.md "get-refs route".
- #1: 22 vrt:// options merged (list in CONTRIBUTIONS.md); two branches left
  (vrtcon-no-value-options2, vrtcon-key-value-required).
- #7: branch warp-tap-with-ts drafts `-tap` with `-ts`.
- #23: GDAL now reads Kerchunk JSON/Parquet refs and has an Icechunk driver;
  close unless something specific is left.

## Labels on existing open issues

| Issue | Labels |
|---|---|
| #1 | gdal:vrt, status:done, P3 |
| #7 | gdal:warp, status:parked, P2 |
| #10, #26 | gdal:warp, status:idea, P3 |
| #13 | gdal:drivers, status:idea, P2 |
| #15, #17 | gdal:warp, status:idea, P3 |
| #16, #28, #30 | gdal:warp, status:idea, P2 |
| #23 | gdal:zarr, status:done |
| #24 | gdal:mdim, status:idea, P3 |
| #27, #32, #38 | gdal:drivers, status:idea, P3 |
| #29 | gdal:warp, status:idea, P3 |
| #34 | gdal:mdim, status:idea, P2 |
| #35 | gdal:python, status:idea, P2, wxylib |
| #36 | gdal:mdim, status:upstream, P1, wxylib |
| #37 | gdal:python, status:idea, P3 |
| #39 | gdal:zarr, status:investigating, P1, wxylib |
