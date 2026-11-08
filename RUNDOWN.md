# Rundown

Generated 2026-11-08 by `scripts/rundown.py` from the open issues; do not edit.
Ranked by priority label, then status (ready, upstream, investigating,
idea, parked), then items that block downstream work.
New gap found downstream? Open an issue with the
[upstream gap form](../../issues/new?template=upstream-gap.yml).
Order and reasons: [PRIORITIES.md](PRIORITIES.md);
items without an issue yet: [PLANS.md](PLANS.md).

## Inbox: needs a priority label

| # | Item | Found in | Suggested |
|---|---|---|---|
| [#48](https://github.com/mdsumner/osgeo-upstream/issues/48) | warp issue oisst: invalid latitude | - | ? |
| [#49](https://github.com/mdsumner/osgeo-upstream/issues/49) | mdim: 3 fixes for GDAL | - | ? |

## Now (P1)

| # | Item | Area | Status | Found in | Idle |
|---|---|---|---|---|---|
| [#42](https://github.com/mdsumner/osgeo-upstream/issues/42) | Zarr codec drafts: JPEG and TIFF predictor | gdal:zarr | ready | - | 4d |
| [#50](https://github.com/mdsumner/osgeo-upstream/issues/50) | gdalwarp: kernel scale estimate ignores the chunk's destination offset | gdal:warp | ready | wxylib | 11d |
| [#59](https://github.com/mdsumner/osgeo-upstream/issues/59) | Test GDAL PR 15305: Zarr V3 scale_offset and cast_value read | gdal:zarr | ready | - | 3d |
| [#36](https://github.com/mdsumner/osgeo-upstream/issues/36) | get-refs todo | gdal:mdim | upstream | wxylib | 14d |
| [#39](https://github.com/mdsumner/osgeo-upstream/issues/39) | Triage: closed GDAL PRs 15388-15398 (Zarr / multidim / AdviseRead) | gdal:zarr | investigating | wxylib | 14d |
| [#41](https://github.com/mdsumner/osgeo-upstream/issues/41) | Zarr V3 fill_value vs nodata: survey of writers and readers | gdal:zarr | investigating | wxylib | 14d |

## Next (P2)

| # | Item | Area | Status | Found in | Idle |
|---|---|---|---|---|---|
| [#51](https://github.com/mdsumner/osgeo-upstream/issues/51) | gdalwarp mode: a value seen once never becomes the mode (32/64-bit ... | gdal:warp | ready | wxylib | 11d |
| [#62](https://github.com/mdsumner/osgeo-upstream/issues/62) | gdalwarp: target across the antimeridian reads a full-width source ... | gdal:warp | ready | - | 0d |
| [#53](https://github.com/mdsumner/osgeo-upstream/issues/53) | gdalwarp average/mode: antimeridian check skips a chunk's last column | gdal:warp | investigating | wxylib | 11d |
| [#55](https://github.com/mdsumner/osgeo-upstream/issues/55) | Geolocation arrays: spiral search, antimeridian and backmap edge fi... | gdal:warp | investigating | wxylib | 11d |
| [#56](https://github.com/mdsumner/osgeo-upstream/issues/56) | CENTER_LONG: special points, %g rounding and the --config wrap of t... | gdal:warp | investigating | wxylib | 11d |
| [#13](https://github.com/mdsumner/osgeo-upstream/issues/13) | rogues gallery from raad | gdal:drivers | idea | - | 14d |
| [#16](https://github.com/mdsumner/osgeo-upstream/issues/16) | Warp: from unscaled geolocation arrays | gdal:warp | idea | - | 14d |
| [#28](https://github.com/mdsumner/osgeo-upstream/issues/28) | remaining problems with longitude wrap for warp | gdal:warp | idea | - | 14d |
| [#30](https://github.com/mdsumner/osgeo-upstream/issues/30) | GDAL Issue: wgs84Extent should densify edges before reprojection fo... | gdal:warp | idea | - | 14d |
| [#34](https://github.com/mdsumner/osgeo-upstream/issues/34) | pick up the mdim info detailed PR | gdal:mdim | idea | - | 14d |
| [#35](https://github.com/mdsumner/osgeo-upstream/issues/35) | expose ReadCompressedData() to python | gdal:python | idea | wxylib | 14d |
| [#40](https://github.com/mdsumner/osgeo-upstream/issues/40) | Capture upstream issues I opened (GDAL, PROJ, GEOS) | - | idea | - | 14d |
| [#47](https://github.com/mdsumner/osgeo-upstream/issues/47) | Multidim VRT: sources without a SourceSlab count are opened on read... | gdal:mdim, gdal:vrt | idea | wxylib | 13d |
| [#7](https://github.com/mdsumner/osgeo-upstream/issues/7) | gdal warp and snap | gdal:warp | parked | - | 14d |

## Later (P3)

<details><summary>18 items</summary>

| # | Item | Area | Status | Found in | Idle |
|---|---|---|---|---|---|
| [#44](https://github.com/mdsumner/osgeo-upstream/issues/44) | Two unsent GDAL doc fixes | gdal:docs | ready | - | 14d |
| [#46](https://github.com/mdsumner/osgeo-upstream/issues/46) | Delete 65 merged or superseded GDAL fork branches | - | ready | - | 14d |
| [#61](https://github.com/mdsumner/osgeo-upstream/issues/61) | NSIDCbin: north geotransform origin is half a cell off (cell centre... | gdal:drivers | ready | - | 1d |
| [#63](https://github.com/mdsumner/osgeo-upstream/issues/63) | GTiff: AdviseRead() is a no-op, so separate windows over /vsicurl/ ... | gdal:drivers | ready | - | 0d |
| [#52](https://github.com/mdsumner/osgeo-upstream/issues/52) | gdalwarp: source window padding ignores XSCALE/YSCALE | gdal:warp | investigating | wxylib | 11d |
| [#54](https://github.com/mdsumner/osgeo-upstream/issues/54) | gdalwarp -cutline: all-touched, tolerance and blend findings from r... | gdal:warp | investigating | wxylib | 11d |
| [#10](https://github.com/mdsumner/osgeo-upstream/issues/10) | gdalwarp crs-only heuristics | gdal:warp | idea | - | 14d |
| [#15](https://github.com/mdsumner/osgeo-upstream/issues/15) | Footprint could use geolocation arrays | gdal:warp | idea | - | 14d |
| [#17](https://github.com/mdsumner/osgeo-upstream/issues/17) | add sum to resampling (for overviews) | gdal:warp | idea | - | 14d |
| [#24](https://github.com/mdsumner/osgeo-upstream/issues/24) | HDF5 group variant (sinusoidal) | gdal:mdim | idea | - | 14d |
| [#26](https://github.com/mdsumner/osgeo-upstream/issues/26) | warp disparate inputs | gdal:warp | idea | - | 14d |
| [#27](https://github.com/mdsumner/osgeo-upstream/issues/27) | tiff explore | gdal:drivers | idea | - | 14d |
| [#29](https://github.com/mdsumner/osgeo-upstream/issues/29) | relation of kernel stats to zonal stats to rasterizing and raster t... | gdal:warp | idea | - | 14d |
| [#32](https://github.com/mdsumner/osgeo-upstream/issues/32) | GNM crash and failures | gdal:drivers | idea | - | 14d |
| [#37](https://github.com/mdsumner/osgeo-upstream/issues/37) | eager configure pyarrow/sedonadb problem | gdal:python | idea | - | 14d |
| [#38](https://github.com/mdsumner/osgeo-upstream/issues/38) | nulls in Parquet domain (implicit zero) | gdal:drivers | idea | - | 14d |
| [#43](https://github.com/mdsumner/osgeo-upstream/issues/43) | netCDF vector timeseries draft | gdal:netcdf | parked | - | 14d |
| [#45](https://github.com/mdsumner/osgeo-upstream/issues/45) | PROJ: unsent "param arg form" commit on patch-1 | proj | parked | - | 14d |

</details>

## Waiting on upstream

- [#36](https://github.com/mdsumner/osgeo-upstream/issues/36) get-refs todo

## Open items by area

| Area | P1 | P2 | P3 | Inbox |
|---|---|---|---|---|
| (none) | 0 | 1 | 1 | 2 |
| gdal:docs | 0 | 0 | 1 | 0 |
| gdal:drivers | 0 | 1 | 5 | 0 |
| gdal:mdim | 1 | 2 | 1 | 0 |
| gdal:netcdf | 0 | 0 | 1 | 0 |
| gdal:python | 0 | 1 | 1 | 0 |
| gdal:warp | 1 | 9 | 7 | 0 |
| gdal:zarr | 4 | 0 | 0 | 0 |
| proj | 0 | 0 | 1 | 0 |
