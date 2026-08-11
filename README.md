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

## The statistical dashboard

Step through to **Dashboard** for the same findings presented for a supervisor, a division office or a research reviewer. Everything is computed in the browser from the underlying records and prints to PDF.

**Tables**

- **Table 1 — Description of the sample.** Enrolled, analytic *n*, boys/girls, age mean ± standard deviation and range, and how much of the sample also has a learning level recorded. Flags samples under 30 as underpowered rather than letting the reader assume otherwise.
- **Table 2 — Prevalence of malnutrition.** Wasting, severe wasting, stunting, severe stunting, overweight/obesity and the combined figure, each as n/N with a percentage and a 95% Wilson score confidence interval.
- **Table 3 — Contingency table.** The 2 × 2 of nutritional status against learning benchmark.

**Figures** — hand-drawn inline SVG, no chart library, no content delivery network, works offline. Every element is hoverable and tappable and reports its exact numbers in the bar beneath the figure.

| Figure | Type | Why this type |
|---|---|---|
| 1 & 2 | **Donut** | Composition — share of one group across mutually exclusive categories. A pie family chart is the right choice for parts of a whole, and only for that. |
| 3 | **Histogram with reference normal curve** | Distribution. Shows whether the *whole class* has shifted left rather than whether a few individuals fell below a line — a different and more serious finding. |
| 4 | **Line chart, growth reference** | Each learner plotted at their exact age against the World Health Organization −3, −2, median and +2 standard deviation curves, with the danger bands shaded. Toggles between sexes and between the two indicators. |
| 5 | **Bar chart with 95% confidence intervals** | Comparison of two proportions. Error bars are shown because a bare pair of percentages from a class of forty is not a finding. |
| 6 | **Radar** | Multivariate profile — six risks on one shape, with baseline (Q1) and endline (Q4) overlaid. This is the case where a radar is genuinely the right tool rather than decoration. |
| 7 | **Slope chart** | Paired change, Quarter 1 to Quarter 4. Shows whether the same children improved, which a pair of summary percentages hides completely. |

**Inferential statistics reported**

- Chi-square test of independence with Yates' continuity correction, degrees of freedom, *p*, and Cramér's V as effect size
- Risk ratio with a 95% interval by the Katz method; odds ratio with Woolf's interval and a Haldane–Anscombe correction when a cell is empty
- Difference in proportions with a 95% interval
- One-sample *t* test of the mean z-score against the reference median, so a group-level shift can be distinguished from individual outliers
- McNemar's test on paired change in status, plus a paired *t* test on change in z-score
- Wilson score intervals throughout

Where the smallest expected cell count falls below 5, the chi-square result is **labelled unreliable and Fisher's exact test named as the correct alternative** rather than being reported as though it were sound. Tail probabilities come from series and continued-fraction expansions of the incomplete gamma and incomplete beta functions, which is why no statistical library is needed and the whole thing still runs with no signal.

A **Statistical methods** section states the LMS formula, the ±3 standard deviation truncation rule, the reporting conventions, and — plainly — that these are observational classroom data, that association is not causation, and that household poverty, absenteeism and prior schooling are unadjusted confounders.

A full **reference list** covers the growth reference (de Onis et al. 2007; Cole 1990; Cole & Green 1992) and every statistical method used (Wilson 1927; Fisher 1922; Yates 1934; Cramér 1946; McNemar 1947; Woolf 1955; Katz et al. 1978; Agresti & Coull 1998; de Onis et al. 2019). **World Health Organization** is spelled out throughout; where the acronym appears inside a published article title it is left verbatim and annotated, because titles are not ours to edit.

## EDCOM II alignment

The dashboard closes with a policy-alignment section covering the **Second Congressional Commission on Education (EDCOM II)** — its 28 priority areas, its three reports (*Miseducation*, January 2024; *Fixing the Foundations*, January 2025; *Turning Point: A Decade of Necessary Reforms 2026–2035*, February 2026), the stunting figures it cites from the Expanded National Nutrition Survey, and a table mapping each of the commission's directions to what SIBOL actually contributes.

It also says what SIBOL **cannot** do. The commission's nutrition emphasis is the first 1,000 days; by Grade 4 stunting has already happened and feeding will not reverse it. SIBOL works the school-age end of the same problem — identifying who arrived already affected, separating them from those whose problem is current and treatable, and connecting both to how the child is actually learning. Claiming more than that would be dishonest.

SIBOL is independent and is not endorsed by or affiliated with EDCOM II, the Department of Education, or the World Health Organization.

---

## Design

**Palette.** Dark green (`#0E4A37`), white, and yellow (`#F2C230` / `#FDF3D0`). Every text-on-background pair that carries a number was contrast-checked against WCAG AA — 33 pairs, all passing, the lowest at 4.89:1 for small grey axis labels where the standard is 3.0:1. Numerals are given an explicit dark ink colour rather than inheriting whatever the parent had.

**Severity encoding.** Nutrition categories run dark green (healthy) → yellow → amber → dark brown (severe), staying inside the palette. The two severe categories are **additionally hatched** in the figures and drawn with a heavier dark outline on the growth chart, so they remain distinguishable in greyscale, in a photocopy, and to readers with colour vision deficiency. Colour alone is never the only signal.

**Icons.** Original line art drawn as inline SVG, inheriting `currentColor`. No emoji anywhere in the file.

**Caption convention.** Figures are `<figure>` elements: **number and title above** the graphic, ***Note.*** and ***Source.*** below it. Tables carry **number and title above**, note below. Figures are numbered 1–7 and tables 1–3, in order of appearance. The contingency table was pulled out of the figure block it was previously buried in and given its own numbered table.

## Baseline and endline only

SIBOL reports on the two mandated measurement rounds, and the learning indicator is bound to them:

- **Baseline → Quarter 1**
- **Endline → Quarter 4**

There is no free quarter picker anywhere; choosing a round sets the quarter. If an earlier version left reading levels recorded against Quarter 2 or Quarter 3, **Settings** surfaces them and offers to move them (Q2 → Q1, Q3 → Q4) or delete them — it does not silently discard them.

## Official emblems

The World Health Organization emblem is a protected mark, and the Department of Education and EDCOM II marks are government marks. **None of them are reproduced in this file.** Copying them into a published repository would risk implying an endorsement that does not exist.

The dashboard instead carries an attribution bar of three original SIBOL badges, each naming its organisation in words and stating what SIBOL takes from it. If your deployment is authorised to display the official emblems, drop any of these beside `index.html` and they are picked up automatically at render time:

```
logo-who.png      logo-deped.png      logo-edcom.png
```

SIBOL remains independent and is not endorsed by, affiliated with, or produced for any of the three.

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
