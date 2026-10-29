# Findings to report later (collected from terrio igh and ob_tran work)

Hold until the #272 list (qsc, HEALPix, ISEA) is done, then file in one batch.

## For mdsumner/osgeo-upstream (PROJ behaviour, checked with PROJ 9.8.1)

- ob_tran accepts a non-finite pole: `+o_lat_p=nan` and `+o_lon_p=inf` build a CRS.
- ob_tran reads an unparseable pole angle as 0: `+o_lat_p=abc` is accepted (only an empty value is refused).
- Spherical sinu inverse returns a latitude past 90 degrees for northings beyond the pole, instead of refusing; ob_tran then rotates that into a valid-looking point.
- utm is refused on a sphere (terrio accepts it); worth recording as a difference, not a bug.
- Ellipsoidal eqc is absent in PROJ 9.4 (GDAL 3.8.4) and present in 9.8.1; results for `+proj=eqc +datum=WGS84` change across versions.

## For rust-proj-capability (benchmark coverage)

- ob_tran has one fixture (seed-ob_tran-moll). Add the other pole forms (o_lon_c/o_lat_c/o_alpha, two equator points), the transverse case (o_lat_p=0), and an inner projection with its own parameters (lcc, merc lat_ts).
- Refusal cases PROJ makes for ob_tran: o_proj=ob_tran, o_lat_c=90 with o_alpha, o_lat_1 == o_lat_2, o_lat_1 = 0, |o_lat_1| = 90.
- The non-finite and unparseable pole cases above, so libraries can be scored on refusing them.
- Note that pyproj's CRS route and Transformer.from_pipeline agree for ob_tran (unlike gamma-only omerc), so either can be the oracle.
- Version note for eqc on an ellipsoid (oracle depends on PROJ version).

## From healpix/rhealpix (2026-10-28)

- PROJ 9.8.1 converts US survey feet with two different factors. In a projection step's own `+units=us-ft` (as the CRS route uses for methods without an EPSG mapping, such as healpix and rhealpix) it parses the units table's string, 0.304800609601219. In `+proj=unitconvert +xy_in=us-ft` (the CRS route for EPSG-mapped methods, such as igh) it uses the numeric 1200/3937. They differ by about 1.4e-16 relative, enough to move a point on a projection's domain edge in or out (e.g. HEALPix with rot_xy=-45 in us-ft: PROJ's own inverse of a pole accepts it on one route and refuses on the other's arithmetic). The same applies to us-yd, us-ch and us-mi. terrio uses 1200/3937 throughout. Candidate for PROJ (osgeo-upstream).

- PROJ healpix.cpp `in_image`: pnpoly skips the polygon's closing edge (last vertex back to the first). For rHEALPix that edge is the image's left side, so the inverse accepts points left of the image between the polar squares: `+proj=rhealpix +R=1` inverse of (-4, 0) gives (130.82, 0) in PROJ 9.8.1, where (3.3, 0) on the right is refused. HEALPix is unaffected (its first and last vertices coincide). terrio follows PROJ and documents it (opengeos/terrio#367).

## From isea (2026-10-28)

- PROJ 9.8.1 isea.cpp on an ellipsoid: the forward takes the geodetic latitude on a sphere of the semi-major axis (TODO in the code), the inverse uses the authalic radius but not the authalic latitude, so inverse(forward(p)) != p: `+proj=isea +datum=WGS84`, (147, -42) round-trips to (147.166, -41.969). Fixed in PROJ 9.9 by the new polyhedral implementation; worth a version note rather than a report.
- PROJ 9.8.1 isea inverse returns inf (no error message) whenever +azi, +lon_0 or +lat_0 (other than the defaults), +resolution != 4 or +aperture != 3 is given, even in +mode=plane where resolution and aperture do not change the forward.
- PROJ 9.8.1 isea applies +lon_0 twice: as the central meridian (generic) and as the icosahedron's orientation longitude (o_lon).
- PROJ 9.4 isea has no inverse and a forward up to 2 mm from 9.8.1; PROJ 9.9.0 replaced isea (polyhedral.cpp, A5-derived, Apache-2.0): new default origin, authalic latitude, orient_lon 11.20 on ellipsoids, mode/resolution/aperture gone, net/dual/orient_lat/orient_lon added. Three incompatible definitions across 9.4, 9.5-9.8 and 9.9.
- For rust-proj-capability: method-isea is from PROJ 9.9.0 only (WGS 84); add a sphere case and a version note, since 9.8.1 gives (11140072.07, -6179576.36) for (147, -42) and 9.9.0 (11139011.78, -6164461.28).
