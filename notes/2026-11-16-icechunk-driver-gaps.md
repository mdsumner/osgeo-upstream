# GDAL Icechunk driver: gaps and limits, 2026-11-16

From the icechunkr work (private repo mdsumner/icechunk-r, WP4:
`notes/gdal-wp4.md`, script `bench/gdal_validate.py`, results
`bench/gdal_validation_{installed,patched}.csv`). Tested against GDAL
3.14.0dev `fa1fc3c77e` (2026-11-03), built and run.

**Timing.** The Icechunk driver (`frmts/icechunk`, f0a75a209, 2026-06) is on
master only: `release/3.13` has no `frmts/icechunk`. 3.14 has not branched
(latest release v3.13.3, 2026-08-18). No commits to `frmts/icechunk` or
`frmts/zarr` since `fa1fc3c77e` (checked 2026-11-16 via the GitHub API). So
everything below ships in the driver's first release unless fixed before the
3.14 branch.

**Policy.** Reference implementations for A to E exist (local only, see
below), written with tooling during WP4. Under this tracker's rules (GDAL
RFC 111) they are reference material: upstream code, tests, commit messages
and issue or PR text are mine to write.

## Validation summary

38 cases: fixtures written by icechunk-python 1.1 (format v1) and 2.x
(format v2, and spec-1 repos written by 2.x), native, inline and virtual
chunks, plus source.coop repos compared with icechunk-python + zarr-python
on the same slab.

| Build | PASS | REFUSED (as intended) | FAIL |
|---|---|---|---|
| 3.14dev `fa1fc3c77e` | 25 | 2 | 11 |
| with patches A to E | 34 | 4 | 0 |

Already right on 3.14dev: every native and inline case in both formats,
strings, sharding, nested groups, 4096^2 arrays, branch and tag selection
with correct history, zstd coordinate arrays over the network.

## Gaps

| # | Gap | Kind | Fix (as implemented locally) | Size |
|---|---|---|---|---|
| A | No snapshot selection: `ICECHUNK:<repo>?snapshot=<id>` is "Invalid Icechunk connection string" | feature | `?snapshot=<id>` in `ICECHUNK:` names and `/vsiicechunk/`; any snapshot under `snapshots/`; id validated as 20 Crockford base32 chars (so it cannot carry path components); at most one of branch/tag/snapshot | small |
| B | No allow-list for virtual chunk locations: any network location in a manifest is fetched. Icechunk itself requires each virtual chunk container to be authorised | security / design | config option `ICECHUNK_VIRTUAL_CHUNK_ALLOWED_PREFIXES` (comma list of URL prefixes); unset = today's behaviour; a listed `file://` prefix also allows those local locations | small; **default is a question for Even** |
| C | With `ICECHUNK_ALLOW_LOCAL_CHUNK_LOCATION=YES`, `file://` chunk locations fail: "Cannot open file:///..." (the URL goes to `VSIFOpenL` verbatim) | bug | strip `file://` before opening | one line + test |
| D | Zarr V3 has no `numcodecs.zlib` / `numcodecs.shuffle`: OISST, ACCESS-ESM, BRAN, GEBCO-style virtual COGs and most netCDF-4 derived virtual arrays are unreadable | missing codec | two thin V3 codecs over the V2 zlib compressor and shuffle filter | small; **already tracked, see below** |
| E | `/vsiicechunk/{/path/to/repo?branch=x}` (the syntax in the driver's own comment and error message) ignores the query unless `ICECHUNK:` is inside the braces | bug | parse the query either way | small |

Tests added with the reference patches: `test_icechunk_open_snapshot` (A,
E), `test_icechunk_virtual_chunk_allowed_prefixes` (B),
`test_icechunk_virtual_ref_local` (C),
`test_zarr_v3_read_numcodecs_shuffle_zlib` (int16, float32, uint8, float64)
and `test_zarr_v3_numcodecs_shuffle_invalid_elementsize` (D). With them,
`autotest/gdrivers/icechunk_driver.py` + `zarr_driver.py`: 880 passed, 16
skipped; pre-commit hooks pass. Docs touched: `icechunk.rst` (snapshot,
config options), `zarr.rst` (numcodecs codecs).

### D overlaps existing work

- This is C2 + C3 of [2026-11-03-zarr-codec-gaps.md](2026-11-03-zarr-codec-gaps.md),
  tracker #42, upstream GDAL issue 14917 (mine, open, one comment, untouched
  since 2026-07-06). The reference patch does not do C1 (`numcodecs.zstd`).
