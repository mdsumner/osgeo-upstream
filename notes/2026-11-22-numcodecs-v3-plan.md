# Plan: Zarr V3 `numcodecs.*` codecs (C1-C3), 2026-11-22

C1 `numcodecs.zstd`, C2 `numcodecs.zlib`, C3 `numcodecs.shuffle`, from
[2026-11-03-zarr-codec-gaps.md](2026-11-03-zarr-codec-gaps.md). Upstream:
GDAL issue 14917 (mine, open, quiet since 2026-07-06). Unblocks BRAN, OISST,
ACCESS-ESM and most netCDF-4 derived stores through `/vsiicechunk/`, and the
second codec of the GHRSST Icechunk store (GHRSST still needs C4,
`imagecodecs_delta`).

Reference implementation of C2 and C3: `~/gdal-wp4`, branch `icechunk-wp4`,
`7f71b6c1e2` (330 lines over 6 files, mostly a new
`zarr_v3_codec_numcodecs.cpp`; based on `fa1fc3c77e`). Use it as reference:
split it per PR and redo each piece on current master. It doesn't do C1.

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

**1. Comment on 14917 (no code).** Fixtures, the real-store errors, the
`elementsize` finding (the generic `Decode()` doesn't pass it, falls back to
4: float32 right, int16 wrong). Propose three small PRs. Ask: decode only or
encode too? Separate classes, or a `numcodecs.<x>` alias onto existing codecs
where the bitstream is the same?
Gate: a reply, or a wait I set.

**PR 1: `numcodecs.zlib` (C2).** One class on the existing compressor base
(like `gzip`), registration line, tiny committed fixture written by
zarr-python (generator noted in the test), one read test, a `zarr.rst` line.
Its real job is to settle conventions (file layout, fixture style, test
style, doc wording). Expect changes; carry them into PR 2 and PR 3 before
opening those.

**PR 2: `numcodecs.shuffle` (C3).** Bytes-to-bytes over the existing shuffle
decoder (`ZarrGetShuffleDecompressor()`), `elementsize` passed explicitly.
Tests for element sizes 1, 2, 4, 8 and an invalid one; `zarr.rst` line. After
PR 1 merges. Closes 14917.
Extra gate: OISST and BRAN read through `/vsiicechunk/` and match
icechunk-python. OISST probe: lon 199.875, lat -9.875, day 1 = 2782 packed
(27.82 C).

**PR 3: `numcodecs.zstd` (C1).** Route the name to the existing zstd codec.
Negative levels: accept on decode (level is irrelevant there), refuse or
clamp on encode. One test, doc line. If 14917's reply prefers an alias table,
this may go first or fold into PR 1.

## Gate before opening each PR

- [ ] read the full diff, line by line
- [ ] build
- [ ] `autotest/gdrivers/zarr_driver.py` and `icechunk_driver.py` pass
- [ ] pre-commit hooks pass
- [ ] fixture values match zarr-python
- [ ] CI green on the fork
- [ ] one independent local review pass (e.g. `/code-review`)
- [ ] the previous PR has merged

## Left after this

- C4-C6 TIFF predictors (GHRSST): the next track.
- GDAL 14833: an array with an unsupported codec is silently left out of
  `mdim info`. Not addressed by C1-C3.
