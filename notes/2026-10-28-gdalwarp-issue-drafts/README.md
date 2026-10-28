# GDAL issue drafts (warp kernel findings)

Drafts for OSGeo/gdal, from
[../2026-10-28-gdalwarp-kernel-findings.md](../2026-10-28-gdalwarp-kernel-findings.md)
(items 1-7). Written during the rwarp sprint and copied here from a local
scratch folder; the filing todos are in PLANS.md, "Warp kernels". These are
**starting points, not text to paste**:

- GDAL's LLM tool policy (`doc/source/community/ai_tool_policy.rst`, RFC 111)
  requires tickets to be mostly written by a human, LLM use to be declared,
  and penalises verbose text. STRATEGY.md says the same: upstream text
  is written by me.
- So rewrite each one in my own words, keep it short, and tick the template's
  LLM box. A possible declaration line is in each draft; adjust it to what
  was actually done.

All repros were re-run on 2026-10-28 with `3.14.0dev-739fcf03bf`, which was
OSGeo master at the time (a fresh fetch had no newer commits).

| File | Finding (notes item) | Kind | Suggested order |
|---|---|---|---|
| [01-chunk-scale-offset.md](01-chunk-scale-offset.md) | Kernel scale estimate ignores the chunk's destination offset (3) | bug, largest effect | 1 |
| [02-mode-ties-list-path.md](02-mode-ties-list-path.md) | `MODE_TIES=MIN/MAX` ignored on a value's first occurrence for 32/64-bit and float types (1), with the `FIRST` docs wording (2) | bug + docs | 2 |
| [03-dstnodata-float-working-type.md](03-dstnodata-float-working-type.md) | Float working type lets a valid pixel round onto `-dstnodata` (5), with the two rounding rules (6) as context | bug | 3 |
| [04-cubicspline-tail.md](04-cubicspline-tail.md) | `cubicspline` weight not zero beyond \|x\| = 2 when downsampling (7) | minor bug | 4 |
| [05-average-overhang-question.md](05-average-overhang-question.md) | `average`/`mode` edge weights above 1 when the footprint overhangs the source (4) | question, maybe intentional | last, or a discussion instead |

Repros: [../2026-10-28-gdalwarp-kernel-repro.py](../2026-10-28-gdalwarp-kernel-repro.py)
covers items 1, 2, 3, 5, 6 and 7 (item 3 prints the `dfYScale` debug lines);
each draft also inlines a minimal snippet. Item 4 still has no standalone
repro.

Pace (STRATEGY.md): file one at a time, not as a burst, and offer a PR
only once the issue has had a response.

Each of 01-04 has a small, local fix, so a PR with a test could follow
after filing. rwarp already behaves the fixed way for 01, 02 and 04 (see
rwarp `book/src/gdal-parity.md`, "Where rwarp deliberately differs").
