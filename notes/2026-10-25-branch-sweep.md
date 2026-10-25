# Branch sweep, 2026-10-25

Own branches in mdsumner/gdal, mdsumner/PROJ and mdsumner/geos compared
with upstream default branches. Re-run with `scripts/sweep.sh`; raw output is
in `data/`.

Method: treeless clones of upstream and the forks; every upstream
`refs/pull/*/head` fetched. A branch counts as merged when its PR number
appears on master as a squash subject `(#N)` or a `Merge pull request #N`,
or when its tip is an ancestor of master. The PR for a branch is the upstream
PR whose head commit equals the branch tip. Git cannot tell whether an
unmerged PR is still open or was closed; those are marked "unmerged".

## GDAL (99 branches: 77 with my work, 22 upstream history)

### Merged upstream (50 branches): safe to delete

vrt:// options: vrt_connection_asrs (#6893), vrt_connection_aullr (#6900),
vrtcon-ovr (#7287), vrtcon-expand (#7290), vrtcon-scl-offset (#7300),
vrtcon-option-ot (#7309), vrtcon-gcp (#7316), vrtcon-if (#7333),
vrtcon-scale-exponent2 (#7521), vrtcon-outsize (#7548), vrtcon_projwin
(#8320), vrtcon_projwin_srs (#8323), vrtcon_various (#8330),
vrtcon_open_options (#8339), vrtcon-scale-unscale2 (#8366),
vrtcon_a_coord_epoch (#8375), vrtcon_nogcp (#8397), vrtcon_eco_epo (#8405),
vrtcon-sds-choose (#8906), vrtcon-transpose (#12366), vrtcon_block (#13786).

Multidim and Zarr: mdim-transpose-valid-axis (#12357),
zarr-v3-numpy-datetime64-extension (#13913),
swig-add-mdarray-guessgeotransform (#14569, rebased in as 7e0e87ad6),
swig-add-mdarray-isregularlyspaced (#14574), patch-14 (#14705),
patch-16 (#14806), fix_14881_mdim_cfunit (#14882).

Drivers, warp, utilities: csv_pipe-sep (#6901), netcdf_6195_assume_longlat
(#6910), gdalwarp-auto-overview-lonwrap (#7078), review-gdal_alg-doc
(#7201), NSIDCbin-2 (#7263), mem-spatialreference (#7272), stacit_s3
(#8168), translate-dmo (#8935), geoloc-normalize-longitude180-fix6582
(#12651).

Docs: patch-1 (#7665), patch-2 (#7718), patch-3 (#7837), gpkg.rst-patch
(#7838), patch-5 (#8284), patch-6 (#8744), patch-7 (#8919), patch-8
(#10388), gti-tiny-typo (#10748), patch-9 (#11184), patch-10 (#11647),
patch-11 (#11668), patch-13 (#12319).

### Superseded or scratch (15 branches): safe to delete

| Branch | Why |
|---|---|
| NSIDCbin | first PR #6183, replaced by #7263 |
| mem-spatialref, deleteme | #7266 replaced by #7272 |
| investigate-ovr, vrtconnection-ovr | #7282 replaced by #7287 |
| gdal_translate-dmo, dmo-backup | #8458 replaced by #8935 |
| vrt_connection, vrt_connection_subds | early vrt:// work; subdataset choice landed as sd_name/sd (#8906) |
| patch-4 | same fix landed as #8744 |
| testme, try-autotest-idiom-mds | test scratch (#8343 closed) |
| zarr_list_array_sizes | draft fix for #11906; fixed upstream by #11927 (LIST_ALL_ARRAYS) |
| patch-12 | CI numpy>=2 (#12308), closed |
| vrtcon-no-value-options | older copy of vrtcon-no-value-options2 |

### Live or revivable (12 branches)

| Branch | Last commit | Upstream | State | Tracker |
|---|---|---|---|---|
| feature/mdim-get-refs | 2026-05-28 | PR #14677, unmerged | review changes partly applied | #36 |
| mdim-helpers | 2026-06-11 | none | helpers split out of get-refs for gcore | #36 |
| stage1-mvp | 2026-05-28 | none | get-refs plus vector layer output, 10 own commits | #36 |
| fast-path-h5-chunk-refs-iter | 2026-05-25 | none | HDF5 chunk refs fast path on top of get-refs | #36 |
| zarr-jpeg | 2026-04-14 | none | draft JPEG codec for Zarr, 107 lines | new |
| zarr-tiff-predictor-DRAFT | 2026-02-26 | none | draft TIFF predictor codec, 140 lines | new |
| warp-tap-with-ts | 2023-01-24 | none | gdalwarp -tap with -ts, 46 lines | #7 |
| netcdf-vector-timeseries | 2024-04-04 | none | wip, 53 lines | new |
| vrtcon-no-value-options2 | 2023-06-30 | none | vrt:// flags without =value | #1 |
| vrtcon-key-value-required | 2023-09-07 | none | error on malformed vrt:// options | #1 |
| patch-15 | 2026-06-03 | none | typos in gdal_mdim_mosaic doc | new |
| mdsumner-patch-1 | 2023-08-13 | none | gdal_footprint.rst one-liner | new |

Check before reviving each: whether master has changed the same code since
the branch point (the vrt:// and doc ones are old).

### Not mine (22 branches)

release/1.4 to release/3.4, vendor/1.4-esri, backport-5201-to-release/3.4,
lzw_improvements (Even Rouault's experiment), master (fork default, 2026-01-27,
behind upstream).

## PROJ

- Merged: docs typo #3275 (backported #3276).
- Live: patch-1 has one more own commit, "param arg form" (2022-08-02), not
  upstream. Small; check if still relevant.
- emscripten-build, docker-build-updates and gdalbarn carry no commits of mine
  (emscripten-build tip is Howard Butler's; the other two are not ahead of
  upstream). They are upstream history, not my work.
- Everything else mirrors upstream release branches.

## GEOS

- Merged in libgeos/geos: #624 (GeosOp explode description), #961 (home page
  View Source link).
- mdsumner/geos branches (master, development, avoid-zero-crs-terra) carry the
  history of the R package geos (Dewey Dunnington), not libgeos.
  avoid-zero-crs-terra (5 own commits, 2026-08-08) is R package work and
  belongs outside this tracker.
