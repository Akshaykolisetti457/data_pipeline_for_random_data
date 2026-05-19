"""
Stage 2 — Data Cleaning
Reads raw_data.csv and applies a systematic cleaning pipeline:
  1. Drop exact duplicate rows
  2. Standardise text fields (whitespace, case)
  3. Parse & unify mixed date formats
  4. Validate / fix email addresses
  5. Impute or drop missing values (strategy-based)
  6. Remove statistical outliers (IQR method)
  7. Enforce correct dtypes
  8. Save to data/cleaned/cleaned_data.csv
"""

import re
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from dateutil import parser as date_parser

# ── logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── paths ─────────────────────────────────────────────────────────
BASE   = Path(__file__).resolve().parents[1]
INPUT  = BASE / "data" / "raw"     / "raw_data.csv"
OUTPUT = BASE / "data" / "cleaned" / "cleaned_data.csv"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════
#  Individual cleaning helpers
# ══════════════════════════════════════════════════════════════════

def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    log.info("Duplicates removed   : %d rows dropped", before - len(df))
    return df


def standardise_text(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace and title-case text columns."""
    text_cols = ["name", "department", "city", "gender"]
    for col in text_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.title()
                .replace("None", np.nan)
                .replace("Nan", np.nan)
            )
    # Normalise gender values: M/Male → Male, F/Female → Female
    gender_map = {"M": "Male", "F": "Female","female":"Female","male":"Male"}
    df["gender"] = df["gender"].replace(gender_map)
    log.info("Text columns standardised.")
    return df


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Convert mixed-format hire_date strings to YYYY-MM-DD."""
    def safe_parse(val):
        try:
            return date_parser.parse(str(val)).strftime("%Y-%m-%d")
        except Exception:
            return np.nan

    df["hire_date"] = df["hire_date"].apply(safe_parse)
    df["hire_date"] = pd.to_datetime(df["hire_date"], errors="coerce")
    bad_dates = df["hire_date"].isna().sum()
    log.info("Date parsing done    : %d unparseable dates set to NaT", bad_dates)
    return df


def validate_emails(df: pd.DataFrame) -> pd.DataFrame:
    """Nullify malformed email addresses."""
    pattern = re.compile(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$")
    def is_valid(email):
        if pd.isna(email):
            return np.nan
        return email.lower() if pattern.match(str(email)) else np.nan

    before_null = df["email"].isna().sum()
    df["email"] = df["email"].apply(is_valid)
    after_null  = df["email"].isna().sum()
    log.info("Invalid emails fixed : %d additional emails nullified",
             after_null - before_null)
    return df


def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Impute or drop based on column strategy."""
    # Rows where name is missing — can't identify the record → drop
    before = len(df)
    df = df.dropna(subset=["name"])
    log.info("Rows missing 'name'  : %d dropped", before - len(df))

    # Numeric columns: impute with median
    num_impute = ["age", "salary", "years_exp", "sales_amount"]
    for col in num_impute:
        if col in df.columns:
            median_val = df[col].median()
            filled = df[col].isna().sum()
            df[col] = df[col].fillna(median_val)
            log.info("Imputed %-14s: %d nulls → median (%.2f)", col, filled, median_val)

    # Categorical columns: impute with mode
    cat_impute = ["gender", "department", "city", "performance"]
    for col in cat_impute:
        if col in df.columns:
            mode_val = df[col].mode(dropna=True)
            if not mode_val.empty:
                filled = df[col].isna().sum()
                df[col] = df[col].fillna(mode_val[0])
                log.info("Imputed %-14s: %d nulls → mode (%s)", col, filled, mode_val[0])

    return df


def remove_outliers_iqr(df: pd.DataFrame,
                        cols: list[str],
                        factor: float = 1.5) -> pd.DataFrame:
    """Remove rows whose values fall outside [Q1 - f*IQR, Q3 + f*IQR]."""
    before = len(df)
    for col in cols:
        if col not in df.columns:
            continue
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        lo, hi = q1 - factor * iqr, q3 + factor * iqr
        df = df[(df[col] >= lo) & (df[col] <= hi)]
    log.info("Outliers removed     : %d rows removed via IQR", before - len(df))
    return df


def enforce_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Cast columns to appropriate dtypes."""
    df["employee_id"]  = df["employee_id"].astype(int)
    df["age"]          = df["age"].astype(int)
    df["performance"]  = df["performance"].astype(int)
    df["salary"]       = df["salary"].round(2)
    df["sales_amount"] = df["sales_amount"].round(2)
    df["years_exp"]    = df["years_exp"].round(1)
    log.info("Dtypes enforced.")
    return df


# ══════════════════════════════════════════════════════════════════
#  Main pipeline
# ══════════════════════════════════════════════════════════════════

def clean_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    df = drop_duplicates(df)
    df = standardise_text(df)
    df = parse_dates(df)
    df = validate_emails(df)
    df = handle_missing(df)
    df = remove_outliers_iqr(df, cols=["salary", "age", "sales_amount"])
    df = enforce_dtypes(df)
    df = df.reset_index(drop=True)
    return df


def main():
    print("=" * 55)
    print("  Stage 2 -- Cleaning raw dataset")
    print("=" * 55)

    log.info("Reading raw data from: %s", INPUT)
    df_raw = pd.read_csv(INPUT)
    log.info("Raw shape            : %s", df_raw.shape)

    df_clean = clean_pipeline(df_raw.copy())

    df_clean.to_csv(OUTPUT, index=False)
    log.info("Clean data saved  -> %s", OUTPUT)
    print(f"\n[OK]  Cleaned data saved -> {OUTPUT}")
    print(f"   Rows : {len(df_clean):,}   |   Columns : {df_clean.shape[1]}")
    print(f"   Nulls remaining: {df_clean.isnull().sum().sum():,}")


if __name__ == "__main__":
    main()