- **Finding worth putting in 14917:** shuffle must pass `elementsize` to the
  decoder; the generic compressor `Decode()` does not, and falls back to the
  filter default of 4. A first version decoded float32 right and int16 wrong
  (caught by comparing OISST with icechunk-python). Test more than one
  element size.
- **Public repro for 14917:** zarr-icechunk-assure's
  `fixtures/oisst-sample/repo-https-2026-07-07.zip` (35 KB, also shipped in
  tabularberg as `inst/extdata/oisst-sample/`): `gdal mdim info
  /vsiicechunk/{/vsizip/repo-https-2026-07-07.zip}/` reads metadata and
  coordinates; the int16 shuffle+zlib data arrays fail. Probe: lon 199.875,
  lat -9.875, day 1 = 2782 packed (27.82 C).
- Related: GDAL issue 14833 (jhamman, Earthmover, 2026-06-19, open): an array
  with an unsupported codec is dropped from `gdal mdim info` instead of being
  listed as unreadable. D removes the most common trigger but not the silent
  omission itself.

## Limits not patched

- **Plain HTTP repo URL.** `/vsicurl/https://host/.../icechunk` 404s on the
  directory; `/vsicurl/https://host/.../icechunk/repo` (the `repo` file) works.
  The driver could try `<url>/repo` when the directory stat fails. Issue or
  question first.
- **Allow-list default (B).** Allow-all when unset keeps today's behaviour;
  requiring authorisation, as Icechunk does, would be safer but breaks
  existing use. Ask before coding.
- **gdalraster, not GDAL:** gdalraster crashes R (C stack overflow, then an
  Rcpp longjmp) on the error storm from gap C. Belongs on the gdalraster
  tracker.
- **By design:** read-only; no commits, branches or virtual-ref authoring.
  The driver reads manifests itself (`icechunkmanifest.cpp`), so exposing
  chunk refs connects to `gdal mdim get-refs` (#36).

## Where the reference patches are

- Worktree `~/gdal-wp4`, local branch `icechunk-wp4` (from `fa1fc3c77e`, not
  pushed), lean build `~/gdal-wp4/build`:
  - `7f71b6c1e2` Zarr V3: add numcodecs.zlib and numcodecs.shuffle codecs (D)
  - `30732f5482` Icechunk: open a snapshot by id, local file:// chunks,
    virtual chunk allow-list (A, B, C, E)
- Patch files: icechunk-r `notes/gdal-patches/0001-*.patch`, `0002-*.patch`.

## Suggested order

1. D: comment on 14917 (fixtures, the `elementsize` finding), then one PR
   for C1 to C3. Already P1 in PRIORITIES.md.
2. C and E: one small bug-fix PR to the driver.
3. A: snapshot selection (feature PR; small).
4. B: open an issue on the default first.
5. HTTP `repo` fallback: issue or question.

All before 3.14 branches, if possible.

Rows for PLANS.md (not added: PLANS.md has uncommitted edits from elsewhere):

| Item | Where | Status | P | Next step |
|---|---|---|---|---|
| Icechunk driver: `file://` chunk locations and `/vsiicechunk/{...?branch=}` query (C, E) | this note; ref. patch `30732f5482` | ready | P1 | One bug-fix PR, before 3.14 branches |
| Icechunk driver: open by snapshot id (A) | this note | ready | P2 | Feature PR |
| Icechunk driver: virtual chunk allow-list and its default (B) | this note | idea | P2 | Issue asking about the default |
| Icechunk over plain HTTP needs the `repo` file URL | this note | idea | P3 | Issue or question |
