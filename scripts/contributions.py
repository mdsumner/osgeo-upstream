"""Build CONTRIBUTIONS tables and the per-year figure from data/*.psv.

Run from the repo root after scripts/sweep.sh:  python3 scripts/contributions.py
"""
import collections
import re

# PR numbers the ancestry heuristic in sweep.sh cannot recover (rebased
# commits, or commits merged through another person's branch).
PR_OVERRIDES = {"7e0e87ad6": "14569", "850e886ac": "7201", "8a9d4a1a4": "",
                "2db55cc37": "8168"}
SKIP = {"d106a259e"}  # merge commit, not a change

AREAS = [  # (label, test on subject), first match wins
    ("gdal:vrt", lambda s: "vrt://" in s or "vrtcon" in s),
    ("gdal:mdim", lambda s: re.search(r"mdim|MDArray|RegularlySpaced|Zarr", s, re.I)),
    ("gdal:docs", lambda s: re.search(r"\.rst|doc|typo|tut|libkea", s, re.I)),
    ("gdal:drivers-warp", lambda s: True),
]
AREA_NAMES = {
    "gdal:vrt": "vrt:// connection",
    "gdal:mdim": "Multidim and Zarr",
    "gdal:drivers-warp": "Drivers, warp, utilities",
    "gdal:docs": "Docs",
}


def area_of(subject):
    for label, test in AREAS:
        if test(subject):
            return label


def gdal_rows():
    rows = []
    for line in open("data/gdal_authored.psv"):
        h, d, pr, s = line.rstrip("\n").split("|", 3)
        if h in SKIP:
            continue
        pr = PR_OVERRIDES.get(h, pr)
        rows.append((d, h, pr, area_of(s), s.encode("ascii", "replace").decode()))
    return rows


def svg(rows, path):
    counts = collections.defaultdict(collections.Counter)
    for d, _, _, a, _ in rows:
        counts[int(d[:4])][a] += 1
    years = list(range(min(counts), max(counts) + 1))
    order = ["gdal:vrt", "gdal:mdim", "gdal:drivers-warp", "gdal:docs"]
    W, H, L, B, T = 640, 300, 40, 40, 56
    bw = (W - L - 16) / len(years)
    ymax = max(sum(c.values()) for c in counts.values())
    sc = (H - B - T) / ymax
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
           'font-family="system-ui,sans-serif" font-size="11">',
           "<style>.bg{fill:#fcfcfb}.t1{fill:#0b0b0b}.t2{fill:#52514e}"
           ".g{stroke:#e4e3df}.s1{fill:#2a78d6}.s2{fill:#eb6834}.s3{fill:#1baf7a}"
           ".s4{fill:#eda100}.gap{stroke:#fcfcfb}"
           "@media (prefers-color-scheme: dark){.bg{fill:#1a1a19}.t1{fill:#f0efec}"
           ".t2{fill:#c3c2b7}.g{stroke:#3a3a37}.s1{fill:#3987e5}.s2{fill:#d95926}"
           ".s3{fill:#199e70}.s4{fill:#c98500}.gap{stroke:#1a1a19}}</style>",
           f'<rect class="bg" width="{W}" height="{H}"/>',
           f'<text class="t1" x="{L}" y="20" font-size="14" font-weight="600">'
           "Commits merged into GDAL, by year and area</text>"]
    lx = L
    for i, a in enumerate(order):
        out.append(f'<rect class="s{i+1}" x="{lx}" y="32" width="10" height="10" rx="2"/>'
                   f'<text class="t2" x="{lx+14}" y="41">{AREA_NAMES[a]}</text>')
        lx += 22 + 6.2 * len(AREA_NAMES[a])
    for v in range(0, ymax + 1, 5):
        y = H - B - v * sc
        out.append(f'<line class="g" x1="{L}" x2="{W-16}" y1="{y:.1f}" y2="{y:.1f}"/>'
                   f'<text class="t2" x="{L-6}" y="{y+4:.1f}" text-anchor="end">{v}</text>')
    for j, yr in enumerate(years):
        x = L + j * bw + bw * 0.2
        y = H - B
        for i, a in enumerate(order):
            n = counts[yr][a]
            if n:
                h = n * sc
                out.append(f'<rect class="s{i+1} gap" stroke-width="2" x="{x:.1f}" '
                           f'y="{y-h:.1f}" width="{bw*0.6:.1f}" height="{h:.1f}">'
                           f"<title>{yr} {AREA_NAMES[a]}: {n}</title></rect>")
                y -= h
        tot = sum(counts[yr].values())
        if tot:
            out.append(f'<text class="t1" x="{x+bw*0.3:.1f}" y="{y-4:.1f}" '
                       f'text-anchor="middle">{tot}</text>')
        out.append(f'<text class="t2" x="{x+bw*0.3:.1f}" y="{H-B+16}" '
                   f'text-anchor="middle">{yr}</text>')
    out.append("</svg>")
    open(path, "w").write("\n".join(out) + "\n")


def main():
    rows = gdal_rows()
    svg(rows, "figures/gdal-commits-by-year.svg")
    by_area = collections.defaultdict(list)
    for r in rows:
        by_area[r[3]].append(r)
    lines = []
    for a in ["gdal:vrt", "gdal:mdim", "gdal:drivers-warp", "gdal:docs"]:
        lines.append(f"### {AREA_NAMES[a]} ({len(by_area[a])})\n")
        lines.append("| Date | PR | Commit | Change |")
        lines.append("|---|---|---|---|")
        for d, h, pr, _, s in by_area[a]:
            prl = f"[#{pr}](https://github.com/OSGeo/gdal/pull/{pr})" if pr else "-"
            s = s.replace("|", "/")
            lines.append(f"| {d} | {prl} | [{h}](https://github.com/OSGeo/gdal/commit/{h}) | {s} |")
        lines.append("")
    open("data/gdal_contributions.md", "w").write("\n".join(lines))
    print(len(rows), {a: len(v) for a, v in by_area.items()})


if __name__ == "__main__":
    main()
