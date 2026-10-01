# Small Print record of MCP server, skill and plugin small print

Small Print (https://smallprint.dev) reads the text that MCP servers, agent skills and plugins publish about themselves, in a nightly run. That text is the tool names, tool descriptions, input schemas and instruction files that an AI agent reads before it uses the software, which Small Print calls "the small print". Small Print stores a fingerprint (a sha256 hash) of every version it reads, compares each version with the one before it, grades each change by a printed rule, and matches public security advisories to the versions they name.

This dataset is the metadata of that record. It lists every entry, every version with its fingerprint and tool count, every recorded change with its grade and the rule that set it, per-day change counts, the advisories matched to entries with their version ranges, and the nightly hash chain that lets anyone check that recorded fingerprints were not changed later. It holds no third-party text: no tool descriptions, schemas, instruction files, READMEs, advisory summaries or diffs. To read what a change actually said, follow the entry's `page_url` to its page on smallprint.dev.

- Release: 2026-09-30 (version 2026.09.30). The earlier release, 2026-09-29, stays in its own folder; see "What changed since 2026-09-29" below.
- Exported: 2026-09-30 at 23:19:48 UTC, from the live record, inside one read-only transaction, so every file describes the same moment.
- Publisher: EmberStack LLC, Small Print. Licence: CC BY 4.0 (see "Licence" below).

## What changed since 2026-09-29

The release of 2026-09-29 was exported before two faults in the record were fixed (on 29 and 30 September 2026). Use this release instead.

- About 1,415 ordinary malicious npm and PyPI packages had been made into entries because a public malware feed named them, although nothing showed them to be MCP servers, skills or plugins. They are hidden from the record now, so they and the advisories that only name them are not in this release.
- When a release was read after a later one, it had sometimes been compared with an older version as well as with the one just before it, so one change was recorded more than once. 12,301 such extra comparisons were deleted, and each version is now compared only with the version before it.
- Changes in whether a registry still lists an entry (field `source.presence`) stay in `changes.csv.gz`, but they are no longer counted as changes to the small print, which matches the live site.

## Files in this release

Every file is UTF-8 CSV with a header row. The three large files are gzip-compressed. An empty field means the value is not on record. `2026-09-30/manifest.json` gives each file's row count, size in bytes, sha256 and columns, the export time, the record chain's newest row, and the counts described in "Checking the counts".

| File | Rows | Size | One row is |
|---|---:|---:|---|
| `entries.csv.gz` | 93,634 | 3.8 MB | one entry: one MCP server, skill or plugin, identified once however many places list it |
| `versions.csv.gz` | 188,088 | 9.1 MB | one version of one entry |
| `changes.csv.gz` | 140,874 | 4.8 MB | one recorded change between two versions of an entry, or one change in whether its source still serves it |
| `changes_by_day.csv` | 266 | 10 KB | the number of changes found on one day, for one field and one grade |
| `advisories.csv` | 1,625 | 185 KB | one public security advisory, by identifier |
| `advisory_matches.csv` | 2,155 | 168 KB | one advisory matched to one entry, with the version range it names |
| `record_chain.csv` | 14 | 5 KB | one night's row of the record chain |

Of the 93,634 entries, 61,895 are MCP servers, 26,950 are agent skills and 4,789 are plugins, listed from 12 public sources. 84,359 entries have at least one version that Small Print has read. Of the 118,421 changes, 94,176 are changes to the small print itself and 24,245 are plain version bumps.

## What each column means

### entries.csv.gz

| Column | Meaning |
|---|---|
| `entry` | The entry's identity in the record, written `registry:name`, for example `npm:@modelcontextprotocol/server-filesystem`. The part before the colon is the package registry or catalog the name belongs to (npm, pypi, oci, nuget, mcpb, mcp-registry, skills.sh, clawhub, smithery, huggingface, claude-plugins, gemini, docker, zed, github). Every other file joins on this column. |
| `page_url` | The entry's page on smallprint.dev, with every version on record, every change shown in full with its grade and rule, and the advisories that name it. |
| `kind` | `mcp` for an MCP server, `agent-skill` for a skill, `agent-plugin` for a plugin or extension. |
| `source_registry` | The public source Small Print listed the entry from: `mcp-registry` (the official MCP registry), `npm`, `pypi`, `skills.sh`, `clawhub`, `smithery`, `huggingface` (Hugging Face Spaces), `anthropic-plugins` (Anthropic's Claude Code plugin marketplaces), `gemini` (Gemini CLI extensions), `docker` (Docker MCP Registry), `zed` (Zed context servers) or `github`. |
| `source_url` | The address Small Print read the listing from. |
| `repo_url` | The source code repository, as the source gives it. Small Print does not check that the address is right. |
| `repo_subfolder` | The folder inside the repository that holds this entry, when the source says so. |
| `latest_version` | The newest version string on record. For sources without version numbers (Hugging Face Spaces, skills, plugins) this is a short commit or content identifier. |
| `first_seen` | The earliest date on record for the entry. For some sources this is the source's own creation date; otherwise it is the day Small Print first listed the entry. |
| `last_seen` | The last time a nightly listing saw the entry. |
| `first_published_at` | When the registry says the first version was published, where it says so (2,308 entries). |
| `install_count` | A popularity count reported by the source (27,802 entries). The number measures different things on different sources, so read it with the next column and do not compare it across sources. |
| `install_count_source` | What `install_count` counts: `npm weekly downloads`, `clawhub installs`, `skills.sh installs`, `smithery uses`, `huggingface likes`, `github stars` (Gemini CLI extensions) or `zed downloads`. |
| `gone_at` | When the source stopped serving the entry, if it has (808 entries). Cleared if the source serves it again. |
| `gone_reason` | The source's answer at that time, in a few words, for example `not on npm (unpublished)` or `gated on Hugging Face (HTTP 401)`. |

### versions.csv.gz

| Column | Meaning |
|---|---|
| `entry` | The entry, as in entries.csv.gz. |
| `version` | The version string as the source gives it. |
| `published_at` | When the source says this version was published, where it says so. |
| `recorded_at` | When Small Print first recorded this version. |
| `content_hash` | The fingerprint of the version's small print: sha256, in hex, of its canonical form. For an MCP server the canonical form is the list of tools (name, description and input schema), sorted by tool name, with object keys sorted and runs of whitespace in prose collapsed. For a skill it is the instruction file with line endings and trailing spaces normalised, followed by a sorted list of every other file's path and sha256. Empty when the version has not been read. Two versions with the same `content_hash` published the same small print. |
| `tree_hash` | A fingerprint of the whole published package: sha256 over the sorted list of every file's path and sha256. It changes when any file changes, not only the small print. |
| `tree_file_count` | How many files the package held when `tree_hash` was taken. |
| `tool_count` | How many tools the version's tool list holds. Empty when no tool list is on record, which is normal for skills. |
| `has_instructions` | 1 when an instruction file (such as SKILL.md) is on record for the version, otherwise 0. |
| `read_method` | How the tools were read: the languages whose source code gave the tool definitions (`js`, `ts`, `python`, `go`, `rust`, `csharp`, `java`, comma-joined), `remote` (asked a running remote server for its tool list), `smithery-api` (Smithery's published tool list), or `unread:gone` and `unread:oversize` when the version could not be read. No code is run to read the tools, and the Go and Rust readers can give partial parameter detail. Empty for skills, plugins and versions not read for tools. |
| `version_source` | Which listing the version record came from. |

### changes.csv.gz

| Column | Meaning |
|---|---|
| `change_id` | A stable identifier for the change in the record. |
| `entry` | The entry, as in entries.csv.gz. |
| `from_version`, `to_version` | The two versions compared. Both are empty for `source.presence` rows. |
| `field` | What changed: `tool.added`, `tool.removed`, `tool.description`, `tool.schema` (a tool's input schema), `skill.instructions` (a skill's instruction file or another file in it), `version.bump` (a new version, recorded whether or not its small print changed), or `source.presence` (the source stopped serving the entry, gated it, or served it again). |
| `subject` | The tool name or the file name the change applies to. For `source.presence` it is the source that was asked. Empty for version bumps. |
| `severity` | The grade: `info`, `low`, `medium`, `high` or `critical`. This release has no change graded critical. |
| `rule` | The printed rule that set the grade, for example `drift.tool.description.imperative`. Every rule is explained at https://smallprint.dev/how-we-grade. |
| `detected_at` | When Small Print found the change. This is not when the change was published: when Small Print first reads an entry it also reads earlier versions, so older changes are found on the day of that read. To date a change by its release, use `published_at` of `to_version` in versions.csv.gz. |

### changes_by_day.csv

`day` (the UTC date of `detected_at`), `field`, `severity`, `changes` (how many changes) and `entries` (how many different entries they came from). It is counted from changes.csv.gz and inherits the caution about `detected_at` above: the large days (19, 20, 22 and 28 September) are mostly earlier versions read for the first time, not a burst of new releases.

### advisories.csv

| Column | Meaning |
|---|---|
| `advisory_id` | The advisory's identifier: a GitHub Advisory Database id (GHSA-), a CVE id, an OSV id (such as MAL- or OSV-MCPS-), or an SP- id that Small Print assigned to a published incident report that had no other identifier. |
| `aliases` | Other identifiers for the same advisory, separated by spaces. |
| `source` | The feed Small Print read the advisory from: `ghsa` (GitHub Advisory Database), `osv` (OSV, osv.dev), `nvd` (the US National Vulnerability Database), `vulnerablemcp` (the Vulnerable MCP Project), `csa-mcps` (the Cloud Security Alliance MCP vulnerability database) or `incident-backfill` (incident reports gathered by Small Print, each attributed on its page to the report that published it). |
| `severity` | Small Print's grade under its printed advisory rules: the CVSS score band first, then the source's own label. |
| `rule` | The advisory rule that set the grade, for example `advisory.cvss>=7`. `advisory.malware-id` means the id or an alias is in the MAL- series; that label is the issuing database's own. |
| `published`, `modified`, `withdrawn` | The dates the source gives. |

Summaries, details, references and Small Print's own explanations are left out.

### advisory_matches.csv

| Column | Meaning |
|---|---|
| `advisory_id` | The advisory, as in advisories.csv. |
| `entry` | The entry it was matched to, by package name or repository. |
| `version_range` | The affected versions, as the advisory states them: a range such as `<0.1.16`, a list of versions, or `*` when it names every version. |
| `matched_at` | When Small Print made the match. |

1,471 of the 1,625 advisories are matched to at least one of 344 entries. Advisories whose only matches are packages hidden from the record (see "What changed since 2026-09-29") are left out, so this file holds fewer advisories than the 4,230 reports smallprint.dev counts on record. An advisory can be matched to the wrong entry, for example where two packages share a name; each match can be disputed from the entry's page.

### record_chain.csv

One row a night since 17 September 2026. https://github.com/gostanos/smallprint-action/blob/main/tools/verify-chain.mjs checks every link of the chain from the public API and recomputes the newest row's `entries_hash` and signature. An older row's `entries_hash` cannot be recomputed from the API yet, because the API rebuilds its lines from the current versions table, and a version read again since then now falls in a later window. Each row takes the versions whose `content_hash` was recorded since the previous row, writes them as sorted lines of `entry<TAB>version<TAB>content_hash`, hashes those lines (`entries_hash`), and hashes that together with the previous row's `chain_hash`: `chain_hash = sha256(prev_hash + "\n" + day + "\n" + through_at + "\n" + entries_hash)`. The first row starts from sixty-four zeros. `versions` is how many lines the row covers, `through_at` is its cut-off time, and `signature` is an Ed25519 signature over the `chain_hash` text, made with Small Print's key (empty on the two rows written without it).

## Checking the chain

The newest row at export time is the row for 2026-09-30:

- `chain_hash` 7bd12caf7de6f5a08770739455d4880f6833fd67d44f169b74b888a64664dd9e
- `through_at` 2026-09-30T11:17:08.211Z, covering 23,126 versions

Every row's link to the one before it and every `chain_hash` were recomputed from the rows' own fields when this release was built. The same rows are served at https://smallprint.dev/api/chain, and the lines behind any row at `https://smallprint.dev/api/chain/<day>`. The signature on the newest row was checked against the public key served at https://smallprint.dev/.well-known/smallprint-chain-key.pub:

```sh
curl -s https://smallprint.dev/.well-known/smallprint-chain-key.pub > chain.pub
printf %s 7bd12caf7de6f5a08770739455d4880f6833fd67d44f169b74b888a64664dd9e > msg.txt
# signature column of the 2026-09-30 row, base64-decoded into sig.bin
openssl pkeyutl -verify -pubin -inkey chain.pub -rawin -in msg.txt -sigfile sig.bin
```

What the chain shows, and only this: a fingerprint recorded on one night cannot be changed afterwards without changing every later row, so anyone who kept a row can detect an edit. It says nothing about what any version contains. Versions whose fingerprint was recorded after the newest row's `through_at` are in versions.csv.gz and will be covered by the next night's row.

## How the record is made

Every night Small Print lists the entries of the 12 sources above, reads new versions, and stores what they publish about themselves. For an npm or PyPI package it downloads the published package and extracts the tool definitions from the code without running it. For a remote server listed on the official MCP registry it asks the server for its tool list once, and calls no tool; a server that answers with a sign-in requirement is listed but not read. For a skill or plugin it reads the instruction files from the published repository.

Each version's small print is written in a canonical form and hashed (`content_hash`). When a version's hash differs from the previous version's, Small Print compares the two, tool by tool and file by file, and records one change per tool or file that differs. Each change is graded by fixed written rules, applied by code, that look for specific patterns in the new text, such as wording that names a secrets file or a network address beside a verb that moves data, or wording that tells the agent to hide something from the user. The rules are printed, with their patterns, at https://smallprint.dev/how-we-grade. Grades come only from these rules; a language model never sets one.

Advisories are read from the feeds named above and matched to entries by package name, then to versions by the ranges the advisory states. The sources and their endpoints are listed in Small Print's source documentation, and every advisory on the site is attributed to the database or report that published it.

## What this dataset does not cover

- **Published text only.** Small Print reads what a server, skill or plugin publishes about itself. It does not watch what the software does when it runs. A server can do something at run time that its description never mentions, and a change that only shows while the software runs is not in the record.
- **Not every entry is read.** 84,359 of 93,634 entries have a read version. Some packages cannot be downloaded, some remote servers need a sign-in or do not answer, some repositories have moved, and 15,005 servers were read but declare no tools in their code, which usually means they build the list while running.
- **A grade is a printed rule that matched, not a verdict.** A grade says which written rule matched the published words. It does not say that the software or its author did anything wrong.
- **False alarms exist, and most high grades have been false alarms.** On 28 September 2026 Small Print audited every change then graded high or critical: 335 changes on 214 entries. 36 of them already dropped below high under the rules as they stood that night. Of the 299 that stayed high, each was read one by one with Claude, the AI model Small Print is built with, and 23 were found that a reviewer would want a person to look at and 276 false alarms, which is 92 per cent. Most false alarms were ordinary documentation that names a key, a secret or a web address, or a warning such as "never send credentials". The rules have since been narrowed (on 29 September four more false-alarm patterns stopped being graded high), and this release has 250 changes graded high. Treat a high grade as a pointer to read the change on its page, not as a finding.
- **Change dates are detection dates.** See `detected_at` above. The record of changes begins on 3 September 2026.
- **Popularity counts are the sources' own and are not comparable.** Downloads, installs, likes, stars and uses are different measures, and most sources report none.
- **Matches can be wrong.** An entry name, a repository address or an advisory match can be mistaken. Each entry page has a way to dispute it.

## Checking the counts against the live statistics

The statistics page (https://smallprint.dev/stats, and as JSON at https://smallprint.dev/api/stats) is counted from the same record. The release's own files reproduce its figures:

```sh
python3 scripts/dataset.py check 2026-09-30
```

The script uses only the Python standard library. It counts each figure from the CSV files, fetches /api/stats, and prints both side by side, with the listed and read counts for each source. The figures it compares are: entries, servers, skills, read entries, versions, the tool totals (total, median, servers with 50 or more tools, servers that declare none), changes other than version bumps, entries and releases with a change, description, added-tool and instruction changes, version bumps with an identical hash, high grades under the data-movement rule (`*.exfiltration`) and the override rule (`*.override`), advisories (total, matched, critical, `advisory.malware-id`, entries with an advisory), chain rows, and read versions by language. The figure called "skills" on the live page counts entries of kind `agent-skill`; its sentence gives the plugins beside it.

On 2026-09-30, 29 of the 32 figures and every source's listed and read counts were equal between this release and /api/stats. The three that differ are the advisory figures (adv-total, adv-critical, adv-malware), and they differ by design: the live site counts every report on record, while this release leaves out advisories that only name packages hidden from the record. The release of 2026-09-29 matched on all 32.

For a later check, expect some gaps, and read them this way:

- The live statistics are rebuilt about once an hour and can be served up to a day old while the next build runs. A release exported at a different hour from the statistics build will differ by whatever the nightly reads wrote in between. Compare `exported_at_utc` in the manifest with the statistics' `asOf` date.
- The live figures for changes in the last 7 and 30 days count back from the moment the statistics were built, so the script does not compare them.
- Some live figures cannot be counted from this dataset because they need text or tables it leaves out: remote server read results, tool description lengths, and security news articles.

## How to cite

EmberStack LLC (2026). Small Print record of MCP server, skill and plugin small print (version 2026.09.30) [Data set]. https://smallprint.dev

Please give the release date with any figure you take from it, because the record changes every night. `CITATION.cff` in this folder carries the same details in the Citation File Format, and GitHub and most reference managers read it. In BibTeX:

```bibtex
@misc{smallprint_record_2026_09_29,
  author = {{EmberStack LLC}},
  title  = {Small Print record of MCP server, skill and plugin small print},
  year   = {2026},
  month  = {9},
  note   = {Version 2026.09.30, released 30 September 2026},
  url    = {https://smallprint.dev}
}
```

## Licence

This compilation is released under the Creative Commons Attribution 4.0 International licence (CC BY 4.0, https://creativecommons.org/licenses/by/4.0/), credited to EmberStack LLC, Small Print. You may copy, share and adapt it for any purpose, including commercial use, as long as you credit "EmberStack LLC, Small Print, https://smallprint.dev", link the licence, and say if you changed anything. This dataset is the form in which the record's metadata may be reused in bulk; the website's own terms still apply to the website.

## LICENSES: data from other sources

The dataset carries facts about public software, not its text. Where a fact comes from a source with its own terms, the source and its licence are named here.

- **Official MCP registry** (registry.modelcontextprotocol.io). Entry names, repository addresses and version strings of registry entries come from the registry's metadata, which is published under CC0 1.0 (public domain dedication). Credit to the Model Context Protocol registry maintainers is given as a courtesy.
- **GitHub Advisory Database** (github.com/advisories). GHSA identifiers, their aliases, dates, severities and affected version ranges come from the GitHub Advisory Database, licensed under CC BY 4.0. Attribution: GitHub, Inc. and the GitHub Advisory Database contributors, https://github.com/advisories, https://creativecommons.org/licenses/by/4.0/.
- **OSV** (osv.dev), **the National Vulnerability Database** (nvd.nist.gov), **the Vulnerable MCP Project** (vulnerablemcp.info) and **the Cloud Security Alliance MCP vulnerability database**. Only advisory identifiers, dates, severities and version ranges are included, attributed to the source in the `source` column. MAL- identifiers are assigned by the Open Source Security Foundation (OpenSSF) and served through OSV. This product uses data from the NVD API but is not endorsed or certified by the NVD.
- **npm, PyPI, skills.sh, ClawHub, Smithery, Hugging Face, Docker, Zed, Gemini CLI extensions and Anthropic's plugin marketplaces.** Only package names, addresses, version strings, dates and the counts named in `install_count_source` are included. No descriptions or other text from these sources are included.

Product and project names are used only to identify them. Their appearance here does not mean any of them endorses Small Print or this dataset.

## Making a release

Releases are made by the publisher from the live record with read-only queries, in one read transaction, so every file in a release describes the same moment. The manifest gives each file's row count and sha256, the export time in UTC, and the head of the record's signed chain for that night.

## Contact and corrections

EmberStack LLC runs Small Print; contact details are at https://smallprint.dev/about. A correction to one entry is best made from that entry's page, where every page has a way to dispute what it shows; corrections reach the next release.
