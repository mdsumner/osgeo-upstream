# GDAL Icechunk driver: `vcc://` chunk locations (gap G), 2026-11-27

Found while publishing relocatable virtual stores from raad.virtualize
(byterefs/spec decision 0014, named remap roots). An Icechunk virtual chunk
can be stored relative to a named virtual chunk container,
`vcc://<container name>/<rest>`. The reader resolves it with the container
of that name in the repository config. icechunk-python does this (2.1.0 and
2.4.0 here), and so does icechunk-js. GDAL's Icechunk driver does not.

Follows [2026-11-16-icechunk-driver-gaps.md](2026-11-16-icechunk-driver-gaps.md)
(gaps A to F). Issue draft:
[2026-11-27-icechunk-vcc-issue.md](2026-11-27-icechunk-vcc-issue.md).

## Repro

[2026-11-27-icechunk-vcc-repro.py](2026-11-27-icechunk-vcc-repro.py).

- One uint8 array, 2 x 4, one chunk per row, no compression, so no codec is
  involved (unlike the Bluelink stores, which also need `numcodecs.shuffle`,
  gap D).
- Both chunks reference the same 8-byte file, served over local HTTP with
  range support; `file://` locations fail on their own (gap C).
  - Row 0: absolute, `http://127.0.0.1:PORT/chunk.bin`.
  - Row 1: `vcc://data/chunk.bin`, through a container named `data` with
    url_prefix `http://127.0.0.1:PORT/`.
- `make` needs icechunk-python >= 2.3 (named containers); `read` needs GDAL
  master (the driver is not in a release). They can run in different
  environments that share the directory.

Output, the same on `3.14.0dev-9c765f0bdd` (osgeo/gdal ubuntu-small-latest,
2026-11-07) and the local build `3.14.0dev-fedfd3ec89`:

```
icechunk-python 2.1.0: row 0 [0, 1, 2, 3], row 1 [4, 5, 6, 7]
GDAL, ICECHUNK_ALLOW_LOCAL_CHUNK_LOCATION=NO, row 0: [0, 1, 2, 3] (ok)
GDAL, ICECHUNK_ALLOW_LOCAL_CHUNK_LOCATION=NO, row 1: ERROR Access to non-network chunk location 'vcc://data/chunk.bin' disabled by default. Set the ICECHUNK_ALLOW_LOCAL_CHUNK_LOCATION configuration option to YES to enable it.
GDAL, ICECHUNK_ALLOW_LOCAL_CHUNK_LOCATION=YES, row 0: [0, 1, 2, 3] (ok)
GDAL, ICECHUNK_ALLOW_LOCAL_CHUNK_LOCATION=YES, row 1: ERROR Cannot open vcc://data/chunk.bin
```

The real case: a relocatable render of Bluelink BRAN `eta_t` (container
`g-data-gb6`, later named `bran2023`, at
`https://thredds.nci.org.au/thredds/fileServer/gb6/`) gives the same two
errors, with `vcc://g-data-gb6/BRAN/BRAN2020/daily/ocean_eta_t_1993_01.nc`.

## Code (master `af949144`, 2026-11-27)

- `frmts/icechunk/vsiicechunk.cpp`, around lines 325 to 365: a chunk
  location becomes a GDAL file name through a fixed table of schemes
  (`s3://`, `gs://`, `gcs://`, `az://`, `azure://`, `http://`, `https://`).
  Anything else is local: refused, or with
  `ICECHUNK_ALLOW_LOCAL_CHUNK_LOCATION=YES` passed to the file system as it
  stands.
- `frmts/icechunk/icechunkrepo.cpp`, `ProcessConfig()`: reads
  `virtual_chunk_containers` only to set S3 options (region, anonymous) per
  `url_prefix`. The container name is not used.
- `git grep vcc:// -- frmts/icechunk`: nothing.

## Fix sketch

- In `ProcessConfig()`, keep a map from container name to `url_prefix` for
  the containers that have a name. Check the name's field in the Icechunk
  spec; icechunk-python exposes it as `VirtualChunkContainer.name`.
- When resolving a location: if it starts with `vcc://`, take the name up to
  the next `/`, look it up, and replace `vcc://<name>/` with that
  `url_prefix`. Then apply the scheme table as now. An unknown name is an
  error naming the container.
- A test: the repro's repository as an autotest fixture (one absolute and
  one `vcc://` chunk, the file served by the test HTTP server), next to the
  gap C test.
- Size: small. It fits the driver bug-fix PR with C, E and F, before 3.14
  branches.

## Why it matters

A relocatable store is published once and read anywhere. For example, a
THREDDS-backed store can be read in place on NCI's `/g/data` by binding the
same container name to a local prefix, with no re-render. Without `vcc://`
in GDAL, such a store is readable from icechunk-python and icechunk-js but
not from GDAL, so raad.virtualize publishes absolute refs (decided
2026-11-27).
