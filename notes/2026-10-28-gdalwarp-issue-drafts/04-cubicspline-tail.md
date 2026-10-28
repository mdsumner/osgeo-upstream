**Title:** gdalwarp -r cubicspline: kernel weight isn't zero beyond |x| = 2, making downsampled output asymmetric

### What is the bug?

`GWKBSpline()` (and `GWKBSpline4Values()`) evaluate the cubic B-spline as a
sum of truncated cubics, but leave out the last term, `(x - 2)^3_+`. So for
x > 2 the weight is `-(x - 2)^3` (unnormalised) instead of 0. At scale 1 the
window never reaches x > 2. When downsampling, the window is widened to
`R = ceil(2 / scale)` and evaluated at `(i - delta) * scale`, which goes past
2. Those taps get small negative weights, on the positive side only.

### Steps to reproduce the issue

A source symmetric about its centre, downsampled 64 -> 23 columns over the
same bounds, should give a mirror-symmetric output. Script: (inline it from
notes/2026-10-28-gdalwarp-kernel-repro.py, item 7).

```
cubicspline  max |out - mirror(out)| = 5.83e-05
cubic        max |out - mirror(out)| = 0
lanczos      max |out - mirror(out)| = 0
```

### Versions and provenance

GDAL 3.14.0dev-739fcf03bf, self-built, Ubuntu 24.04.

### Additional context

Suggested fix: return 0 for |x| >= 2 (or add the missing term) in both
functions. The effect is small (about 1e-4 relative here), but it's a
systematic one-sided bias.

<!-- Declaration (adjust): Found while checking a Rust reimplementation
(hypertidy/rwarp) against gdalwarp. I used an LLM tool (Claude) to help read
the code and write the repro; I checked the numbers and wrote this text. -->
