# Zarr codec gaps, 2026-11-03

Why GDAL cannot read the virtual stores raad.virtualize writes for GHRSST MUR
(COGs, ZSTD + PREDICTOR=2) and BRAN (netCDF4, shuffle + zlib) through
`/vsiicechunk/` (Zarr V3) or kerchunk refs (Zarr V2), and what each fix
involves. Code locations are GDAL master `5906ed4` (2026-11-03), read, not
built. The repro has not been run against GDAL yet.

Repro: [2026-11-03-zarr-codec-repro.py](2026-11-03-zarr-codec-repro.py)
writes six tiny stores (same 4 x 6 Int16 array, 2 x 3 chunks) with
zarr-python and imagecodecs, then reads each with GDAL and compares:

```
python 2026-11-03-zarr-codec-repro.py make  fx   # zarr, numcodecs, imagecodecs
python 2026-11-03-zarr-codec-repro.py check fx   # osgeo.gdal
```

The codec metadata each fixture carries (zarr 3.4.2, numcodecs 0.17.1,
imagecodecs 2026.10.10):

```
v3_numcodecs_shuffle_zlib  bytes, numcodecs.shuffle {elementsize: 2}, numcodecs.zlib {level: 1}
v3_numcodecs_zlib          bytes, numcodecs.zlib {level: 1}
v3_numcodecs_zstd          bytes, numcodecs.zstd {level: 1}
v3_imagecodecs_delta_zstd  imagecodecs_delta {axis: -1, dist: 1}, bytes, numcodecs.zstd {level: 1}
v2_shuffle_zlib            filters [shuffle {elementsize: 2}], compressor zlib
v2_imagecodecs_delta_zstd  filters [imagecodecs_delta {axis: -1, dist: 1, shape: [2, 3], dtype: <i2}], compressor zstd
```

Expected from reading master: `v2_shuffle_zlib` OK, the other five fail.

## What master has

- Zarr V3 codec dispatch, `frmts/zarr/zarr_v3_codec_sequence.cpp` around
  line 89: `gzip`, `blosc`, `zstd`, `bytes` (and old `endian`), `transpose`,
  `crc32c`, `vlen-utf8`, `sharding_indexed`, `pcodec`. Anything else is
  "Unsupported codec". No `numcodecs.*` name is recognised.
- Zarr V2 filters, `frmts/zarr/zarr_v2_array.cpp` around line 686 (decode)
  and 2042 (open-time check): `shuffle`, `quantize`, `fixedscaleoffset`,
  `bitround` special-cased, otherwise `CPLGetDecompressor(id)`.
- `port/cpl_compressor.cpp` has a `delta` filter, but it is numcodecs
  `delta`: one run over the flattened chunk. TIFF PREDICTOR=2 restarts on
  every row. On the fixture's first chunk the stored values are
  `[[-50, 7, 7], [-8, 7, 7]]`: a cumulative sum along each row gives the
  data back, a flat cumulative sum does not.
- The shuffle decoder already exists (`zarr_filters.cpp`,
  `ZarrGetShuffleDecompressor()`, option `ELEMENTSIZE`), and so does CPL
  `zlib`.

## The gap is wider than shuffle

The BRAN Icechunk store fails first at `numcodecs.shuffle`, but its next
codec is `numcodecs.zlib`, which master does not know either. The GHRSST
Icechunk store needs `imagecodecs_delta` and then `numcodecs.zstd`. So
"map numcodecs.shuffle" alone would only move the error one codec along.
zarr-python 3 writes `numcodecs.<id>` for every codec it takes from
numcodecs (numcodecs.zarr3), so these names are common in the wild.

## Fixes, smallest first

| # | What | Size | Where | Notes |
|---|---|---|---|---|
| C1 | V3 `numcodecs.zstd` as another name for `zstd` | a few lines | dispatch in zarr_v3_codec_sequence.cpp | Same bitstream and config keys (`level`, `checksum`). numcodecs allows negative levels; GDAL's zstd codec rejects level < 0. |
| C2 | V3 `numcodecs.zlib` | one small class, like `ZarrV3CodecGZip` over CPL `zlib` | new zarr_v3_codec_zlib.cpp or shared with gzip | Not the same as `gzip` (zlib header, not gzip header). |
| C3 | V3 `numcodecs.shuffle` | one small bytes-to-bytes class over the existing shuffle decoder | zarr_v3_codec_*.cpp | Config `elementsize` maps to `ELEMENTSIZE`. |
| C4 | V3 `imagecodecs_delta` | array-to-array class, like `ZarrV3CodecTranspose` | zarr_v3_codec_*.cpp | Gets the chunk shape from the input array metadata, so no config shape is needed. Decode only is enough to start. |
| C5 | V2 `imagecodecs_delta` filter | revive fork branch `zarr-tiff-predictor-DRAFT` | zarr_filters.cpp, zarr_v2_array.cpp (both places above) | See below. |

C1 to C3 are one concern (numcodecs.* names in Zarr V3) and could be one
issue and one PR. C4 and C5 are the TIFF predictor, a second issue.

### Notes for C4 and C5 (TIFF predictor)

- The draft branch registers id `tiff_predictor` and takes `TILEWIDTH`,
  `NBITS`, `PREDICTOR` options. Stores in the wild say `imagecodecs_delta`
  with `axis`, `dist` (and in V2 `shape`, `dtype`), so the id and options
  would change: row length from `shape[-1]` in the filter config, falling
  back to the array's chunk size along the last dimension.
- In V2, imagecodecs' own decoder needs `shape` in the config: with
  `shape: null` it decodes along the flattened chunk, and zarr-python then
  reads the fixture wrong too. raad.virtualize (R/mdimrefs.R) and tifffile
  write `shape` and `dtype`, so GDAL can rely on them, or on the chunk size.
- Scope to start: integer types, `axis: -1`, `dist: 1`, unsigned wrap
  arithmetic (as libtiff does), which the draft already does. Float
  predictor (PREDICTOR=3, `imagecodecs_floatpred`) is a separate later item
  and nothing in the current stores needs it.
- The draft adds as native integers on raw bytes, which is right on little
  endian hosts for `<i2`; the V3 array-to-array form runs after `bytes`, so
  it sees native order and avoids the question.
- `imagecodecs_delta` is not a codec in the Zarr V3 spec or zarr-extensions
  as far as checked; ask upstream whether GDAL accepts that name, since
  VirtualiZarr / virtual_tiff / tifffile output uses it.

## Suggested order

1. Run the repro against GDAL master on the VM; record the six lines in
   LEDGER.md.
2. Search GDAL issues for `numcodecs.` and `imagecodecs_delta` first.
3. Issue: Zarr V3 `numcodecs.*` names (C1 to C3), with the three V3 fixture
   lines and the BRAN `/vsiicechunk/` error. Then one PR.
4. Issue: TIFF predictor (`imagecodecs_delta`) for V2 and V3, asking about
   the name. PR after a response (C5 first if the draft is the quicker
   route, C4 next).
