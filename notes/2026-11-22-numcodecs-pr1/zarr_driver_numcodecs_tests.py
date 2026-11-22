# Append to autotest/gdrivers/zarr_driver.py. Same shape as
# test_zarr_driver_v3_decode_pcodec: committed stores under data/zarr/v3/,
# written by zarr-python when absent.


###############################################################################
# Test decoding of the Zarr V3 numcodecs.shuffle and numcodecs.zlib codecs


@pytest.mark.parametrize(
    "name,dtype",
    [
        ("numcodecs_shuffle_zlib_uint8", "uint8"),
        ("numcodecs_shuffle_zlib_int16", "int16"),
        ("numcodecs_shuffle_zlib_float32", "float32"),
        ("numcodecs_shuffle_zlib_float64", "float64"),
        ("numcodecs_zlib", "int16"),
    ],
)
@gdaltest.enable_exceptions()
def test_zarr_driver_v3_decode_numcodecs_shuffle_zlib(name, dtype):

    np = pytest.importorskip("numpy")
    gdaltest.importorskip_gdal_array()

    ar = (np.arange(1, 9).reshape(2, 4) * 25).astype(dtype)

    dirname = f"data/zarr/v3/{name}.zarr"
    if not os.path.exists(dirname):
        import zarr

        codecs = [zarr.codecs.BytesCodec()]
        if "shuffle" in name:
            codecs.append(zarr.codecs.numcodecs.Shuffle(elementsize=ar.itemsize))
        codecs.append(zarr.codecs.numcodecs.Zlib(level=1))
        zarr.array(ar, chunk_shape=ar.shape, codecs=codecs, store=dirname)

    ds = gdal.Open(dirname)
    np.testing.assert_equal(ds.ReadAsArray(), ar)


###############################################################################
# Test that numcodecs.shuffle with an unsupported elementsize is rejected


@gdaltest.enable_exceptions()
def test_zarr_driver_v3_numcodecs_shuffle_invalid_elementsize():

    dirname = "data/zarr/v3/numcodecs_shuffle_invalid_elementsize.zarr"
    if not os.path.exists(dirname):
        np = pytest.importorskip("numpy")
        import zarr

        zarr.array(
            np.arange(6, dtype="uint8").reshape(2, 3),
            chunk_shape=(2, 3),
            codecs=[
                zarr.codecs.BytesCodec(),
                zarr.codecs.numcodecs.Shuffle(elementsize=3),
                zarr.codecs.numcodecs.Zlib(level=1),
            ],
            store=dirname,
        )

    with pytest.raises(Exception, match="elementsize"):
        gdal.Open(dirname)
