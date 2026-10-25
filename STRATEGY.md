# Strategy

Working note, 2026-10-25. Provisional; edit freely.

## What the record shows

- 56 commits merged into GDAL since 2019, plus small PROJ and GEOS fixes.
- The record peaks in 2023 (31 commits, mostly vrt:// options). Since 2025
  the work has moved to multidim, Zarr and SWIG bindings: fewer, larger
  changes that take more review.
- On 14 of the merged branches the last commit is a maintainer's (review
  suggestions, test and doc touch-ups), so review time from the core team is
  the real cost of each contribution.

## Themes

1. **Multidim and byte references.** get-refs, chunk reference iteration,
   ReadCompressedData, Zarr V3 correctness. This is where GDAL meets the
   virtual-store ecosystem (Kerchunk, Icechunk, VirtualiZarr) and where
   wxylib needs GDAL as an oracle. Highest value, highest review cost.
2. **Georeferencing at the edges.** Longitude wrap, polar extents,
   geolocation arrays, warp heuristics. Long-standing personal expertise,
   small fixes, easy to illustrate.
3. **vrt:// as a compositional interface.** Feature-complete enough; now
   maintenance, docs and examples rather than more options.
4. **Docs.** Steady small fixes; low cost to maintainers.

## How to contribute (the house rules for this tracker)

- Conformance and ecosystem work in support of GDAL, PROJ and GEOS; never a
  parallel or competing effort.
- Issue first, with a short reproducer, for anything beyond a typo.
- One concern per PR, no stacked PRs, house commit style
  (`Component: what (fixes #N)`), proportionate tests.
- Pace: one open PR per area at a time. #39 shows how a burst of stacked
  PRs gets closed even when the bugs behind it are real.
- Code, tests and upstream text are mine; tool use is declared in the PR
  template. The tracker holds the investigation, repros and notes.
- In tracker issues, comments and commit messages, write upstream items as
  plain text ("GDAL PR 14677"), not as GitHub references or issue/PR URLs,
  so upstream threads do not collect a flurry of backlinks. Link on purpose,
  one at a time, when the backlink helps others. Links in repo files are fine.
- Larger design changes (Zarr fill_value semantics, new algorithms) go to a
  discussion on the issue tracker or gdal-dev before code; RFC if the PSC
  asks.

## get-refs route (decision pending)

Options for #14677:

- **A. Land the core helpers first** (mdim-helpers: the part useful to gcore
  and the Zarr driver), then a slimmer `gdal mdim get-refs` on top. Smaller
  reviews, reuses existing smells (#36 lists the clean-ups).
- B. Revive #14677 as is, with the #36 clean-ups applied.
- C. Ask on the PR or gdal-dev whether the maintainers want the algorithm in
  GDAL at all, or prefer the helpers plus an external tool.

Provisional default: A, after reading the last review on #14677. stage1-mvp
and fast-path-h5-chunk-refs-iter stay as later follow-ups.

## Open questions

- Which upstream issues did I open, and which are still open? (gap in
  CONTRIBUTIONS.md)
- Is #14677 still open, and what did the last review ask for?
- Does wxylib need anything from GDAL beyond get-refs and Zarr fixes?

## Measures

Merged PRs per quarter, median time to merge, and how many PRs needed
maintainer follow-up commits. Re-run scripts/sweep.sh each quarter.
