**Title:** gdalwarp -r mode: MODE_TIES=MIN/MAX ignored on a value's first occurrence for 32/64-bit and float types

### What is the bug?

For Byte/Int8/(U)Int16, mode uses a histogram and applies the tie rule on
every increment. For other types, `GWKModeRealType<T>` (and
`GWKModeComplexType`) keep a list of values. A value seen for the first time
is appended, but it is never compared with the current mode. It only becomes
the mode if there is none yet (`if (iModeIndex < 0) iModeIndex = i;`). So
the same data gives a different mode depending on the data type.

### Steps to reproduce the issue

```python
from osgeo import gdal
import numpy as np
gdal.UseExceptions()
for dt in (gdal.GDT_Byte, gdal.GDT_Int32, gdal.GDT_Float32):
    ds = gdal.GetDriverByName("MEM").Create("", 2, 2, 1, dt)
    ds.SetGeoTransform([0, 1, 0, 2, 0, -1])
    ds.GetRasterBand(1).WriteArray(np.array([[5, 3], [7, 1]]))
    got = {t: int(gdal.Warp("", ds, format="MEM", resampleAlg="mode", xRes=2, yRes=2,
                            warpOptions={"MODE_TIES": t}).ReadAsArray()[0, 0])
           for t in ("FIRST", "MIN", "MAX")}
    print(gdal.GetDataTypeName(dt), got)
```

```
Byte    {'FIRST': 5, 'MIN': 1, 'MAX': 7}
Int32   {'FIRST': 5, 'MIN': 5, 'MAX': 5}
Float32 {'FIRST': 5, 'MIN': 5, 'MAX': 5}
```

On a 64x64 source with four distinct values in each 2x2 block, warped 2:1,
Int32 and Float32 differ from Byte on 768 of 1024 pixels for both MIN and
MAX.

### Versions and provenance

GDAL 3.14.0dev-739fcf03bf, self-built, Ubuntu 24.04.

### Additional context

Suggested fix: in the branch that appends a new value, compare it with the
current mode the same way the increment branch does. `test_warp_mode_ties`
only covers ties at a count of 3 in Int16/Int32.

Related docs point: `gdalwarper.cpp` says for `MODE_TIES=FIRST` "the first
value encountered will be used". In both paths the tie is re-decided on each
increment, so FIRST keeps the value that first *reaches* the top count:
`[[5, 3], [3, 5]]` gives 3 for every type. Perhaps "the value that first
reaches the maximum count, in scan order".

<!-- Declaration (adjust): Found while checking a Rust reimplementation
(hypertidy/rwarp) against gdalwarp. I used an LLM tool (Claude) to help read
the code and write the repro; I checked the numbers and wrote this text. -->
