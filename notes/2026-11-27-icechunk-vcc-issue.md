# GDAL issue draft: Icechunk driver does not resolve `vcc://` locations

From [2026-11-27-icechunk-vcc.md](2026-11-27-icechunk-vcc.md). **A
starting point, not text to paste.** GDAL's LLM tool policy (RFC 111) and
STRATEGY.md mean the issue text is rewritten in my own words, kept short,
with tool use declared.

Record for the declaration:

- LLM-written (Claude, 2026-11-27): all text below, the repro script and the
  findings note.
- Found in the same session, from my request to check GDAL support before
  publishing relocatable Bluelink stores (raad.virtualize #117).

Before filing: re-run the repro on the then-current master. Check how the
Icechunk spec serializes the container name. Consider filing it together
with C, E and F, as one driver bug-fix PR.

---

**Title:** Icechunk: virtual chunk locations relative to a named container (`vcc://<name>/...`) are not resolved

### What is the bug?

Icechunk virtual refs can be written relative to a named virtual chunk
container, `vcc://<name>/<path>`. The repository config gives that
container's `url_prefix`. icechunk-python resolves them. The Icechunk
driver treats them as local paths. By default the read is refused
("Access to non-network chunk location ... disabled by default"); with
`ICECHUNK_ALLOW_LOCAL_CHUNK_LOCATION=YES` it fails with "Cannot open
vcc://...".

`vsiicechunk.cpp` maps locations through a fixed scheme table (`s3://`,
`https://`, ...), and `ProcessConfig()` reads `virtual_chunk_containers`
only for S3 options, so the name is never looked up.

### Steps to reproduce the issue

A repository with one 2 x 4 uint8 array (no compression). Row 0 has an
absolute `http://127.0.0.1:PORT/chunk.bin` ref; row 1 has
`vcc://data/chunk.bin` with a container named `data` at the same
`http://127.0.0.1:PORT/` prefix. Script (inline or attach):
notes/2026-11-27-icechunk-vcc-repro.py (`make` with icechunk-python >= 2.3,
`read` with GDAL master).

```
icechunk-python: row 0 [0, 1, 2, 3], row 1 [4, 5, 6, 7]
GDAL row 0: [0, 1, 2, 3]
GDAL row 1: ERROR Access to non-network chunk location 'vcc://data/chunk.bin' disabled by default. ...
GDAL row 1 (ICECHUNK_ALLOW_LOCAL_CHUNK_LOCATION=YES): ERROR Cannot open vcc://data/chunk.bin
```

### Versions and provenance

GDAL 3.14.0dev-9c765f0bdd (osgeo/gdal ubuntu-small-latest image); code
unchanged on master af949144. icechunk-python 2.4.0 wrote the repository.

### Additional context

Suggested fix: keep a name -> `url_prefix` map from the config's
containers, and resolve `vcc://<name>/` through it before the scheme
table. I can open a PR with a test.

<!-- Declaration (adjust): Found while publishing relocatable Icechunk
stores. I used an LLM tool (Claude) to trace the code, write the repro and
draft this text; I checked the results and rewrote it. -->
