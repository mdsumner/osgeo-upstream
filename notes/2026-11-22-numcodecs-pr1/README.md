# PR 1 materials: numcodecs.zlib + numcodecs.shuffle (GDAL 14917)

- `v3/`: six stores written by zarr 3.2.1 / numcodecs 0.16.5 with the
  generator code inside the tests (one chunk each, 14-28 byte chunks). Copy
  into `~/gdal/autotest/gdrivers/data/zarr/v3/`.
- `zarr_driver_numcodecs_tests.py`: two tests to append to
  `autotest/gdrivers/zarr_driver.py`, replacing the runtime-built tests in
  `7f71b6c1e2`.

Checked 2026-11-22: with the WP4 build (`3.14.0dev-30732f5482`) all five
read stores match and the invalid one is refused ("only elementsize = 1, 2,
4 or 8 is supported (got 3)"); with the stock build (`fedfd3ec89`) all six
fail "Unsupported codec". Steps: [../2026-11-22-numcodecs-v3-plan.md](../2026-11-22-numcodecs-v3-plan.md).
