# GitHub Project board: proposed setup

One user-level Project ("OSGeo upstream") holding this tracker's issues plus
my OSGeo PRs and issues (added by URL).

Fields:

- Status (single select): Idea, Investigating, Ready, Upstream, Done, Parked
  (same words as the `status:` labels)
- Priority: P1, P2, P3
- Area: vrt, mdim, zarr, netcdf, warp, drivers, python, docs, proj, geos
- Upstream link (text): the OSGeo issue or PR
- Fork branch (text)

Views:

1. **Board by Status**, filtered to P1 and P2: the working view.
2. **Table by Area**, grouped by Area, sorted by Priority: the consolidated
   list, matching PLANS.md.
3. **Upstream**: filter Status = Upstream; shows what is waiting on
   maintainers, with the Upstream link column.
4. **wxylib**: filter label `wxylib` (get-refs, Zarr, byte access).
5. **Done**: Status = Done, grouped by quarter, for reporting.

Automation: built-in workflows "item closed -> Done" and "item added ->
Idea".
