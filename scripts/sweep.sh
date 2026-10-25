#!/usr/bin/env bash
# Status sweep: Michael Sumner's GDAL contributions and fork branches.
# Read-only. Needs git >= 2.27. Output goes to data/.
# Usage: scripts/sweep.sh [workdir]
set -euo pipefail
OUT="$(cd "$(dirname "$0")/.." && pwd)/data"
WORK="${1:-$(mktemp -d)}"
AUTHOR="Sumner"
mkdir -p "$OUT"
cd "$WORK"

[ -d gdal.git ] || git clone -q --bare --filter=tree:0 --single-branch \
  --branch master https://github.com/OSGeo/gdal gdal.git
cd gdal.git
git fetch -q origin master:master
git fetch -q --filter=tree:0 https://github.com/mdsumner/gdal '+refs/heads/*:refs/fork/*'
git fetch -q --filter=tree:0 https://github.com/OSGeo/gdal '+refs/pull/*/head:refs/pr/*'

# 1. Commits authored upstream (merged contributions)
# Columns: hash|date|PR|subject. PR comes from "(#N)" in the subject, else from
# the first later "Merge pull request #N from mdsumner/..." on the ancestry
# path (a heuristic; scripts/contributions.py holds corrections).
git log --author="$AUTHOR" --format='%h|%cs|%s' master | while IFS='|' read -r h d s; do
  pr=$(echo "$s" | grep -oE '\(#[0-9]+\)' | head -1 | tr -d '(#)' || true)
  if [ -z "$pr" ]; then
    pr=$(git log --merges --ancestry-path --reverse --format='%s' "$h..master" \
      | grep -m1 -oE 'Merge pull request #[0-9]+ from mdsumner' | grep -oE '[0-9]+' || true)
  fi
  echo "$h|$d|$pr|$s"
done > "$OUT/gdal_authored.psv"

# 2. Upstream PRs carrying own commits, and whether they landed on master
git log --author="$AUTHOR" --format='%H' --glob='refs/pr/*' --not master \
  | xargs git name-rev --refs='refs/pr/*' --name-only \
  | sed -E 's#pr/##; s/[~^].*//' | sort -un > "$WORK/prs.txt"
: > "$OUT/gdal_prs.psv"
while read -r n; do
  sq=$(git log master --format='%h' --grep="(#$n)" | head -1)
  mg=$(git log master --format='%h' --grep="Merge pull request #$n " | head -1)
  st=unmerged; [ -n "$sq$mg" ] && st="merged $sq$mg"
  echo "$n|$st|$(git log -1 --format='%cs|%s' "refs/pr/$n")" >> "$OUT/gdal_prs.psv"
done < "$WORK/prs.txt"

# 3. Fork branches: commits ahead of master, own commits, matching PR head
git for-each-ref refs/pr --format='%(objectname) %(refname:short)' > "$WORK/prheads.txt"
: > "$OUT/gdal_fork_branches.psv"
for ref in $(git for-each-ref refs/fork --format='%(refname)'); do
  b=${ref#refs/fork/}; sha=$(git rev-parse "$ref")
  ahead=$(git rev-list --count "master..$ref")
  own=$(git rev-list --count --author="$AUTHOR" "master..$ref")
  pr=$(awk -v s="$sha" '$1==s{sub("pr/","",$2); print $2}' "$WORK/prheads.txt" | paste -sd, -)
  echo "$b|$(git log -1 --format='%cs|%an' "$ref")|$ahead|$own|$pr" >> "$OUT/gdal_fork_branches.psv"
done
echo "done: $OUT"
