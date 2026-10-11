#!/usr/bin/env python3
import argparse, os, re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

RULES = {
    "GPS / live tracking / ETA": [r"\bgps\b", r"\blocation\b", r"\btracking\b", r"\btrack\b", r"\beta\b", r"\barrival time\b", r"\brealtime\b", r"\breal time\b", r"\bmap\b", r"\bvehicle location\b", r"\bcab icon\b"],
    "Booking / booking state": [r"\bbook", r"\bshuttle\b", r"\bcab\b", r"\bbooking\b", r"\bconfirm", r"\breserv", r"\btrip\b"],
    "Notifications / check-in / no-show": [r"\bnotification", r"\bcheck.?in\b", r"\bno.?show\b", r"\bmiss(ed|ing)? the (bus|cab)\b", r"\balert\b"],
    "Login / OTP / account / profile": [r"\blog.?in\b", r"\bsign.?up\b", r"\botp\b", r"\bauth", r"\bpassword\b", r"\baccount\b", r"\bemployee id\b", r"\baddress\b", r"\bprofile\b", r"\bsession\b"],
    "Crashes / performance / connectivity": [r"\bcrash", r"\bslow\b", r"\bload(ing)?\b", r"\bhang", r"\bfreeze", r"\bnetwork\b", r"\bno network\b", r"\bnot installed\b", r"\bblank screen\b", r"\berror\b", r"\bbug\b"],
    "Support / driver contact / issue resolution": [r"\bsupport\b", r"\bhelp.?desk\b", r"\bcall(ing)? the driver\b", r"\bcontact\b", r"\boperational number\b", r"\bfeedback\b", r"\bcomplaint\b"],
    "Pickup / routing / safety": [r"\bpick.?up\b", r"\bdrop.?off\b", r"\broute\b", r"\brouting\b", r"\bdriver\b", r"\bvehicle\b", r"\blate\b", r"\bsafety\b", r"\bdangerous\b", r"\bstop\b"],
    "Usability / UI / instructions": [r"\bui\b", r"\buser.?friendly\b", r"\bdifficult to use\b", r"\bconfus", r"\binstruction", r"\bnavigation\b", r"\bfeature\b", r"\bdesign\b", r"\binterface\b", r"\boption\b"],
}
def categorize(text):
    for category, patterns in RULES.items():
        if any(re.search(pattern, text) for pattern in patterns):
            return category
    return "Other / unclear"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_csv")
    ap.add_argument("--outdir", default="moveinsync_analysis")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    charts = os.path.join(args.outdir, "charts")
    os.makedirs(charts, exist_ok=True)
    raw = pd.read_csv(args.input_csv)
    required = ["Review ID", "Author", "Rating", "Date", "Helpful Count", "Review Text"]
    missing = [c for c in required if c not in raw.columns]
    if missing: raise SystemExit(f"Missing required columns: {missing}")
    df = raw.copy()
    df["rating_numeric"] = pd.to_numeric(df["Rating"], errors="coerce")
    df.loc[~df["rating_numeric"].isin([1,2,3,4,5]), "rating_numeric"] = np.nan
    df["date_parsed"] = pd.to_datetime(df["Date"], format="%d %B %Y", errors="coerce")
    df["helpful_numeric"] = pd.to_numeric(df["Helpful Count"], errors="coerce")
    df["review_text_original"] = df["Review Text"]
    df["review_text_clean"] = (df["Review Text"].fillna("").astype(str).str.lower()
        .str.replace(r"https?://\S+", " ", regex=True)
        .str.replace(r"[^a-z0-9\s]", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True).str.strip())
    df["primary_issue_category"] = df["review_text_clean"].map(categorize)
    df["sentiment_proxy_from_rating"] = np.select(
        [df["rating_numeric"] <= 2, df["rating_numeric"] >= 4],
        ["negative", "positive"], default="mixed/neutral")
    df["duplicate_review_id"] = df["Review ID"].duplicated(keep="first")
    df["duplicate_normalized_text"] = df["review_text_clean"].duplicated(keep="first")
    df["data_quality_flags"] = df.apply(lambda r: "; ".join(
        (["missing_review_id"] if pd.isna(r["Review ID"]) or not str(r["Review ID"]).strip() else []) +
        (["invalid_or_missing_rating"] if pd.isna(r["rating_numeric"]) else []) +
        (["unparsed_or_missing_date"] if pd.isna(r["date_parsed"]) else []) +
        (["missing_helpful_count"] if pd.isna(r["helpful_numeric"]) else []) +
        (["empty_review_text"] if not str(r["review_text_original"] or "").strip() else [])), axis=1)
    df.to_csv(os.path.join(args.outdir, "cleaned_reviews.csv"), index=False)
    rated = df[df["rating_numeric"].isin([1,2,3,4,5])]
    counts = rated["rating_numeric"].value_counts().reindex([1,2,3,4,5], fill_value=0)
    categories = df["primary_issue_category"].value_counts()
    summary = pd.DataFrame({"metric": [
        "input_rows", "valid_ratings", "mean_sample_rating", "ratings_1_2_count",
        "earliest_parsed_date", "latest_parsed_date", "missing_or_invalid_ratings",
        "unparsed_dates", "duplicate_review_id_rows", "duplicate_normalized_text_rows"],
        "value": [len(df), len(rated), rated["rating_numeric"].mean(),
                  int((rated["rating_numeric"] <= 2).sum()),
                  df["date_parsed"].min(), df["date_parsed"].max(),
                  int(df["rating_numeric"].isna().sum()), int(df["date_parsed"].isna().sum()),
                  int(df["Review ID"].duplicated(keep=False).sum()),
                  int(df["review_text_clean"].duplicated(keep=False).sum())]})
    summary.to_csv(os.path.join(args.outdir, "summary_metrics.csv"), index=False)
    categories.rename_axis("primary_issue_category").reset_index(name="review_count").to_csv(
        os.path.join(args.outdir, "issue_frequency.csv"), index=False)
    plt.figure(figsize=(7,4))
    plt.bar(counts.index.astype(int).astype(str), counts.values)
    plt.title(f"Rating distribution (n={len(rated)})"); plt.xlabel("Stars"); plt.ylabel("Count")
    plt.tight_layout(); plt.savefig(os.path.join(charts, "rating_distribution.png"), dpi=160); plt.close()
    ordered = categories.sort_values()
    plt.figure(figsize=(9,5))
    plt.barh(ordered.index, ordered.values); plt.title(f"Primary issue categories (n={len(df)})")
    plt.xlabel("Review count"); plt.tight_layout()
    plt.savefig(os.path.join(charts, "issue_frequency.png"), dpi=160); plt.close()
    print(summary.to_string(index=False))
    print("\\nIssue categories:\\n", categories.to_string())
if __name__ == "__main__": main()
