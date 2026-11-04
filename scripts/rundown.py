"""Render RUNDOWN.md: a ranked list of open tracker issues to work through.

Reads open issues from the GitHub API (or a saved JSON file) and sorts them
by priority label, then status, then whether they block downstream work.
Issues without a P label land in the Inbox, with a suggested priority taken
from the intake form's "Impact" answer.

    python3 scripts/rundown.py > RUNDOWN.md
    python3 scripts/rundown.py --json issues.json > RUNDOWN.md

GITHUB_TOKEN is optional (the tracker is public); GITHUB_REPOSITORY defaults
to mdsumner/osgeo-upstream. Standard library only.
"""
import argparse
import datetime
import json
import os
import re
import urllib.request

REPO = os.environ.get("GITHUB_REPOSITORY", "mdsumner/osgeo-upstream")

PRIORITY = ["P1", "P2", "P3"]
PRIORITY_NAMES = {"P1": "Now (P1)", "P2": "Next (P2)", "P3": "Later (P3)"}
# Order inside a priority: what I can act on now comes first.
STATUS = ["ready", "upstream", "investigating", "idea", "parked"]
STATUS_NOTE = {
    "ready": "repro and fix described; write the patch",
    "upstream": "open upstream; check for review",
    "investigating": "confirm on master, write the repro",
    "idea": "needs a look",
    "parked": "waiting on something",
}
# Intake form "Impact" answer -> suggested priority for the Inbox.
IMPACT_TO_P = {"blocks": "P1", "workaround": "P2", "nice": "P3"}


def fetch(repo):
    issues, page = [], 1
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "osgeo-upstream-rundown"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    while True:
        url = ("https://api.github.com/repos/%s/issues?state=open"
               "&per_page=100&page=%d" % (repo, page))
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
            batch = json.load(r)
        issues += batch
        if len(batch) < 100:
            return issues
        page += 1


def section(body, heading):
    """Text under a '### heading' of an issue form, or ''."""
    m = re.search(r"^###\s+%s\s*$(.*?)(?=^###\s|\Z)" % re.escape(heading),
                  body or "", re.M | re.S | re.I)
    if not m:
        return ""
    text = m.group(1).strip()
    return "" if text == "_No response_" else text


def one_line(text, n=60):
    text = " ".join(text.split()).replace("|", "/")
    return text if len(text) <= n else text[: n - 3] + "..."


def describe(issue):
    labels = {l["name"] for l in issue["labels"]}
    pri = next((p for p in PRIORITY if p in labels), None)
    status = next((s for s in STATUS + ["done"] if "status:" + s in labels), "idea")
    areas = sorted(l for l in labels if l.startswith("gdal:") or l in ("proj", "geos"))
    body = issue.get("body") or ""
    found = one_line(section(body, "Found in"), 30)
    if not found and "wxylib" in labels:
        found = "wxylib"
    impact = section(body, "Impact").lower()
    blocks = impact.startswith("blocks") or "blocks" in labels
    project = section(body, "Project")
    if not areas and project:
        areas = [project.lower()]
    return {
        "n": issue["number"], "title": one_line(issue["title"], 70),
        "url": issue["html_url"], "p": pri, "status": status,
        "area": ", ".join(areas) or "-", "found": found or "-",
        "blocks": blocks, "impact": impact,
        "updated": issue["updated_at"][:10],
    }


def sort_key(d):
    return (STATUS.index(d["status"]) if d["status"] in STATUS else 99,
            not d["blocks"], d["n"])


def table(rows, today):
    out = ["| # | Item | Area | Status | Found in | Idle |",
           "|---|---|---|---|---|---|"]
    for d in rows:
        idle = (today - datetime.date.fromisoformat(d["updated"])).days
        title = d["title"] + (" **(blocks downstream)**" if d["blocks"] else "")
        out.append("| [#%d](%s) | %s | %s | %s | %s | %dd |" % (
            d["n"], d["url"], title, d["area"], d["status"], d["found"], idle))
    return out


def render(issues, today):
    items = [describe(i) for i in issues if "pull_request" not in i]
    items = [d for d in items if d["status"] != "done"]
    inbox = sorted((d for d in items if d["p"] is None), key=lambda d: d["n"])
    lines = [
        "# Rundown",
        "",
        "Generated %s by `scripts/rundown.py` from the open issues; do not edit."
        % today.isoformat(),
        "Ranked by priority label, then status (ready, upstream, investigating,",
        "idea, parked), then items that block downstream work.",
        "New gap found downstream? Open an issue with the",
        "[upstream gap form](../../issues/new?template=upstream-gap.yml).",
        "Order and reasons: [PRIORITIES.md](PRIORITIES.md);",
        "items without an issue yet: [PLANS.md](PLANS.md).",
        "",
    ]
    if inbox:
        lines += ["## Inbox: needs a priority label", ""]
        lines += ["| # | Item | Found in | Suggested |", "|---|---|---|---|"]
        for d in inbox:
            sug = next((p for k, p in IMPACT_TO_P.items() if d["impact"].startswith(k)), "?")
            lines.append("| [#%d](%s) | %s | %s | %s |" % (
                d["n"], d["url"], d["title"], d["found"], sug))
        lines.append("")
    for p in PRIORITY:
        rows = sorted((d for d in items if d["p"] == p), key=sort_key)
        if not rows:
            continue
        lines += ["## %s" % PRIORITY_NAMES[p], ""]
        if p == "P3":
            lines += ["<details><summary>%d items</summary>" % len(rows), ""]
        lines += table(rows, today)
        if p == "P3":
            lines += ["", "</details>"]
        lines.append("")
    waiting = [d for d in items if d["status"] == "upstream"]
    if waiting:
        lines += ["## Waiting on upstream", ""]
        lines += ["- [#%d](%s) %s" % (d["n"], d["url"], d["title"]) for d in waiting]
        lines.append("")
    counts = {}
    for d in items:
        key = d["area"].split(", ")[0].replace("-", "(none)")
        counts.setdefault(key, [0, 0, 0, 0])
        counts[key][PRIORITY.index(d["p"]) if d["p"] else 3] += 1
    lines += ["## Open items by area", "",
              "| Area | P1 | P2 | P3 | Inbox |", "|---|---|---|---|---|"]
    for key in sorted(counts):
        lines.append("| %s | %s |" % (key, " | ".join(str(c) for c in counts[key])))
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", help="read issues from this file, not the API")
    ap.add_argument("--repo", default=REPO)
    args = ap.parse_args()
    if args.json:
        with open(args.json) as f:
            issues = json.load(f)
    else:
        issues = fetch(args.repo)
    print(render(issues, datetime.date.today()), end="")


if __name__ == "__main__":
    main()
