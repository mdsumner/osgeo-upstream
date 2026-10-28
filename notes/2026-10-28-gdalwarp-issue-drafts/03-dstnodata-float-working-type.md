**Title:** gdalwarp: with a float working type, a valid pixel can be written as -dstnodata in an integer output

### What is the bug?

The kernel moves a result off the destination nodata value (`AvoidNoData`)
while it is still in the working type. Conversion to the output type comes
later, in `GDALCopyWords`. With a float working type and an integer output,
a value like 0.2 isn't equal to nodata 0, so it isn't moved. It is then
rounded to 0 on write, which is nodata. A valid pixel silently becomes
nodata. With an integer working type, the same case is moved to 1, with a
warning.

### Steps to reproduce the issue

```python
from osgeo import gdal
import numpy as np
gdal.UseExceptions()
ds = gdal.GetDriverByName("MEM").Create("", 2, 1, 1, gdal.GDT_Float32)
ds.SetGeoTransform([0, 1, 0, 1, 0, -1])
ds.GetRasterBand(1).WriteArray(np.array([[0.2, 1.0]]))
o = gdal.Warp("", ds, format="MEM", resampleAlg="near", width=2, height=1,
              dstNodata=0, outputType=gdal.GDT_Byte)
print(o.ReadAsArray().tolist())   # [[0, 1]]; expected [[1, 1]]
```

### Versions and provenance

GDAL 3.14.0dev-739fcf03bf, self-built, Ubuntu 24.04. Also 3.8.4.

### Additional context

Suggested fix: when the output band is an integer type different from the
working type, apply the nodata check to the value after rounding to the
output type, or do the check at write time.

Related, probably docs only: rounding into an integer output also depends on
the working type. The kernel rounds half up (`floor(x + 0.5)`), but
`GDALCopyWords` rounds half away from zero. So averaging [-2, -3] into Int16
gives -2 from an Int16 source and -3 from a Float32 source. A sentence under
`-ot`/`-wt` might be enough.

<!-- Declaration (adjust): Found while checking a Rust reimplementation
(hypertidy/rwarp) against gdalwarp. I used an LLM tool (Claude) to help read
the code and write the repro; I checked the numbers and wrote this text. -->
