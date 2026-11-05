"""Write wishes.json: the open tracker issues as search queries for issuescope.

issuescope (mdsumner/issue-triage) loads this file into its "From my
tracker" picker and runs each wish's search text against the upstream
tracker, to find existing issues and PRs before anything is filed.

Search text, first that is present:
  1. the intake form's "Search words" answer;
  2. a line "search: ..." anywhere in the issue body;
  3. the issue title.
Tracker wording ("C1-C3", "get-refs") rarely matches upstream wording, so
give the words an upstream reporter would use, synonyms included.

    python3 scripts/wishes.py > wishes.json
    python3 scripts/wishes.py --json issues.json > wishes.json

Standard library only; shares the API fetch and parsing with rundown.py.
"""
import argparse
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rundown import REPO, describe, fetch, section  # noqa: E402

SEARCH_LINE = re.compile(r"^\s*search:\s*(.+?)\s*$", re.I | re.M)


def search_text(issue):
    body = issue.get("body") or ""
    words = section(body, "Search words")
    if words:
        return " ".join(words.split()), "form"
    m = SEARCH_LINE.search(body)
    if m:
        return m.group(1), "line"
    return issue["title"], "title"


def wish(issue):
    d = describe(issue)
    text, source = search_text(issue)
    return {
        "number": d["n"], "title": issue["title"], "url": d["url"],
        "priority": d["p"], "status": d["status"], "area": d["area"],
        "upstream": section(issue.get("body") or "", "Upstream link") or None,
        "search": text, "search_source": source,
    }


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
    wishes = [wish(i) for i in issues if "pull_request" not in i]
    wishes = [w for w in wishes if w["status"] != "done"]
    order = {"P1": 0, "P2": 1, "P3": 2, None: 3}
    wishes.sort(key=lambda w: (order[w["priority"]], w["number"]))
    out = {"repo": args.repo,
           "generated": datetime.date.today().isoformat(),
           "wishes": wishes}
    json.dump(out, sys.stdout, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
