# GDAL issue drafts (warp-sandbox, 2026-11-08)

Two drafts for OSGeo/gdal, copied from mdsumner/warp-sandbox `notes/`
(commit 0868cf1, merged in aae1578). The evidence is in warp-sandbox
`bench/README.md`, sections 4 and 5, and the scripts beside it. Written
against `3.14.0dev-fa1fc3c77e`.

The sandbox README says these "can be pasted into an issue as they are".
Here they are **starting points, not text to paste**, as with
[../2026-10-28-gdalwarp-issue-drafts/](../2026-10-28-gdalwarp-issue-drafts/README.md):
GDAL's LLM tool policy (RFC 111) and STRATEGY.md mean the issue text is
rewritten by me, kept short, with tool use declared.

| File | Finding | Kind | Suggested order |
|---|---|---|---|
| [01-warp-antimeridian-strip.md](01-warp-antimeridian-strip.md) | A target crossing the antimeridian of a global lon/lat source reads a full-width source strip; two edge windows need 11.3x fewer pixels | performance, with a fix sketch (rwarp, hypertidy/rwarp#57) | 1 |
| [02-gtiff-adviseread-prefetch.md](02-gtiff-adviseread-prefetch.md) | GTiff doesn't implement `AdviseRead()`, so separate windows over /vsicurl/ can't be prefetched together | feature request | 2, after 01 has a response; 01 is its motivating case |

Points to settle before filing:

- 01 says 235 x 418 per edge window, 200,600 pixels, 11.3x; warp-sandbox
  `bench/README.md` section 4 says 234 x 416, 195 k, 11.6x. Pick one (the
  draft is the later, more careful count) and quote only that.
- 01 relies on a public COG (GEBCO_2025 on source.coop) and gdalwarp alone,
  so it reproduces without the sandbox. The timings need the sandbox's local
  slow server; keep them to one sentence upstream.
- 02 overlaps the AdviseRead plumbing in tracker #39 (work package 3:
  Python buffer args, mdim bridge overview forwarding, and WP3c, the warper
  advising its source window). Read that before filing, and check whether
  `GDAL_NUM_THREADS` multi-threaded reads cover the case under other
  conditions (draft 02's first question).
- Re-run 01 on current master before filing.
