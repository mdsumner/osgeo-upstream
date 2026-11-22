# Plan: Zarr V3 `numcodecs.*` codecs (C1-C3), 2026-11-22

C1 `numcodecs.zstd`, C2 `numcodecs.zlib`, C3 `numcodecs.shuffle`, from
[2026-11-03-zarr-codec-gaps.md](2026-11-03-zarr-codec-gaps.md). Upstream:
GDAL issue 14917 (mine, open, quiet since 2026-07-06). Unblocks BRAN, OISST,
ACCESS-ESM and most netCDF-4 derived stores through `/vsiicechunk/`, and the
second codec of the GHRSST Icechunk store (GHRSST still needs C4,
`imagecodecs_delta`).

Decided 2026-11-22: one fix at a time, starting with the one 14917 asks for
(zlib + shuffle, which every affected store uses together). The first PR
draws the review of the approach; later ones follow whatever it settles.
Approach A (explicit codec classes, as `gzip`, `zstd`, `numcodecs.pcodec`).
B (one generic `numcodecs.<id>` bridge onto CPL compressors, as V2 filters
do) is off precedent: mention it in the PR as the alternative considered,
and offer it if maintainers prefer it.

The code exists: `~/gdal-wp4` (a worktree of `~/gdal`), branch
`icechunk-wp4`, commit `7f71b6c1e2` "Zarr V3: add numcodecs.zlib and
numcodecs.shuffle codecs" (330 lines, 6 files; shuffle overrides `Decode()`
to pass `ELEMENTSIZE`; tests write stores at runtime for int16, float32,
uint8, float64, plus an invalid elementsize). Applies cleanly to master
`900c99f512` (2026-11-22). The commit after it (`30732f5482`, Icechunk
snapshot / file:// / allow-list) is a separate track.

## Steps

**0. Baseline (no PR).** Fresh branch from current master, build. Run
`notes/2026-11-03-zarr-codec-repro.py` (make, check), the OISST zip
(zarr-icechunk-assure `fixtures/oisst-sample/repo-https-2026-07-07.zip`) and
the BRAN Icechunk store. Record the failures in LEDGER.md.
Gate: each failure is the expected one; nobody else has started (14917, open
PRs).
**Done 2026-11-22** on `3.14.0dev-fedfd3ec89` (LEDGER.md): fixtures, OISST
zip and BRAN all fail as expected. BRAN over HTTP:
`/vsiicechunk/{/vsicurl/https://data.source.coop/ausantarctic/ausantarctic-scratch/bluelink/bluelink-daily-temp/icechunk}`.
Both stores also show GDAL 14833 (failing arrays left out of the listing).
Before PR 1: add an OSGeo remote to `~/gdal` (origin is the fork) and branch
from upstream master.

**PR 1: `numcodecs.zlib` + `numcodecs.shuffle` (fixes 14917).** Code from
`7f71b6c1e2`; tests replaced by committed stores, pcodec style. Materials:
[2026-11-22-numcodecs-pr1/](2026-11-22-numcodecs-pr1/README.md).

```
cd ~/gdal
# 1. branch from upstream master
git remote add upstream https://github.com/OSGeo/gdal   # origin is the fork
git fetch upstream
git switch -c zarr-v3-numcodecs upstream/master

# 2. take the WP4 commit without committing, drop its runtime-built tests
git cherry-pick -n 7f71b6c1e2
git restore --source=upstream/master --staged --worktree autotest/gdrivers/zarr_driver.py

# 3. fixtures and the pcodec-style tests
cp -r ~/Git/osgeo-upstream/notes/2026-11-22-numcodecs-pr1/v3/*.zarr autotest/gdrivers/data/zarr/v3/
cat ~/Git/osgeo-upstream/notes/2026-11-22-numcodecs-pr1/zarr_driver_numcodecs_tests.py >> autotest/gdrivers/zarr_driver.py
#    (then delete the 3-line "Append to ..." comment at the top of what was appended)

# 4. build and test. build/autotest is a copy of autotest (not a symlink), so
#    check the new tests and stores reached it; if not, `cmake -S . -B build`
#    refreshes the copy. Otherwise the tests would regenerate the stores in
#    the build tree and never read the committed ones.
cmake --build build -j
grep -c numcodecs build/autotest/gdrivers/zarr_driver.py      # expect > 0
ls build/autotest/gdrivers/data/zarr/v3 | grep -c numcodecs   # expect 6
cd build && pytest autotest/gdrivers/zarr_driver.py -k numcodecs && \
  pytest autotest/gdrivers/zarr_driver.py autotest/gdrivers/icechunk_driver.py; cd ..
pre-commit run --files $(git diff --name-only --cached) autotest/gdrivers/zarr_driver.py
```

5. Real reads with the new build: repro `check fx` (`v3_numcodecs_shuffle_zlib`
   and `v3_numcodecs_zlib` OK; `v3_numcodecs_zstd` still fails, expected);
   OISST probe lon 199.875, lat -9.875, day 1 = 2782 packed (27.82 C); BRAN
   `temp` listed and readable.
6. Read the whole diff: `git add -A autotest/gdrivers && git diff --cached`.
7. Commit (message from `7f71b6c1e2`, with "(fixes #14917)" in the title,
   test sentence updated), push to the fork, CI green, open the PR. In the
   description: still failing on master before this; the `elementsize` point
   (the base `Decode()` passes no options, so shuffle would fall back to 4);
   alternative considered: B.

**Next, after PR 1 settles:** `numcodecs.zstd` (C1). Route the name to the
existing zstd codec, keep the name in the metadata, accept negative levels
on decode (the existing check rejects `level < 0`). Shape it the way PR 1's
review lands.

## Left after this

- C4-C6 TIFF predictors (GHRSST): the next track.
- GDAL 14833: an array with an unsupported codec is silently left out of
  `mdim info`. Not addressed by C1-C3.
