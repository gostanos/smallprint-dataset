#!/usr/bin/env python3
"""Small Print record dataset: write a release from an export stream, and check a release against the live statistics.

  python3 dataset.py build --raw <export stream> --out <dataset folder> [--release YYYY-MM-DD] [--force]
  python3 dataset.py check <release folder> [--stats-url https://smallprint.dev/api/stats]
  python3 dataset.py counts <release folder>

`build` is called by export.sh. `check` needs only the release files and the network: it counts every figure from the
CSV files themselves and prints each one beside the figure https://smallprint.dev/api/stats serves. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import sys
import urllib.parse
import urllib.request
from collections import Counter, defaultdict

TITLE = "Small Print record of MCP server, skill and plugin small print"
GZIPPED = {"entries", "versions", "changes"}
ORDER = ["entries", "versions", "changes", "changes_by_day", "advisories", "advisory_matches", "record_chain"]
GENESIS = "0" * 64


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def page_url(entry: str) -> str:
    """The entry's page on smallprint.dev, built the way the site builds it (apps/web/src/lib/data.ts pathFromCanonicalName)."""
    i = entry.index(":")
    parts = entry[i + 1 :].split("/")
    if len(parts) > 1 and parts[0].lower() in ("http:", "https:") and parts[1] == "":
        parts.pop(1)
    return "https://smallprint.dev/a/" + entry[:i] + "/" + "/".join(urllib.parse.quote(p, safe="!'()*-._~") for p in parts)


def parse_stream(path: str) -> dict[str, list[list[str]]]:
    sections: dict[str, list[list[str]]] = {}
    current: str | None = None
    ended = False
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) == 1 and row[0].startswith("@@FILE "):
                current = row[0][len("@@FILE ") :].strip()
                sections[current] = []
                continue
            if len(row) == 1 and row[0] == "@@END":
                ended = True
                continue
            if current is None or not row:
                continue
            sections[current].append(row)
    if not ended:
        sys.exit("build: the export stream has no @@END line; it is incomplete")
    missing = [n for n in ["meta", "entries", "versions", "changes", "advisories", "advisory_matches", "record_chain"] if n not in sections]
    if missing:
        sys.exit(f"build: the export stream lacks {', '.join(missing)}")
    return sections


def write_csv(path: str, header: list[str], rows: list[list[str]], gz: bool) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    data = buf.getvalue().encode("utf-8")
    if gz:
        out = io.BytesIO()
        # no name and a zero timestamp, so the same rows always give the same bytes and the same sha256
        with gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0, compresslevel=9) as g:
            g.write(data)
        data = out.getvalue()
    with open(path, "wb") as f:
        f.write(data)
    return data


def check_chain(header: list[str], rows: list[list[str]]) -> dict:
    ix = {c: i for i, c in enumerate(header)}
    prev = GENESIS
    for r in rows:
        day, through, eh, ph, ch = r[ix["day"]], r[ix["through_at"]], r[ix["entries_hash"]], r[ix["prev_hash"]], r[ix["chain_hash"]]
        if ph != prev:
            sys.exit(f"build: record chain row {day} does not point at the previous row")
        if sha256_hex(f"{ph}\n{day}\n{through}\n{eh}".encode()) != ch:
            sys.exit(f"build: record chain row {day} does not recompute")
        prev = ch
    return {"rows": len(rows), "links_and_hashes_recomputed": True}


# ---------------------------------------------------------------------------------------------------------------
# Reading a release back, and counting the figures that /api/stats also serves
# ---------------------------------------------------------------------------------------------------------------


def read_release(folder: str, name: str) -> list[dict[str, str]]:
    gz = os.path.join(folder, name + ".csv.gz")
    plain = os.path.join(folder, name + ".csv")
    if os.path.exists(gz):
        f = io.TextIOWrapper(gzip.open(gz, "rb"), encoding="utf-8", newline="")
    else:
        f = open(plain, encoding="utf-8", newline="")
    with f:
        return list(csv.DictReader(f))


