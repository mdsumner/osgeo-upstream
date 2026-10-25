# Priorities

Provisional, 2026-10-25. Ordered by value to me and to downstream users,
then by how cheaply a maintainer can say yes. Revisit after each upstream
merge or rejection.

## Now (P1)

1. **mdim get-refs (#36, PR #14677).** The most valuable open work: byte
   references for multidimensional arrays feed virtual stores (Kerchunk,
   Icechunk, VirtualiZarr) and wxylib, which uses GDAL as a test oracle.
   Before more code: confirm the PR's state and read the last review, then
   decide the route (STRATEGY.md, "get-refs route").
2. **Zarr V3 fill_value vs nodata survey (#39 WP7a).** Tracker-only work, no
   upstream text needed yet, and it underpins several Zarr bugs. Output: a
   note with small test stores from zarr-python, xarray and GDAL, and what
   each reader does.
3. **Zarr small bugs from #39 (WP2, then WP1).** Confirm each on master, keep
   a repro here, then file one short issue at a time.

## Next (P2)

4. Longitude wrap and extent densification (#28, #30): small, clear,
   illustrated repros; fits my polar data work.
5. ReadCompressedData in Python (#35): small binding gap, related to byte
   access.
6. `mdim info --detailed` default limit (#34): only if #13723 is abandoned.
7. Capture the upstream issues I opened, so CONTRIBUTIONS.md is complete.
8. Zarr codec drafts (JPEG, TIFF predictor): ask upstream first.
9. Rogues gallery from raad (#13): a source of repros and figures.

## Later (P3)

Everything else in PLANS.md, plus housekeeping: two doc fixes, the PROJ
patch-1 leftover, and deleting the 65 merged or superseded fork branches.
