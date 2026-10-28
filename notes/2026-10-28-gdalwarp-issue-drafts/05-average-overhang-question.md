**Title:** gdalwarp -r average/mode: edge source pixels weighted above 1 when the target pixel overhangs the source — intended?

(A question rather than a bug report. It may fit better as a GitHub
discussion or a gdal-dev post.)

### What is the behaviour?

In `GWKAverageOrModeComputeSourceCoords` / `COMPUTE_WEIGHT`,
`iSrcXMin = max(floor(dfXMin + eps), 0)`. When the destination pixel's box
starts left of the source (`dfXMin < 0`), the first column's weight is
`1 - (dfXMin - iSrcXMin) = 1 - dfXMin`, which is more than 1. The far edges
and rows behave the same way. So source edge pixels are overweighted, in
proportion to how far the target pixel hangs off the source.

### Steps to reproduce the issue

```python
from osgeo import gdal
import numpy as np
gdal.UseExceptions()
ds = gdal.GetDriverByName("MEM").Create("", 4, 1, 1, gdal.GDT_Float32)
ds.SetGeoTransform([0, 1, 0, 1, 0, -1])
ds.GetRasterBand(1).WriteArray(np.array([[1, 2, 3, 4]]))
for x0, x1 in ((-1, 3), (2, 6)):
    o = gdal.Warp("", ds, format="MEM", resampleAlg="average", width=1, height=1,
                  outputBounds=[x0, 0, x1, 1])
    print(x0, x1, o.ReadAsArray().tolist())
```

```
-1 3 [[1.75]]   # weights 2, 1, 1; clipped footprint would give 2.0
2 6 [[3.75]]    # weights 1, 3;    clipped footprint would give 3.5
```

`mode` is affected the same way: a Byte source over [1, 5] gives 4 (weight
2), where clipped weights would tie 2, 3, 4 and `MODE_TIES=FIRST` would
give 2.

### Question

Is this intended, i.e. extrapolating the edge value into the missing area?
If not, the clipped weight would be `1 - (max(dfXMin, 0) - iSrcXMin)`.

### Versions and provenance

GDAL 3.14.0dev-739fcf03bf, self-built, Ubuntu 24.04.

<!-- Declaration as in the other drafts. -->
