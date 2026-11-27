"""Repro for notes/2026-11-27-icechunk-vcc.md (driver gap G).

An Icechunk virtual chunk can be stored relative to a named virtual chunk
container, `vcc://<container name>/<rest>`, which the reader resolves with
the container of that name in the repository config (Icechunk named
containers, icechunk-python >= 2.3). GDAL's Icechunk driver does not resolve
the name: it treats the location as a local, non-network path.

One uint8 array of 2 x 4, one chunk per row, no compression (so no codec is
involved). Both chunks reference the same 8-byte file, served over local
HTTP (file:// locations fail on their own, gap C):

  row 0  absolute   http://127.0.0.1:PORT/chunk.bin      bytes 0-3  -> 0 1 2 3
  row 1  relative   vcc://data/chunk.bin                 bytes 4-7  -> 4 5 6 7
         container  name "data", url_prefix http://127.0.0.1:PORT/

PORT is a free port chosen by `make` and kept in DIR/port (the container's
url_prefix holds it).

    python3 2026-11-27-icechunk-vcc-repro.py make DIR    # icechunk-python >= 2.3, zarr 3
    python3 2026-11-27-icechunk-vcc-repro.py read DIR    # icechunk-python and GDAL (master)

`read` serves DIR/data on the same port and reads each row with
icechunk-python + zarr (both rows expected) and with GDAL's Icechunk driver.
The two phases can run in different environments that share DIR (GDAL
master has the driver; a GDAL release has none).
"""
import functools
import http.server
import os
import sys
import threading

import numpy as np

class RangeHandler(http.server.SimpleHTTPRequestHandler):
    """Static files with single byte ranges (virtual chunks are range reads)."""

    def do_GET(self):
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().do_GET()
        data = open(path, "rb").read()
        a, _, b = rng.removeprefix("bytes=").partition("-")
        a = int(a) if a else len(data) - int(b)
        b = int(b) if b and rng.split("=")[1][0] != "-" else len(data) - 1
        part = data[a:b + 1]
        self.send_response(206)
        self.send_header("Content-Range", f"bytes {a}-{a + len(part) - 1}/{len(data)}")
        self.send_header("Content-Length", str(len(part)))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        self.wfile.write(part)

    def log_message(self, *a):
        pass


def serve(directory, port=0):
    handler = functools.partial(RangeHandler, directory=directory)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def make(d):
    import icechunk
    import zarr
    srv = serve(d)  # only to take a free port
    port = srv.server_address[1]
    srv.shutdown()
    srv.server_close()
    with open(f"{d}/port", "w") as f:
        f.write(str(port))
    PREFIX = f"http://127.0.0.1:{port}/"
    os.makedirs(f"{d}/data", exist_ok=True)
    with open(f"{d}/data/chunk.bin", "wb") as f:
        f.write(bytes(range(8)))
    cfg = icechunk.RepositoryConfig.default()
    cfg.set_virtual_chunk_container(icechunk.VirtualChunkContainer(PREFIX, icechunk.http_store(), name="data"))
    repo = icechunk.Repository.create(icechunk.local_filesystem_storage(f"{d}/repo"), config=cfg,
                                      authorize_virtual_chunk_access={PREFIX: icechunk.credentials.HttpAccess})
    s = repo.writable_session("main")
    g = zarr.group(store=s.store)
    g.create_array("a", shape=(2, 4), chunks=(1, 4), dtype="uint8", compressors=None, fill_value=255)
    failed = s.store.set_virtual_refs("a", [
        icechunk.VirtualChunkSpec(index=[0, 0], location=f"{PREFIX}chunk.bin", offset=0, length=4),
        icechunk.VirtualChunkSpec(index=[1, 0], location="vcc://data/chunk.bin", offset=4, length=4),
    ], validate_containers=True)
    assert not failed, failed
    print("icechunk", icechunk.__version__, "| commit", s.commit("two virtual chunks: absolute and vcc://"))


def read(d):
    port = int(open(f"{d}/port").read())
    PREFIX = f"http://127.0.0.1:{port}/"
    srv = serve(f"{d}/data", port)
    try:
        import icechunk
        import zarr
        st = icechunk.local_filesystem_storage(f"{d}/repo")
        repo = icechunk.Repository.open(st, authorize_virtual_chunk_access={PREFIX: icechunk.credentials.HttpAccess})
        a = zarr.open_group(repo.readonly_session("main").store, mode="r")["a"]
        print(f"icechunk-python {icechunk.__version__}: row 0 {a[0].tolist()}, row 1 {a[1].tolist()}")
    except ImportError:
        print("icechunk-python: not installed here; skipped")
    from osgeo import gdal
    gdal.UseExceptions()
    print(gdal.VersionInfo("--version"))
    if gdal.GetDriverByName("Icechunk") is None:
        sys.exit("this GDAL has no Icechunk driver (master only)")
    for allow_local in ("NO", "YES"):
        gdal.SetConfigOption("ICECHUNK_ALLOW_LOCAL_CHUNK_LOCATION", allow_local)
        arr = gdal.OpenEx(f"ICECHUNK:{d}/repo", gdal.OF_MULTIDIM_RASTER).GetRootGroup().OpenMDArray("a")
        for row, expected in ((0, [0, 1, 2, 3]), (1, [4, 5, 6, 7])):
            try:
                got = arr.ReadAsArray(array_start_idx=[row, 0], count=[1, 4])[0].tolist()
                res = f"{got} ({'ok' if got == expected else 'WRONG, expected ' + str(expected)})"
            except Exception as e:
                res = f"ERROR {str(e).splitlines()[0]}"
            print(f"GDAL, ICECHUNK_ALLOW_LOCAL_CHUNK_LOCATION={allow_local}, row {row}: {res}")
    srv.shutdown()


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("make", "read"):
        sys.exit(__doc__)
    {"make": make, "read": read}[sys.argv[1]](os.path.abspath(sys.argv[2]))
