# Ledger

Each learnt fact, with the check that guards it. Re-run the check before
relying on the fact.

| Date | Fact | Check |
|---|---|---|
| 2026-10-25 | 56 commits authored by me are on GDAL master (excluding one merge commit) | `scripts/sweep.sh`, then `wc -l data/gdal_authored.psv` (57 lines, one is a merge) |
| 2026-10-25 | 42 upstream GDAL PRs carry my commits; 28 merged by squash or merge, the rest superseded, duplicated or unmerged | `data/gdal_prs.psv` from `scripts/sweep.sh` |
| 2026-10-25 | PR #14569 (GuessGeoTransform) shows as unmerged by PR number but its commit 7e0e87ad6 is on master (rebased in) | `git merge-base --is-ancestor 7e0e87ad6 master` in the sweep clone |
| 2026-10-25 | Closed PRs 15388-15398 (#39) were authored by another contributor, not me | `git log -1 --format=%an refs/pr/15388` |
| 2026-10-25 | Fork branch zarr_list_array_sizes (draft fix for GDAL #11906) is superseded by #11927 (LIST_ALL_ARRAYS) | `git log master --grep=11906` |
| 2026-10-25 | GDAL has read support for Kerchunk JSON and Parquet references (8682cb47e) and an Icechunk driver (f0a75a209, 2026-06) | `git log master --oneline -i --grep=kerchunk --grep=icechunk` |
| 2026-10-25 | gdalwarp has sum-preserving `sum` resampling since 2022 (#6560) | `git log master --grep=warp_sum_preserving` |
| 2026-10-25 | mdsumner/geos branches carry the R package geos history, not libgeos | `git log -1 refs/fork/master` shows R package version bumps |
| 2026-10-25 | PROJ fork branches emscripten-build, docker-build-updates, gdalbarn have no commits of mine | sweep: `git rev-list --author=Sumner HEAD..refs/fork/<b>` is empty |
| 2026-10-25 | Git cannot show whether an unmerged GitHub PR is open or closed; `refs/pull/N/merge` is not a reliable signal (687 such refs exist) | `git ls-remote https://github.com/OSGeo/gdal 'refs/pull/*/merge' \| wc -l` |
| 2026-10-28 | GDAL 3.13.3: a strided read (step > 1) across multidim VRT sources fails with "arrayStartIdx[0] = N >= 1"; step 1, or a step within one source, works | `python notes/2026-10-28-mdim-vrt-repro.py`, item 1 |
| 2026-10-28 | GDAL 3.13.3: `gdal mdim convert --array 'name=v,view=[::2,...]'` over such a VRT prints ERROR 1, exits 0 and writes fill values | repro script, item 1 (exit code and written values) |
| 2026-10-28 | GDAL 3.13.3: mdim `<BlockSize>` parses comma-separated only; gdalvrt.xsd types it as whitespace-separated integerList | repro script, item 2 |
| 2026-10-28 | GDAL 3.13.3: absent `dataAxisToSRSAxisMapping` on a (t, y, x) array reads as [1, 2]; 2D slices of arrays with a wrong mapping report a 0 entry | repro script, item 3 |
| 2026-10-28 | GDAL 3.13.3: `gdal mdim mosaic` output already carries `<SourceSlab offset count step>` per source | `gdal mdim mosaic a.nc b.nc m.vrt; grep -c SourceSlab m.vrt` |
| 2026-10-28 | GDAL 3.14.0dev (739fcf03bf): `-r mode -wo MODE_TIES=MIN` on all-distinct 2x2 blocks gives different answers for Byte and Int32/Float32 (768 of 1024 pixels in the fixture) | rwarp branch kernels/gdal-parity, `tests/fixtures/kernels/gen.py`, cases `mode_distinct_*` |
| 2026-10-28 | GDAL 3.14.0dev: `MODE_TIES=FIRST` keeps the value that first reaches the winning count; `[[5,3],[3,5]]` warped 2:1 gives 3 | same fixtures, mode cases |
| 2026-10-28 | GDAL 3.14.0dev: `-wo XSCALE=1 -wo YSCALE=1` disables kernel widening when downsampling (point kernel) | rwarp kernels fixtures, `XSCALE=1` cases match rwarp `KernelScaling::Point` within 1e-6 |
| 2026-10-28 | GDAL 3.14.0dev: `average` uses the axis-aligned box between the transformed top-left and bottom-right destination corners; a 45 degree pixel gives 5.0 where the exact mean is 4.5 | rwarp kernels fixtures, average rotation cases |
| 2026-10-28 | GDAL 3.8.4: geolocation `GEOREFERENCING_CONVENTION` defaults to TOP_LEFT_CORNER; with PIXEL_CENTER, cell edges are midpoints between centres in the geolocation coordinates | hypertidy/rwarp `tests/geoloc.rs` (regenerate with `tests/fixtures/make_geoloc_swath.py`) |
| 2026-10-28 | GDAL 3.8.4: gdal.Warp onto a target with geolocation arrays (`DST_METHOD=GEOLOC_ARRAY`) works; nearest output matched by rwarp pixel for pixel | hypertidy/rwarp `tests/geoloc.rs`, `curvilinear_target_*` |
