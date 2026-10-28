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

A 64x64 source with unit pixels over [0, 64], warped with `-r average` to a
20x20 grid of 4-unit pixels over [-8, 72]. The edge target pixels' means
match only with weights above 1 for the edge source pixels. (Case
`average_overhang` in hypertidy/rwarp `tests/fixtures/kernels/gen.py`.)

### Question

Is this intended, i.e. extrapolating the edge value into the missing area?
If not, the clipped weight would be `1 - (max(dfXMin, 0) - iSrcXMin)`.

### Versions and provenance

GDAL 3.14.0dev-739fcf03bf, self-built, Ubuntu 24.04.

<!-- Before filing: a standalone repro snippet would help; there isn't one
yet. Declaration as in the other drafts. -->