def counts(folder: str) -> dict:
    entries = read_release(folder, "entries")
    versions = read_release(folder, "versions")
    changes = read_release(folder, "changes")
    advisories = read_release(folder, "advisories")
    matches = read_release(folder, "advisory_matches")
    chain = read_release(folder, "record_chain")

    kind = Counter(e["kind"] for e in entries)
    registry_of = {e["entry"]: e["source_registry"] for e in entries}
    kind_of = {e["entry"]: e["kind"] for e in entries}
    latest_of = {e["entry"]: e["latest_version"] for e in entries}
    read = {v["entry"] for v in versions if v["content_hash"] or v["tree_hash"]}
    listed_by = Counter(e["source_registry"] for e in entries)
    read_by = Counter(registry_of[x] for x in read)

    # tools on the latest read version of each server
    tool_counts = []
    no_tools = 0
    for v in versions:
        if kind_of.get(v["entry"]) != "mcp" or v["version"] != latest_of.get(v["entry"]) or v["tool_count"] == "":
            continue
        n = int(v["tool_count"])
        if v["content_hash"] and n > 0:
            tool_counts.append(n)
        if not v["content_hash"] and n == 0:
            no_tools += 1
    tool_counts.sort()

    languages: Counter = Counter()
    for v in versions:
        m = v["read_method"]
        if v["content_hash"] and m and not m.startswith("unread:"):
            for lang in m.split(","):
                languages[lang] += 1

    # the live figure counts what the text says: not a version bump, and not a source that stopped listing an entry
    # (decision 326, 29 Sep 2026); both stay in changes.csv, where the field column tells them apart
    real = [c for c in changes if c["field"] not in ("version.bump", "source.presence")]
    field = Counter(c["field"] for c in changes)
    high = [c for c in changes if c["severity"] == "high"]
    return {
        "entries": len(entries),
        "servers": kind["mcp"],
        # the live figure "skills" counts kind agent-skill; its line gives the plugins beside it
        "skills": kind["agent-skill"],
        "plugins": kind["agent-plugin"],
        "read": len(read),
        "versions": len(versions),
        "versions_hashed": sum(1 for v in versions if v["content_hash"]),
        "tools-total": sum(tool_counts),
        "servers-with-tools": len(tool_counts),
        "tools-median": tool_counts[len(tool_counts) // 2] if tool_counts else 0,
        "tools-big": sum(1 for x in tool_counts if x >= 50),
        "tools-none": no_tools,
        "changes_all_rows": len(changes),
        "drift-total": len(real),
        "drift-assets": len({c["entry"] for c in real}),
        "drift-releases": len({(c["entry"], c["to_version"]) for c in real}),
        "desc-changes": field["tool.description"],
        "tools-added": field["tool.added"],
        "tools-removed": field["tool.removed"],
        "schema-changes": field["tool.schema"],
        "instr-changes": field["skill.instructions"],
        "presence-changes": field["source.presence"],
        "bumps": field["version.bump"],
        "bumps-same": sum(1 for c in changes if c["rule"] == "drift.version.bump.same-hash"),
        "high-exfil": sum(1 for c in high if c["rule"].endswith(".exfiltration")),
        "high-override": sum(1 for c in high if c["rule"].endswith(".override")),
        "high-all": len(high),
        "critical-all": sum(1 for c in changes if c["severity"] == "critical"),
        "adv-total": len(advisories),
        "adv-linked": len({m["advisory_id"] for m in matches}),
        "adv-critical": sum(1 for a in advisories if a["severity"] == "critical"),
        "adv-high": sum(1 for a in advisories if a["severity"] == "high"),
        "adv-malware": sum(1 for a in advisories if a["rule"] == "advisory.malware-id"),
        "adv-assets": len({m["entry"] for m in matches}),
        "chain-days": len(chain),
        "sources": {r: {"listed": listed_by[r], "read": read_by[r]} for r in sorted(listed_by, key=lambda r: -listed_by[r])},
        "languages": dict(languages.most_common()),
    }


# ---------------------------------------------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------------------------------------------


def build(args: argparse.Namespace) -> None:
    s = parse_stream(args.raw)
    exported_at = s["meta"][1][0]
    release = args.release or exported_at[:10]
    folder = os.path.join(args.out, release)
    if os.path.exists(folder) and not args.force:
        sys.exit(f"build: {folder} exists; pass --force to write over it")
    os.makedirs(folder, exist_ok=True)

    tables: dict[str, tuple[list[str], list[list[str]]]] = {}
    for name in ["entries", "versions", "changes", "advisories", "advisory_matches", "record_chain"]:
        header, *rows = s[name]
        tables[name] = (header, rows)

    # entries: add the page address, built as the site builds it
    h, rows = tables["entries"]
    at = h.index("entry") + 1
    tables["entries"] = (h[:at] + ["page_url"] + h[at:], [r[:at] + [page_url(r[0])] + r[at:] for r in rows])

    # changes_by_day: counted from the changes rows, by UTC detection day, field and grade
    h, rows = tables["changes"]
    ix = {c: i for i, c in enumerate(h)}
    per: dict[tuple[str, str, str], list] = defaultdict(lambda: [0, set()])
    for r in rows:
        k = (r[ix["detected_at"]][:10], r[ix["field"]], r[ix["severity"]])
        per[k][0] += 1
        per[k][1].add(r[ix["entry"]])
    tables["changes_by_day"] = (["day", "field", "severity", "changes", "entries"], [[d, f, sev, str(n), str(len(e))] for (d, f, sev), (n, e) in sorted(per.items())])

    chain_check = check_chain(*tables["record_chain"])

    files = []
    for name in ORDER:
        header, rows = tables[name]
        gz = name in GZIPPED
        fname = name + (".csv.gz" if gz else ".csv")
        data = write_csv(os.path.join(folder, fname), header, rows, gz)
        files.append({"file": fname, "rows": len(rows), "bytes": len(data), "sha256": sha256_hex(data), "columns": header})

    ch, crow = tables["record_chain"]
    head = dict(zip(ch, crow[-1])) if crow else None
    c = counts(folder)
    manifest = {
        "title": TITLE,
        "release": release,
        "version": release.replace("-", "."),
        "exported_at_utc": exported_at,
        "publisher": "EmberStack LLC, Small Print",
        "url": "https://smallprint.dev",
        "licence": "CC-BY-4.0",
        "licence_url": "https://creativecommons.org/licenses/by/4.0/",
        "snapshot": "Every file was read inside one read-only transaction of the record database, at exported_at_utc.",
        "chain_head": head,
        "chain_head_note": (
            "The newest record chain row at export time (decision 138). Versions whose content hash was recorded after its "
            "through_at are in versions.csv.gz but are covered by the next night's row. Every row's link and hash were recomputed "
            "from the row's own fields when this release was built; the lines behind a row are at https://smallprint.dev/api/chain/<day>."
        ),
        "chain_check": chain_check,
        "files": files,
        "counts": c,
    }
    with open(os.path.join(folder, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print(f"release {release} written to {folder}")
    for x in files:
        print(f"  {x['file']:<24} {x['rows']:>8} rows {x['bytes']:>11} bytes  {x['sha256']}")
    if head:
        print(f"  chain head {head['day']} {head['chain_hash']} (through {head['through_at']})")


# ---------------------------------------------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------------------------------------------


def check(args: argparse.Namespace) -> None:
    ours = counts(args.folder)
    req = urllib.request.Request(args.stats_url, headers={"user-agent": "smallprint-dataset-check (+https://smallprint.dev)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        live = json.load(r)
    stat = {st["id"]: st["value"] for sec in live["sections"] for st in sec["stats"]}
    manifest_path = os.path.join(args.folder, "manifest.json")
    exported = json.load(open(manifest_path)).get("exported_at_utc") if os.path.exists(manifest_path) else "?"
    print(f"release files exported {exported}; live statistics asOf {live.get('asOf')}")
    print(f"{'figure':<16} {'release':>10} {'live':>10} {'difference':>11}")
    same = 0
    ids = ["entries", "servers", "skills", "read", "versions", "tools-total", "tools-median", "tools-big", "tools-none",
           "drift-total", "drift-assets", "drift-releases", "desc-changes", "tools-added", "instr-changes", "bumps-same",
           "high-exfil", "high-override", "adv-total", "adv-linked", "adv-critical", "adv-malware", "adv-assets", "chain-days"]
    ids += [f"lang-{k}" for k in ours["languages"] if f"lang-{k}" in stat]
    for k in ids:
        mine = ours["languages"][k[5:]] if k.startswith("lang-") else ours[k]
        theirs = stat.get(k)
        if theirs is None:
            print(f"{k:<16} {mine:>10} {'(none)':>10}")
            continue
        diff = mine - theirs
        same += diff == 0
        print(f"{k:<16} {mine:>10} {theirs:>10} {diff:>+11}")
    live_src = {x["registry"]: x for x in live.get("sources", [])}
    for reg, v in ours["sources"].items():
        l = live_src.get(reg, {})
        print(f"{'src ' + reg:<16} {v['listed']:>5}/{v['read']:<5}{l.get('listed', '-'):>6}/{l.get('read', '-'):<5}")
    print(f"{same} of {len(ids)} figures equal. A difference usually means the statistics were built at a different hour; see the README.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--raw", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--release")
    b.add_argument("--force", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("folder")
    c.add_argument("--stats-url", default="https://smallprint.dev/api/stats")
    n = sub.add_parser("counts")
    n.add_argument("folder")
    a = p.parse_args()
    if a.cmd == "build":
        build(a)
    elif a.cmd == "check":
        check(a)
    else:
        print(json.dumps(counts(a.folder), indent=2))


if __name__ == "__main__":
    main()
