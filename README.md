# SIBOL

**Nutrition–Learning Screening for Mindanao Classrooms**

An offline-first, zero-cost web application that turns the height and weight DepEd already collects into actionable evidence about who is failing to learn, and why.

DepEd measures every learner twice a year for School Form 8. Those measurements decide who receives School-Based Feeding Program support, and then they stop being useful — recorded on paper, hand-classified against WHO tables, submitted upward as compliance counts. The teacher who took the measurement rarely gets an interpretation back, and the nutrition data is never joined to the learning data sitting in the same class record.

SIBOL joins them, offline, on the phone the teacher already owns, and answers the question the system currently cannot: **are the learners who are wasted or stunted the same learners who are failing to read?**

---

## What's in this repository

| File | Purpose |
|---|---|
| `index.html` | The entire application. No framework, no build step, no runtime dependencies. |
| `who-lms.json` | WHO 5–19 LMS reference tables. **Not included — you generate it** (see below). |
| `build_who_lms.py` | Converts the official WHO spreadsheets into `who-lms.json`. Python 3.8+, stdlib only. |
| `sw.js` | Service worker for full offline use once installed. |
| `manifest.webmanifest` | Makes SIBOL installable to the home screen as a PWA. |
| `sample-roster.csv` | Column format for roster import. |
| `.nojekyll` | Stops GitHub Pages running Jekyll over the files. |

---

## Step 1 — Get the WHO reference data

**SIBOL ships without the WHO tables and refuses to classify anyone until they are loaded.** This is deliberate. The L, M and S parameters drive every z-score; one wrong number misclassifies a real child. They are never typed in by hand.

```bash
python3 build_who_lms.py
```

That downloads the four official WHO files, parses them, verifies its own output against WHO's published ±1 SD and ±2 SD columns, and writes `who-lms.json`. If any recomputed value differs from WHO's by more than 0.05 the script aborts rather than write a file.

If the machine has no internet, download these four "Expanded tables for constructing national health cards — z-scores" by hand, put them in a folder called `who-source/`, and run `python3 build_who_lms.py --offline`:

- BMI-for-age: <https://www.who.int/tools/growth-reference-data-for-5to19-years/indicators/bmi-for-age> → `bmi-boys-z-who-2007-exp.xlsx`, `bmi-girls-z-who-2007-exp.xlsx`
- Height-for-age: <https://www.who.int/tools/growth-reference-data-for-5to19-years/indicators/height-for-age> → `hfa-boys-z-who-2007-exp.xlsx`, `hfa-girls-z-who-2007-exp.xlsx`

To bake the tables into `index.html` so it works as a genuinely single file you can email or put on a USB stick:

```bash
python3 build_who_lms.py --inject
```

## Step 2 — Deploy to GitHub Pages

```bash
git init
git add .
git commit -m "SIBOL v1"
git branch -M main
git remote add origin https://github.com/<you>/sibol.git
git push -u origin main
```

Then **Settings → Pages → Source: Deploy from a branch → `main` / `/ (root)` → Save**. The app appears at `https://<you>.github.io/sibol/` within a minute or two.

Two things to know before you push:

- **`who-lms.json` must be committed** for the deployed app to classify anything. It is roughly 60 KB.
- **Do not commit learner data.** SIBOL never writes files into the repository, but backups you export do contain names, birthdates and LRNs. Keep them out of git.

Locally, open `index.html` directly in a browser — everything works except the service worker and the automatic `who-lms.json` fetch, which need `http://`. For a local server: `python3 -m http.server 8000`.

## Step 3 — Use it

1. **Setup** — school details and at least one class.
2. **Roster** — add learners, or import `sample-roster.csv`'s column format. Birthdate is mandatory; age in completed months drives every z-score.
3. **Measure** — pick the round (baseline or endline), read the protocol guide, then work down the class list. Height, weight, Enter, next learner. The classification appears as you type.
4. **Learning** — one band per learner per quarter: reading level, numeracy, or quarterly grade.
5. **Analysis** — distributions, the nutrition × learning contingency table with a chi-square test, the named double-burden list, and baseline-vs-endline movement against the SBFP 70% criterion.
6. **Reports** — SF8 format, SBFP shortlist, referral list, double-burden list, CSV export, print to PDF.

