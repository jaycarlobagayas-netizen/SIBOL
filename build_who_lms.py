#!/usr/bin/env python3
"""
build_who_lms.py — turn the official WHO Growth Reference 5–19 spreadsheets
into who-lms.json for SIBOL.

Why this script exists
----------------------
SIBOL classifies real children. The L, M and S parameters that drive every
z-score are therefore never typed in by hand and never reproduced from memory.
They are read directly out of the .xlsx files WHO publishes, and the script
verifies its own output against WHO's own SD columns before writing anything.

Usage
-----
    python3 build_who_lms.py                 # download from who.int, then build
    python3 build_who_lms.py --dir ./who     # use .xlsx files already downloaded
    python3 build_who_lms.py --inject        # also bake the tables into index.html

Requires Python 3.8+. No third-party packages — .xlsx parsing is stdlib only.

Source files (WHO, "Expanded tables for constructing national health cards"):
    BMI-for-age    boys   bmi-boys-z-who-2007-exp.xlsx
    BMI-for-age    girls  bmi-girls-z-who-2007-exp.xlsx
    Height-for-age boys   hfa-boys-z-who-2007-exp.xlsx
    Height-for-age girls  hfa-girls-z-who-2007-exp.xlsx

Reference: de Onis M, Onyango AW, Borghi E, Siyam A, Nishida C, Siekmann J.
Development of a WHO growth reference for school-aged children and adolescents.
Bull World Health Organ. 2007;85(9):660-667.
"""

import argparse
import datetime
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

BASE = ("https://cdn.who.int/media/docs/default-source/child-growth/"
        "growth-reference-5-19-years/")

SOURCES = {
    ("bfa", "M"): BASE + "bmi-for-age-(5-19-years)/bmi-boys-z-who-2007-exp.xlsx?sfvrsn=a84bca93_2",
    ("bfa", "F"): BASE + "bmi-for-age-(5-19-years)/bmi-girls-z-who-2007-exp.xlsx?sfvrsn=79222875_2",
    ("hfa", "M"): BASE + "height-for-age-(5-19-years)/hfa-boys-z-who-2007-exp.xlsx?sfvrsn=7fa263d_2",
    ("hfa", "F"): BASE + "height-for-age-(5-19-years)/hfa-girls-z-who-2007-exp.xlsx?sfvrsn=79d310ee_2",
}

LOCAL_HINTS = {
    ("bfa", "M"): ("bmi", "boy"),
    ("bfa", "F"): ("bmi", "girl"),
    ("hfa", "M"): ("hfa", "boy"),
    ("hfa", "F"): ("hfa", "girl"),
}

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


