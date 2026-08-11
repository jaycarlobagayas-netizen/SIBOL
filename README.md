# SIBOL

**Nutrition &amp; Reading Check for Basic Education classrooms**

Open `index.html` on any phone or laptop. It works immediately, offline, with nothing to install and nothing to configure.

DepEd already measures every learner twice a year for School Form 8. That measurement decides who gets feeding support — and then it usually stops being useful, because nobody ever puts it next to how the same child is doing in class. SIBOL puts them side by side and answers one question:

> **Are the learners who are underweight or too short the same ones who are struggling to read?**

If they are, the teacher gets their names.

---

## For teachers — start here

1. **Open the file.** On a phone: open `index.html` in Chrome, then tap the menu and **Add to Home screen**. After that it opens like an app and works with no signal.
2. **Tap “Show me a sample class.”** Twenty-four made-up learners load so you can look at every screen before typing anything real. Remove it in one tap when you are done.
3. **Then do your own class**, following the four steps along the top:

| | Step | What you do |
|---|---|---|
| 1 | **Class** | Type your learners once — name, boy or girl, birthday. Or import a CSV list. |
| 2 | **Measure** | Height and weight, one learner per screen, using the big on-screen number pad. The result appears as you type. |
| 3 | **Reading** | One tap per learner: Non-reader, Frustration, Instructional, Independent. |
| 4 | **Results** | Plain answers — who needs help, who needs it most, and whether the two problems overlap. |

Then **Reports** for the SF8 form, the feeding-programme list, the referral list and the priority list, ready to print or save as PDF.

**Nothing leaves the phone.** There is no account, no server, no internet needed. That also means that if the phone is wiped, everything is gone — so use **Settings → Download backup** at the end of every measurement round.

---

## What's in this repository

| File | Purpose |
|---|---|
| `index.html` | The whole application, including the WHO growth tables. Nothing else is required to run it. |
| `who-lms.json` | The same WHO tables as a separate file, for inspection or reuse. |
| `build_who_lms.py` | Optional. Regenerates and re-verifies `who-lms.json` from WHO's official spreadsheets. |
| `sw.js`, `manifest.webmanifest` | Make it installable and fully offline. |
| `sample-roster.csv` | The column format for importing a class list. |
| `.nojekyll` | Stops GitHub Pages running Jekyll over the files. |

## Deploy to GitHub Pages

```bash
git init && git add . && git commit -m "SIBOL v2"
git branch -M main
git remote add origin https://github.com/<you>/sibol.git
git push -u origin main
```

Then **Settings → Pages → Deploy from a branch → `main` / `/ (root)` → Save**. The app appears at `https://<you>.github.io/sibol/` within a minute or two.

Locally, just open `index.html` — everything works except the service worker, which needs `http://`. For that: `python3 -m http.server 8000`.

**Do not commit learner data.** SIBOL never writes into the repository, but backups you export contain names, birthdays and LRNs. `.gitignore` already excludes them; keep it that way.

---

## Where the healthy ranges come from

SIBOL classifies learners against the **WHO Growth Reference 5–19 years** (de Onis et al., 2007). The *L*, *M* and *S* parameters that drive every score come from WHO's own published z-score tables:

- [BMI-for-age (5–19 years)](https://www.who.int/tools/growth-reference-data-for-5to19-years/indicators/bmi-for-age) — `bmifa-boys-5-19years-z.pdf`, `bmifa-girls-5-19years-z.pdf`
- [Height-for-age (5–19 years)](https://www.who.int/tools/growth-reference-data-for-5to19-years/indicators/height-for-age) — `hfa-boys-5-19years-z.pdf`, `hfa-girls-5-19years-z.pdf`

Those tables print the L, M and S values *and* the resulting −3, −2, −1, median, +1, +2 and +3 SD values for every one of the 168 months from 61 to 228. That makes each row self-checking, and the build does check it: **every row is recomputed from its own L, M and S and compared against the SD values WHO printed beside it — 1,344 checks, largest deviation 0.05**, which is exactly the rounding of WHO's one-decimal columns. As an independent check, the tables reproduce WHO's own stated landmark that +1 SD at 19 years equals a BMI of about 25 and +2 SD about 30.

`build_who_lms.py` regenerates the file from WHO's `.xlsx` expanded tables and applies the same verification, aborting rather than writing anything that fails. You do not need to run it — the data is already in `index.html` — but it is there so the numbers can be re-derived from source rather than trusted.

### Method

```
z = ((X / M)^L − 1) / (L · S)          and    z = ln(X / M) / S  when L = 0
```

For BMI-for-age, WHO restricts the distribution to the range where real data exist, so beyond ±3 SD SIBOL applies WHO's documented linear extension rather than the raw formula. Height-for-age is not truncated.

| BMI-for-age | Status | Height-for-age | Status |
|---|---|---|---|
| < −3 | Severely wasted | < −3 | Severely stunted |
| −3 to < −2 | Wasted | −3 to < −2 | Stunted |
| −2 to +1 | Normal | −2 to +2 | Normal |
| > +1 to +2 | Overweight | > +2 | Tall |
| > +2 | Obese | | |

**Statistics.** Chi-square test of independence with Yates' correction on 2×2 tables, Cramér's V for effect size, McNemar's test with continuity correction for baseline-to-endline change, Wilson score intervals for proportions. The chi-square tail probability comes from a regularized incomplete gamma function, so no statistical library is needed. SIBOL reports the smallest expected cell count and downgrades any p-value the approximation cannot support — routine at class size — instead of presenting it as if it were solid.

Teachers see plain sentences. The statistics sit under **“Show the numbers”** for a supervisor or reviewer.

---

## Privacy

- All data lives in this browser's IndexedDB on this device. Nothing is transmitted anywhere.
- **Hide learners' names** (Settings) replaces every name with a stable code on screen, in exports and on printed reports. Names stay on the device; they are simply not shown.
- A pilot in a real school still needs school consent and a data-sharing agreement. Local-first storage reduces the risk; it does not remove the obligation.

## What SIBOL cannot do

- **It shows a link, not a cause.** A significant result means the undernourished learners are disproportionately the ones falling behind. That justifies targeting them. It is not evidence that malnutrition caused the reading difficulty.
- **It is only as good as the scale.** A scale that is consistently 2 kg out corrupts every result and no software can detect it. The calibration checklist sits inside the measurement screen for that reason.
- **It does not diagnose.** Severe cases go to a health professional, every time.
- **The reading level is teacher-reported.** Good enough to decide who to help first; not a validated literacy instrument.
- **One class is a small sample.** A non-significant result in a single class is weak evidence of anything.

## Generating evidence a reviewer will ask for

1. **Accuracy** — run one school's existing SF8 records through SIBOL and compare against the manually computed originals. Manual WHO table lookup produces well-known misclassification; measuring that error rate is a finding on its own.
2. **Efficiency** — time the manual SF8 workflow for one class against the SIBOL workflow.
3. **Association** — for a school with both SF8 records and reading assessment results, compute the cross-tabulation retrospectively. This is the headline result and it requires only data entry.

## Reference

de Onis M, Onyango AW, Borghi E, Siyam A, Nishida C, Siekmann J. Development of a WHO growth reference for school-aged children and adolescents. *Bulletin of the World Health Organization* 2007;85(9):660–667.

SIBOL is an independent tool. It is not produced, endorsed or certified by WHO or by the Department of Education.

## Licence

MIT for the application code. The WHO growth reference data is published by WHO under its own terms of use and is not covered by this licence.
