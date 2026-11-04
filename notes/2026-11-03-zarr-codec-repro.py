"""Zarr codec gaps in GDAL: tiny fixtures and a GDAL read check.

Two steps, so the fixtures can be written where zarr-python and imagecodecs
are installed and read where the GDAL under test is:

    python 2026-11-03-zarr-codec-repro.py make  fx   # zarr, numcodecs, imagecodecs
    python 2026-11-03-zarr-codec-repro.py check fx   # osgeo.gdal (and numpy)

Every Int16 store holds the same 4 x 6 array (values a*7 - 50), chunks 2 x 3,
so a correct read returns expected.npy exactly; the floatpred stores hold
the Float32 array in expected_f4.npy. Fixtures written 2026-11-03
with zarr 3.4.2, numcodecs 0.17.1, imagecodecs 2026.10.10.
"""

import json
import os
import shutil
import sys

import numpy as np

SHAPE, CHUNKS = (4, 6), (2, 3)


def expected():
    return (np.arange(24, dtype="<i2").reshape(SHAPE) * 7 - 50).astype("<i2")


def expected_f4():
    return (np.arange(24, dtype="<f4").reshape(SHAPE) * 1.5 - 2).astype("<f4")


def make(out):
    import numcodecs
    import numcodecs.zarr3 as nc3
    import zarr
    import imagecodecs.numcodecs as icn
    from imagecodecs.zarr import Delta as DeltaV3, register_codecs
    from imagecodecs.zarr import Floatpred as FloatpredV3

    icn.register_codecs(verbose=False)
    register_codecs(verbose=False)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    a = expected()

    def write(name, fmt, data=a, fill=-32768, **kw):
        z = zarr.create_array(f"{out}/{name}.zarr", shape=SHAPE, chunks=CHUNKS,
                              dtype=data.dtype, zarr_format=fmt,
                              fill_value=fill, **kw)
        z[:] = data

    # Zarr V3: what zarr-python / VirtualiZarr / Icechunk stores carry
    write("v3_numcodecs_shuffle_zlib", 3,
          compressors=[nc3.Shuffle(elementsize=2), nc3.Zlib(level=1)])
    write("v3_numcodecs_zlib", 3, compressors=[nc3.Zlib(level=1)])
    write("v3_numcodecs_zstd", 3, compressors=[nc3.Zstd(level=1)])
    write("v3_imagecodecs_delta_zstd", 3, filters=[DeltaV3(axis=-1, dist=1)],
          compressors=[nc3.Zstd(level=1)])
    # Zarr V2: what kerchunk JSON / Parquet refs carry
    write("v2_shuffle_zlib", 2, filters=[numcodecs.Shuffle(elementsize=2)],
          compressors=numcodecs.Zlib(level=1))
    write("v2_imagecodecs_delta_zstd", 2,
          # shape and dtype must be given: with shape null the V2 codec
          # decodes along the flattened chunk (zarr-python then reads it
          # wrong too). tifffile and raad.virtualize write both.
          filters=[icn.Delta(axis=-1, dist=1, shape=CHUNKS, dtype="<i2")],
          compressors=numcodecs.Zstd(level=1))
    # TIFF PREDICTOR=3 (floating point), Float32
    f = expected_f4()
    write("v3_imagecodecs_floatpred_zstd", 3, data=f, fill=float("nan"),
          # array-to-bytes in V3: it takes the place of the bytes codec
          serializer=FloatpredV3(axis=-1, dist=1),
          compressors=[nc3.Zstd(level=1)])
    write("v2_imagecodecs_floatpred_zstd", 2, data=f, fill=float("nan"),
          filters=[icn.Floatpred(axis=-1, dist=1, shape=CHUNKS, dtype="<f4")],
          compressors=numcodecs.Zstd(level=1))
    np.save(f"{out}/expected.npy", a)
    np.save(f"{out}/expected_f4.npy", f)

    for name in sorted(os.listdir(out)):
        for meta in ("zarr.json", ".zarray"):
            p = os.path.join(out, name, meta)
            if os.path.exists(p):
                m = json.load(open(p))
                codecs = m.get("codecs") or {"filters": m.get("filters"),
                                             "compressor": m.get("compressor")}
                print(f"{name}: {json.dumps(codecs)}")


def check(out):
    from osgeo import gdal

    gdal.UseExceptions()
    print("GDAL", gdal.VersionInfo("--version"))
    want_i2 = np.load(f"{out}/expected.npy")
    want_f4 = np.load(f"{out}/expected_f4.npy")
    for name in sorted(os.listdir(out)):
        if not name.endswith(".zarr"):
            continue
        path = os.path.join(out, name)
        want = want_f4 if "floatpred" in name else want_i2
        try:
            ds = gdal.OpenEx(path, gdal.OF_MULTIDIM_RASTER)
            arr = ds.GetRootGroup().OpenMDArray(
                ds.GetRootGroup().GetMDArrayNames()[0])
            got = arr.ReadAsArray()
            status = "OK" if np.array_equal(got, want) else "WRONG VALUES"
        except Exception as e:  # noqa: BLE001
            status = f"ERROR {str(e).strip()}"
        print(f"{name:32s} {status}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("make", "check"):
        sys.exit(__doc__)
    {"make": make, "check": check}[sys.argv[1]](sys.argv[2])