# --------------------------------------------------------------------------
# minimal .xlsx reader (stdlib only)
# --------------------------------------------------------------------------
def _col_index(ref):
    """'BC12' -> 54 (zero-based column index)."""
    letters = re.match(r"([A-Z]+)", ref).group(1)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_xlsx(path):
    """Return the first worksheet as a list of rows of str/float."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.iter(
                    "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")))

        sheets = sorted(n for n in z.namelist()
                        if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
        if not sheets:
            raise SystemExit("%s contains no worksheet" % path)
        root = ET.fromstring(z.read(sheets[0]))

        rows = []
        for row in root.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
            cells = {}
            for c in row.findall("m:c", NS):
                ref = c.get("r") or ""
                idx = _col_index(ref) if ref else len(cells)
                t = c.get("t")
                if t == "inlineStr":
                    node = c.find("m:is", NS)
                    val = "".join(x.text or "" for x in node.iter(
                        "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")) if node is not None else ""
                else:
                    v = c.find("m:v", NS)
                    raw = v.text if v is not None else None
                    if raw is None:
                        val = ""
                    elif t == "s":
                        val = shared[int(raw)]
                    elif t in ("str", "e"):
                        val = raw
                    else:
                        try:
                            val = float(raw)
                        except ValueError:
                            val = raw
                cells[idx] = val
            if cells:
                width = max(cells) + 1
                rows.append([cells.get(i, "") for i in range(width)])
    return rows


# --------------------------------------------------------------------------
# table extraction + self-check
# --------------------------------------------------------------------------
def value_at_z(L, M, S, z):
    return M * pow(1 + L * S * z, 1.0 / L) if L != 0 else M * pow(2.718281828459045, S * z)


def extract(rows, label):
    """Pull {month: [L, M, S]} out of a WHO expanded z-score sheet."""
    header_i = None
    for i, r in enumerate(rows[:20]):
        low = [str(c).strip().lower() for c in r]
        if "l" in low and "m" in low and "s" in low and any(x in low for x in ("month", "age", "age (months)")):
            header_i = i
            break
    if header_i is None:
        raise SystemExit("%s: could not find a header row containing Month, L, M, S" % label)

    head = [str(c).strip().lower() for c in rows[header_i]]

    def col(*names):
        for n in names:
            if n in head:
                return head.index(n)
        return None

    ci = {
        "month": col("month", "age", "age (months)"),
        "L": col("l"), "M": col("m"), "S": col("s"),
        "sd2neg": col("sd2neg", "-2 sd", "sd2neg "),
        "sd1neg": col("sd1neg", "-1 sd"),
        "sd1": col("sd1", "+1 sd"),
        "sd2": col("sd2", "+2 sd"),
    }
    for k in ("month", "L", "M", "S"):
        if ci[k] is None:
            raise SystemExit("%s: missing the %s column" % (label, k))

    table, checked, worst = {}, 0, 0.0
    for r in rows[header_i + 1:]:
        try:
            month = int(float(r[ci["month"]]))
            L = float(r[ci["L"]]); M = float(r[ci["M"]]); S = float(r[ci["S"]])
        except (ValueError, TypeError, IndexError):
            continue
        if M <= 0 or S <= 0:
            raise SystemExit("%s: month %d has non-positive M or S" % (label, month))
        table[month] = [L, M, S]

        # integrity check: recompute WHO's own +/-1 and +/-2 SD columns from LMS
        for key, z in (("sd2neg", -2), ("sd1neg", -1), ("sd1", 1), ("sd2", 2)):
            j = ci[key]
            if j is None or j >= len(r):
                continue
            try:
                published = float(r[j])
            except (ValueError, TypeError):
                continue
            diff = abs(value_at_z(L, M, S, z) - published)
            worst = max(worst, diff)
            checked += 1

    if not table:
        raise SystemExit("%s: no data rows found" % label)
    if checked and worst > 0.05:
        raise SystemExit("%s: FAILED integrity check — recomputed SD columns differ from "
                         "WHO's published values by up to %.4f. Do not ship this file." % (label, worst))

    months = sorted(table)
    gaps = [m for m in range(months[0], months[-1] + 1) if m not in table]
    print("  %-14s months %d–%d (%d rows), %d SD values re-checked, max deviation %.5f%s"
          % (label, months[0], months[-1], len(table), checked, worst,
             ", %d GAPS" % len(gaps) if gaps else ""))
    if gaps:
        raise SystemExit("%s: age table has gaps at %s" % (label, gaps[:10]))
    return table


def fetch(url, dest):
    import urllib.request
    print("  downloading %s" % os.path.basename(dest))
    req = urllib.request.Request(url, headers={"User-Agent": "sibol-build/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())


def find_local(directory, hints):
    a, b = hints
    for name in sorted(os.listdir(directory)):
        low = name.lower()
        if low.endswith(".xlsx") and a in low and b in low and "perc" not in low:
            return os.path.join(directory, name)
    return None


def main():
    ap = argparse.ArgumentParser(description="Build who-lms.json for SIBOL from official WHO spreadsheets.")
    ap.add_argument("--dir", default="who-source", help="folder holding (or to hold) the WHO .xlsx files")
    ap.add_argument("--out", default="who-lms.json", help="output JSON path")
    ap.add_argument("--offline", action="store_true", help="never download; fail if a file is missing")
    ap.add_argument("--inject", action="store_true", help="also embed the tables into index.html")
    ap.add_argument("--html", default="index.html", help="path to index.html for --inject")
    args = ap.parse_args()

    os.makedirs(args.dir, exist_ok=True)
    out = {"meta": {}, "bfa": {}, "hfa": {}}
    used = {}

    print("Building WHO 5–19 LMS tables")
    for (indicator, sex), url in SOURCES.items():
        path = find_local(args.dir, LOCAL_HINTS[(indicator, sex)])
        if not path:
            if args.offline:
                raise SystemExit("missing %s %s file in %s and --offline was given" % (indicator, sex, args.dir))
            path = os.path.join(args.dir, os.path.basename(url.split("?")[0]))
            try:
                fetch(url, path)
            except Exception as e:
                raise SystemExit(
                    "could not download %s (%s).\nDownload the four 'Expanded tables for constructing "
                    "national health cards' (z-scores, boys and girls) by hand from\n"
                    "  https://www.who.int/tools/growth-reference-data-for-5to19-years/indicators/bmi-for-age\n"
                    "  https://www.who.int/tools/growth-reference-data-for-5to19-years/indicators/height-for-age\n"
                    "put them in %s, and re-run with --offline." % (url, e, args.dir))
        label = "%s %s" % (indicator, "boys" if sex == "M" else "girls")
        out[indicator][sex] = extract(read_xlsx(path), label)
        used[label] = os.path.basename(path)

    # cross-check: both sexes and both indicators must cover the same age span
    spans = {k + " " + s: (min(map(int, t)), max(map(int, t)))
             for k in ("bfa", "hfa") for s, t in out[k].items()}
    if len(set(spans.values())) != 1:
        print("  note: age spans differ between tables: %s" % spans, file=sys.stderr)

    out["meta"] = {
        "source": "WHO Growth Reference 5–19 years (de Onis et al., Bull World Health Organ 2007;85:660-667), "
                  "expanded tables for constructing national health cards, z-scores",
        "files": used,
        "generated": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "builder": "build_who_lms.py",
        "note": "L, M, S read directly from the WHO spreadsheets and verified against WHO's own "
                "published +/-1 and +/-2 SD columns. Not transcribed by hand.",
    }

    # JSON keys must be strings
    for ind in ("bfa", "hfa"):
        for sex in out[ind]:
            out[ind][sex] = {str(k): v for k, v in sorted(out[ind][sex].items())}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))
    print("wrote %s (%.1f KB)" % (args.out, os.path.getsize(args.out) / 1024.0))

    if args.inject:
        payload = json.dumps(out, separators=(",", ":"))
        with open(args.html, encoding="utf-8") as f:
            html = f.read()
        pattern = re.compile(
            r'(<script id="who-lms-data" type="application/json">).*?(</script>)', re.S)
        if not pattern.search(html):
            raise SystemExit("could not find the who-lms-data script tag in %s" % args.html)
        html = pattern.sub(lambda m: m.group(1) + payload + m.group(2), html, count=1)
        with open(args.html, "w", encoding="utf-8") as f:
            f.write(html)
        print("injected tables into %s (%.1f KB total)" % (args.html, os.path.getsize(args.html) / 1024.0))


if __name__ == "__main__":
    main()
