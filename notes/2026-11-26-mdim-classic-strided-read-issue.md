# GDAL issue draft: index and strided views of AsMDArray()

From [2026-11-26-mdim-classic-strided-read.md](2026-11-26-mdim-classic-strided-read.md).
**A starting point, not text to paste.** As with
[2026-10-28-gdalwarp-issue-drafts/](2026-10-28-gdalwarp-issue-drafts/README.md):
GDAL's LLM tool policy (RFC 111) and STRATEGY.md mean the issue text is
rewritten in my own words, kept short, with tool use declared.

Record for the declaration:

- LLM-written (Claude, 2026-11-26): all text below, the snippet, the repro
  script and the findings note.
- Found in the same session: index views (item 1), the `Dataset.AsMDArray()`
  and `GetResampled()` coverage, and the version checks.
- The original failure is from my gdalraster run (BedMachine `[::14,::14]`).
  The first note on it (the window line, the decimation and overview caveats)
  was pasted into the session. Record who wrote that note before declaring.

Before filing: re-run the snippet on the then-current master.

---

**Title:** `AsMDArray()`: index and strided views read a `count * step` window (buffer not written, out-of-range errors, decimated values)

### What is the bug?

Arrays from `GDALRasterBand::AsMDArray()`, `GDALDataset::AsMDArray()` and
`GetResampled()` read a RasterIO window of `count * |step|` per axis
(`GDALMDRasterIOFromBand()` in gcore/gdalrasterband.cpp,
`GDALMDArrayFromDataset::ReadWrite()` in gcore/gdaldataset.cpp). The extent
actually covered is `(count - 1) * |step| + 1`. Consequences:

1. An index view (`GetView("[0]")`) passes step 0 for the removed axis. The
   window is 0 rows high, RasterIO skips it, and the read succeeds without
   writing the buffer.
2. A step that does not divide the extent overruns it: `[::2,::2]` on 5 x 5
   requests 6 x 6.
3. When the window fits, it is decimated (nearest) instead of picking
   `start + i * step`: `[::2,::2]` on 6 x 6 gives columns 1, 3, 5. If the
   band has overviews, the values come from an overview.

Multidim VRT `<SourceBand>` sources go through the same code. Found with
`[::14,::14]` on a 13333 x 13333 GeoTIFF source: "Requested (0,0) of size
13342x13342 on raster of 13333x13333".

### Steps to reproduce the issue

```python
from osgeo import gdal
import numpy as np
gdal.UseExceptions()

def band(n):
    ds = gdal.GetDriverByName("MEM").Create(f"a{n}", n, n, 1, gdal.GDT_Int16)
    ds.GetRasterBand(1).WriteArray(np.arange(n * n, dtype=np.int16).reshape(n, n))
    return ds

ds5, ds6 = band(5), band(6)
a5, a6 = ds5.GetRasterBand(1).AsMDArray(), ds6.GetRasterBand(1).AsMDArray()

buf = np.full(5, -999, dtype=np.int16)
print(a5.GetView("[0]").ReadAsArray(buf_obj=buf))  # [-999 -999 -999 -999 -999], expected [0 1 2 3 4]
print(a6.GetView("[::2,::2]").ReadAsArray()[0])    # [ 7  9 11], expected [0 2 4]
a5.GetView("[::2,::2]").ReadAsArray()              # Access window out of range ... (0,0) of size 6x6 on raster of 5x5
```

(Fuller script covering `Dataset.AsMDArray()`, `GetResampled()`, a GTiff
with overviews and a multidim VRT: inline or attach
notes/2026-11-26-mdim-classic-strided-read-repro.py.)

### Versions and provenance

Same output on 3.12.3, 3.13.3 and 3.14.0dev-9c765f0bdd (osgeo/gdal
ubuntu-small-latest image). The code is unchanged on master 948f102a.

### Additional context

A `(count - 1) * |step| + 1` window fixes 1 and 2. For step > 1 it doesn't
fix 3: resampling that window into `count` cells picks 1, 4, 6, 9 for step 3
over 20 pixels. Exact picks probably need a full-resolution read, for example
like `GDALMDArray::ReadUsingContiguousIRead()`, or row by row. I can open a
PR with a test.

<!-- Declaration (adjust): Found with gdalraster on a multidim VRT. I used an
LLM tool (Claude) to trace the code, write the repro and draft this text; I
checked the results and rewrote it. -->
