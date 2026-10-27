# Multidimensional VRT findings, 2026-10-28

Found while building and round-tripping multidim VRTs over long daily
collections (one file per day, e.g. GHRSST MUR COGs on source.coop, OISST
NetCDF): writing VRTs with rgdal-dev/xvrt and hypertidy/vrtstack, reading
them with GDAL and hypertidy/gdalxarray.

Tested on GDAL 3.13.3 (conda-forge). **Not yet checked on master.**
Repro: [2026-10-28-mdim-vrt-repro.py](2026-10-28-mdim-vrt-repro.py), output
below. Upstream issue text, if any, still to be written (see README, "How
contributions are made").

## 1. Strided read across sources fails; the CLI exits 0 with fill values

A multidim VRT array whose dimension is split over several `<Source>`
elements (the normal one-file-per-step layout) cannot be read with a step
that crosses from one source to the next.

```
step 1 across sources (expect [0..5]): [0, 1, 2, 3, 4, 5]
step 2 across sources (expect [0, 2, 4]): ERROR arrayStartIdx[0] = 1 >= 1
step 3 across sources (expect [0, 3]): ERROR arrayStartIdx[0] = 2 >= 1
step 2 within one source (expect [0, 2, 4]): [0, 2, 4]
```

- Same with `<SourceBand>` + `<SourceTranspose>` (GeoTIFF sources) as with
  `<SourceArray>` (NetCDF sources), and with or without `<SourceSlab>`.
- A VRT written by `gdal mdim mosaic` fails the same way (message variant:
  `arrayStartIdx[0] + (count[0]-1) * arrayStep[0] >= 1`).
- The message suggests the step is applied inside a source of extent 1 along
  that dimension, rather than first choosing the sources the strided request
  intersects.

On the command line the same request is worse than an error:

```
gdal mdim convert --array 'name=v,view=[::2,...]' a.vrt o.nc
  exit code 0; stderr: 'ERROR 1: arrayStartIdx[0] = 1 >= 1'
  written values along t: [-32767, -32767, -32767] (expect [0, 2, 4])
```

`--scale-axes "t(2)"` behaves the same. Writing to `.vrt` instead succeeds
(a `<SourceView>[::2,...]</SourceView>` over the input) and the error appears
only when the data is read. Contiguous selections (`view=[1:4,...]`,
`--subset "t(min,max)"`) work.

Why it matters: "every Nth day" (one value per year, per month) is a natural
query over a daily collection, and the CLI path silently produces a file of
fill values with a success exit code.

Workaround in tools: read the wanted positions one at a time or in
contiguous runs.

To do: check on master; find the strided path in the VRT mdim source read
(frmts/vrt, VRTMDArraySourceFromArray); separately, whether
`gdal mdim convert` should fail (non-zero exit) when a read errors.

## 2. mdim `<BlockSize>`: schema says spaces, driver wants commas

```
<BlockSize>1,3,4</BlockSize>: [1, 3, 4]
<BlockSize>1 3 4</BlockSize>: ERROR Invalid number of values in BLOCKSIZE
gdalvrt.xsd: BlockSize types ['integerList']; integerList = xs:list of xs:integer (whitespace-separated)
```

The driver's form (commas) is what tools write, so every multidim VRT with a
`<BlockSize>` fails XSD validation against GDAL's own schema. Either the
schema type or the parser is wrong; the schema is the cheaper fix (a pattern
for comma-separated integers), unless the parser should accept both.

To do: check master's gdalvrt.xsd and the BLOCKSIZE parse in the VRT mdim
driver; see whether any test validates mdim VRT output against the XSD.

## 3. `dataAxisToSRSAxisMapping`: silent defaults and a 0 in slices

The mapping lists, for each SRS axis in WKT order, the 1-based array dimension
holding it, counting every dimension (time included). On a `(t, y, x)` array
with EPSG:4326 WKT (latitude first) the right value is `2,3`.

```
attribute absent : 3D mapping [1, 2], 2D slice mapping [0, 2]
attribute '2,1'  : 3D mapping [2, 1], 2D slice mapping [2, 0]
attribute '2,3'  : 3D mapping [2, 3], 2D slice mapping [2, 1]
```

- With the attribute absent GDAL assumes the identity, which maps latitude to
  the time dimension. Writers that omit it (or copy `2,1` from 2D examples)
  produce VRTs that open without complaint.
- Slicing such an array (`GetView("[0,:,:]")`, `AsClassicDataset`) reports a
  mapping containing 0, which is not a valid axis number.

Possible directions, smallest first: warn at open when a mapping points at a
dimension whose type is TEMPORAL/VERTICAL, or when its length differs from
the SRS axis count; derive a default from HORIZONTAL_X / HORIZONTAL_Y
dimension types when the attribute is absent; make the view/slice path drop
or reject a mapping it cannot remap instead of emitting 0.

To do: check master; read how the VRT mdim driver sets the mapping and how
`GetView` / `AsClassicDataset` remap it.

## Related, already done downstream (no GDAL change needed)

- `<SourceSlab offset count step>` on every source, so a read opens only the
  sources it touches: `gdal mdim mosaic` already writes it (3.13), and xvrt
  and vrtstack now do too. The earlier idea of GDAL needing this is covered
  for mosaic output.
- xvrt, vrtstack: computed axis mapping (item 3), comma BlockSize (item 2).
- gdalxarray: the multidim path now attaches the array SRS, keeps time
  encoding, units and dimension types.
