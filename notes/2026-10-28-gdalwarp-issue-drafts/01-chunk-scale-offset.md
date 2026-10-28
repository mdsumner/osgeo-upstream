**Title:** gdalwarp: kernel scale estimate ignores the chunk's destination offset, so chunked output differs from single-chunk output

### What is the bug?

`GDALWarpKernel::PerformWarp()` estimates `dfXScale`/`dfYScale` by
transforming sample points `iX * nDstXSize / (nPointsX - 1)` (and likewise
for Y), without adding `nDstXOff`/`nDstYOff`. The resampling threads do add
the offsets. So in a multi-chunk warp, every chunk estimates its scale over
the top-left corner of the whole output, and the estimate depends only on
the chunk's size.

Where the scale varies over the output, chunks away from the top-left get
the wrong kernel widening. For example, in the repro, chunks that downsample
are treated as upsampling.

### Steps to reproduce the issue

A 0.1° lon/lat grid (3600 x 1600, 80N to 80S) to EPSG:3857, 400 x 800, cubic,
`-et 0`, run once with a large warp memory limit and once with 1 MB.
Script: (inline it from
notes/2026-10-28-gdalwarp-kernel-repro.py, item 3). With `CPL_DEBUG=ON`:

```
single chunk:  dfYScale = 0.778956   Dst=0,0,400x800
1 MB limit:    dfYScale = 1.244978   Src=0,0,1818x85    Dst=0,0,200x100
               dfYScale = 1.244978   Src=0,79,918x154   Dst=0,100,100x100
               ... every 100-row chunk logs 1.244978
```

The chunk at destination rows 100-199 reads 154 source rows for 100
destination rows (scale about 0.65), but uses 1.24, so cubic isn't widened.
Single-chunk and chunked outputs differ in all 320,000 pixels, by up to
0.113 on data in [0, 1]. It also reproduces on GDAL 3.8.4.

### Versions and provenance

GDAL 3.14.0dev-739fcf03bf, self-built, Ubuntu 24.04. Also 3.8.4 (Ubuntu
package).

### Additional context

Suggested fix: add `nDstXOff`/`nDstYOff` to the sample points, or wrap the
transformer the way the threads do. The `XSCALE`/`YSCALE` docs already say
the estimate can vary between chunks; this issue is about where it is taken,
not that it varies. I can open a PR with a test.

<!-- Declaration (adjust): Found while checking a Rust reimplementation
(hypertidy/rwarp) against gdalwarp. I used an LLM tool (Claude) to help read
the code and write the repro; I checked the numbers and wrote this text. -->
