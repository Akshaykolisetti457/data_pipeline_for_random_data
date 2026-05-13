"""
Stage 3 — Data Processing
Reads cleaned_data.csv and produces enriched, analysis-ready outputs:

  1.  Feature Engineering
      - seniority_band  : years_exp bucketed into Junior/Mid/Senior/Lead
      - salary_band     : salary quintile label
      - age_group       : decade-based group (20s, 30s, 40s, …)
      - exp_salary_ratio: years_exp / salary  (talent-value proxy)
      - hire_year / hire_month: extracted from hire_date

  2.  Aggregations (department-level summary)
      - headcount, avg salary, avg age, avg performance, total sales

  3.  KPI Calculations (company-wide)
      - overall avg salary, top performers %, attrition proxy

  4.  Normalisation
      - MinMax scale salary, sales_amount, years_exp for ML-ready output

  5.  Encode categoricals
      - One-hot encode: department, city, gender
      - Ordinal encode: performance (1–5)

  6.  Export
      - data/processed/processed_data.csv      (full enriched dataset)
      - data/processed/dept_summary.csv        (department-level KPIs)
      - data/processed/company_kpis.json       (scalar KPIs as JSON)
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# ── logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── paths ─────────────────────────────────────────────────────────
BASE      = Path(__file__).resolve().parents[1]
INPUT     = BASE / "data" / "cleaned"   / "cleaned_data.csv"
OUT_DIR   = BASE / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROCESSED_CSV   = OUT_DIR / "processed_data.csv"
DEPT_SUMMARY    = OUT_DIR / "dept_summary.csv"
COMPANY_KPIS    = OUT_DIR / "company_kpis.json"


# ══════════════════════════════════════════════════════════════════
#  Feature Engineering
# ══════════════════════════════════════════════════════════════════

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns."""

    # Seniority band from years of experience
    bins   = [-1, 2, 6, 14, 100]
    labels = ["Junior", "Mid-Level", "Senior", "Lead"]
    df["seniority_band"] = pd.cut(df["years_exp"], bins=bins, labels=labels)

    # Salary quintile band
    df["salary_band"] = pd.qcut(
        df["salary"], q=5,
        labels=["Very Low", "Low", "Medium", "High", "Very High"],
        duplicates="drop",
    )

    # Age group
    df["age_group"] = (df["age"] // 10 * 10).astype(str) + "s"

    # Experience-to-salary efficiency ratio (higher = more value per $)
    df["exp_salary_ratio"] = (df["years_exp"] / df["salary"]).round(6)

    # Hire date parts
    df["hire_date"] = pd.to_datetime(df["hire_date"], errors="coerce")
    df["hire_year"]  = df["hire_date"].dt.year
    df["hire_month"] = df["hire_date"].dt.month

    log.info("Feature engineering  : 7 new columns added.")
    return df


# ══════════════════════════════════════════════════════════════════
#  Aggregations
# ══════════════════════════════════════════════════════════════════

def build_dept_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Department-level KPI rollup."""
    summary = (
        df.groupby("department", observed=True)
        .agg(
            headcount       = ("employee_id",  "count"),
            avg_salary      = ("salary",        "mean"),
            median_salary   = ("salary",        "median"),
            avg_age         = ("age",           "mean"),
            avg_performance = ("performance",   "mean"),
            avg_years_exp   = ("years_exp",     "mean"),
            total_sales     = ("sales_amount",  "sum"),
        )
        .round(2)
        .reset_index()
        .sort_values("headcount", ascending=False)
    )
    log.info("Department summary   : %d departments aggregated.", len(summary))
    return summary


# ══════════════════════════════════════════════════════════════════
#  Company-wide KPIs
# ══════════════════════════════════════════════════════════════════

def calc_company_kpis(df: pd.DataFrame) -> dict:
    top_perf_pct = round(
        (df["performance"] >= 4).sum() / len(df) * 100, 2
    )
    kpis = {
        "total_employees":        int(len(df)),
        "avg_salary_usd":         round(float(df["salary"].mean()), 2),
        "median_salary_usd":      round(float(df["salary"].median()), 2),
        "avg_age_years":          round(float(df["age"].mean()), 1),
        "avg_years_experience":   round(float(df["years_exp"].mean()), 1),
        "top_performer_pct":      top_perf_pct,
        "total_sales_usd":        round(float(df["sales_amount"].sum()), 2),
        "most_common_department": df["department"].mode()[0],
        "most_common_city":       df["city"].mode()[0],
        "hire_year_range":        f"{int(df['hire_year'].min())}-{int(df['hire_year'].max())}",
    }
    log.info("Company KPIs         : %d metrics calculated.", len(kpis))
    return kpis


# ══════════════════════════════════════════════════════════════════
#  Normalisation
# ══════════════════════════════════════════════════════════════════

def normalise_features(df: pd.DataFrame) -> pd.DataFrame:
    """MinMax scale selected numeric columns into [0, 1] range."""
    scale_cols = ["salary", "sales_amount", "years_exp"]
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df[scale_cols])
    for i, col in enumerate(scale_cols):
        df[f"{col}_norm"] = scaled[:, i].round(4)
    log.info("Normalisation        : %d columns scaled to [0,1].", len(scale_cols))
    return df


# ══════════════════════════════════════════════════════════════════
#  Encode categoricals
# ══════════════════════════════════════════════════════════════════

def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """One-hot encode department, city, gender."""
    ohe_cols = ["department", "city", "gender"]
    df = pd.get_dummies(df, columns=ohe_cols, drop_first=False, dtype=int)
    # Ordinal: performance is already 1-5 (keep as-is, it's already numeric)
    log.info("Encoding done        : one-hot applied to [department, city, gender].")
    return df


# ══════════════════════════════════════════════════════════════════
#  Main pipeline
# ══════════════════════════════════════════════════════════════════

def process_pipeline(df: pd.DataFrame):
    df = engineer_features(df)

    dept_summary = build_dept_summary(df)
    company_kpis = calc_company_kpis(df)

    df = normalise_features(df)
    df = encode_categoricals(df)

    return df, dept_summary, company_kpis


def main():
    print("=" * 55)
    print("  Stage 3 -- Processing cleaned dataset")
    print("=" * 55)

    log.info("Reading cleaned data : %s", INPUT)
    df = pd.read_csv(INPUT)
    log.info("Clean shape          : %s", df.shape)

    df_proc, dept_summary, kpis = process_pipeline(df)

    # Save outputs
    df_proc.to_csv(PROCESSED_CSV, index=False)
    dept_summary.to_csv(DEPT_SUMMARY, index=False)
    with open(COMPANY_KPIS, "w") as f:
        json.dump(kpis, f, indent=2)

    print(f"\n[OK]  Processed data   -> {PROCESSED_CSV}")
    print(f"[OK]  Dept summary     -> {DEPT_SUMMARY}")
    print(f"[OK]  Company KPIs     -> {COMPANY_KPIS}")
    print(f"\n   Final shape : {df_proc.shape[0]:,} rows x {df_proc.shape[1]} cols")
    print("\nCompany KPIs:")
    for k, v in kpis.items():
        print(f"   {k:<30} {v}")


if __name__ == "__main__":
    main()
