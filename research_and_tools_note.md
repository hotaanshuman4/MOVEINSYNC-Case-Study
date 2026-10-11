# MoveInSync FDE assignment — research and tools note

## Sources and collection
- Primary source: user-supplied CSV `google_play_reviews_1791741001758(1).csv` (360 rows; fields: Review ID, Author, Rating, Date, Helpful Count, Review Text).
- Assignment framing: user-supplied MoveInSync FDE assignment PDF.
- Collection method described in the supplied brief: browser-console JavaScript extracting review cards visible in Google Play. The export itself does not include the exact collection timestamp, visible filters, sort order, app listing URL, or pagination coverage. Those are therefore.
- Analysis date: 12 October 2026 (system date in this work session).
.

## Cleaning and validation
- Input rows: 360; no columns were missing.
- Ratings parsed as numeric: 360 valid values from 1–5; invalid/missing ratings: 0.
- Dates parsed using `%d %B %Y`: 360; failed/missing dates: 0.
- Helpful counts numeric: 360; blank/invalid: 0. A numeric 0 is treated as zero only when explicitly present.
- Duplicate review IDs: 0 rows are part of repeated-ID groups (count includes each row in a duplicate group). Duplicate normalized text: 0 rows are part of repeated-text groups. The dataset is not silently deduplicated; all rows are retained and duplicate flags are supplied.
- Original `Review Text`, rating, date, and helpful-count fields are retained. Cleaned text and parsed numeric/date columns are additional fields.

## Categorization and sentiment
- Primary category is a deterministic keyword taxonomy. Categories are evaluated in listed order and the first match wins, so each review contributes to exactly one primary category.
- The category is a triage label, not a human-validated diagnosis. Keyword overlap, negation, sarcasm, and multi-issue reviews can lead to errors. Review rows include the category rationale; manually inspect ambiguous/high-impact rows before making product commitments.
- Sentiment is a **rating proxy**: 1–2 stars = negative; 3 stars = mixed/neutral; 4–5 stars = positive. This is not NLP sentiment classification and may not reflect the wording.
- Excerpts in the report are copied from real source reviews and shortened only for display. The full original text remains in the cleaned CSV.

## Sample coverage and limitations
- Earliest parsed review date: 2018-10-03; latest parsed review date: 2026-09-18.
- The 360 records are a visible-review sample, not a verified census or random sample of all Play Store reviews. Counts are not user-prevalence estimates.
- Average rating: 2.19/5. This is not the app's overall displayed Play Store rating.
- No causal claim is made that a particular complaint caused the app's overall rating. Engineering root causes are hypotheses requiring internal telemetry and reproduction.
- This sample spans multiple years and may reflect different app versions, regions, and collection ordering. Do not interpret it as a time trend without a consistent repeated collection method.
- Author names are preserved in the source export but are not reproduced in the report; share the cleaned CSV only with appropriate internal access controls.

## Tools
- Python, pandas, NumPy, matplotlib, and ReportLab.
- A reproducible Python script is included. The script uses keyword rules and regenerates a cleaned CSV, summary metrics, issue-frequency table, and charts.

## Rerun
```bash
python -m pip install pandas numpy matplotlib
python analyze_moveinsync_reviews.py google_play_reviews_1791741001758(1).csv --outdir moveinsync_analysis
```