---

## Method

For a measurement *X* at a given sex and age in completed months, with WHO parameters *L*, *M*, *S*:

```
z = ((X / M)^L − 1) / (L · S)        and    z = ln(X / M) / S  when L = 0
```

For BMI-for-age, WHO restricts the Box–Cox distribution to the range where empirical data exist. Beyond ±3 SD, SIBOL applies WHO's documented linear extrapolation instead of the raw LMS value:

```
z >  3  →   3 + (X − SD3⁺) / (SD3⁺ − SD2⁺)
z < −3  →  −3 + (X − SD3⁻) / (SD2⁻ − SD3⁻)
```

Height-for-age is a length-based indicator and is not truncated.

**Cut-offs** (WHO 2007, as used in DepEd School Form 8):

| BMI-for-age | Status | Height-for-age | Status |
|---|---|---|---|
| < −3 | Severely wasted | < −3 | Severely stunted |
| −3 to < −2 | Wasted | −3 to < −2 | Stunted |
| −2 to +1 | Normal | −2 to +2 | Normal |
| > +1 to +2 | Overweight | > +2 | Tall |
| > +2 | Obese | | |

**Statistics.** Chi-square test of independence with Yates' continuity correction on 2×2 tables; Cramér's V as the effect size; McNemar's test with continuity correction for baseline-to-endline status change; Wilson score intervals for proportions. The chi-square upper-tail probability comes from a regularized incomplete gamma function (series and continued-fraction expansions), so no statistical library is needed. SIBOL states the smallest expected cell count and warns when the chi-square approximation is not trustworthy rather than reporting a p-value as if it were.

**Data quality.** SIBOL flags biologically implausible heights, weights and BMIs, and flags height/weight transposition. It cannot detect a scale that is consistently wrong — only calibration can, which is why the calibration checklist sits in the measurement screen and not in an appendix.

---

## Privacy and data handling

- All data lives in this browser's IndexedDB on this device. Nothing is transmitted anywhere. There is no server and no account.
- **Anonymisation mode** replaces every learner name with a stable code on screen, in exports and in printed reports. Names remain on the device; they are simply not displayed.
- Clearing site data deletes everything. Export a backup at the end of each measurement round.
- A pilot in a real school needs school consent and a data-sharing agreement. Local-first storage reduces the risk; it does not remove the obligation.

## Honest limitations

- **SIBOL detects association, not causation.** A significant chi-square means the undernourished learners are disproportionately the ones falling behind. That is enough to justify targeting them; it is not evidence that malnutrition caused the reading difficulty.
- **Output quality is capped by measurement quality.** Uncalibrated scales and poor stadiometer technique corrupt z-scores regardless of the software.
- **SIBOL does not diagnose.** It flags learners for teacher and health-worker attention. Severe cases go to a health professional.
- **The learning indicator is teacher-reported and coarse.** Adequate for triage and priority-setting; not a validated literacy instrument.
- Class-sized samples are small. A non-significant result in one class is weak evidence of anything.

## Generating evidence a reviewer will ask for

Three studies are available immediately from data schools already hold:

1. **Accuracy** — run one school's existing SF8 records through SIBOL and compare against the manually computed originals. Manual WHO table lookup produces well-known misclassification; quantifying that error rate is a publishable finding on its own.
2. **Efficiency** — time the manual SF8 workflow for one class against the SIBOL workflow.
3. **Association** — for a school with both SF8 records and reading assessment results, compute the cross-tabulation retrospectively. This is the headline result and it requires only data entry.

---

## Reference

de Onis M, Onyango AW, Borghi E, Siyam A, Nishida C, Siekmann J. Development of a WHO growth reference for school-aged children and adolescents. *Bulletin of the World Health Organization* 2007;85(9):660–667.

SIBOL is an independent tool. It is not produced, endorsed or certified by WHO or by the Department of Education. The WHO growth reference data is published by WHO under its own terms of use.

## Licence

MIT for the application code. WHO reference data is not covered by this licence — see WHO's terms of use.
