"""
Stage 1 — Data Generation
Generates a realistic but intentionally messy random dataset (employees/sales).
Introduces nulls, duplicates, formatting inconsistencies, and outliers
so the cleaning stage has real work to do.
"""

import random
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# ── reproducibility ──────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ── output path ──────────────────────────────────────────────────
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = RAW_DIR / "raw_data.csv"

# ── helpers ──────────────────────────────────────────────────────
DEPARTMENTS   = ["Sales", "Engineering", "HR", "Marketing", "Finance", "SALES", "sales"]
CITIES        = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
                 "new york", "LOS ANGELES", "  Chicago  "]
GENDERS       = ["Male", "Female", "M", "F", "male", "female", None]

def random_date(start_year: int = 2018, end_year: int = 2024) -> str:
    """Return a random date string in a mixed format."""
    start = datetime(start_year, 1, 1)
    end   = datetime(end_year, 12, 31)
    delta = end - start
    rand_days = random.randint(0, delta.days)
    date = start + timedelta(days=rand_days)
    # Mix date formats deliberately
    fmt = random.choice(["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%B %d, %Y"])
    return date.strftime(fmt)

def random_salary() -> float:
    """Salary with occasional outliers."""
    base = np.random.normal(loc=65_000, scale=15_000)
    if random.random() < 0.05:          # 5 % extreme outliers
        base = random.choice([5, 1_000_000, -3_000])
    return round(base, 2)

def random_age() -> float | None:
    """Age with some invalids and nulls."""
    if random.random() < 0.07:
        return None
    age = int(np.random.normal(loc=38, scale=10))
    if random.random() < 0.04:
        age = random.choice([-5, 0, 150, 200])   # impossible ages
    return age

def random_email(name: str) -> str | None:
    """Email — sometimes malformed or missing."""
    if random.random() < 0.08:
        return None
    slug = name.lower().replace(" ", ".")
    domain = random.choice(["gmail.com", "yahoo.com", "company.org",
                             "outlook.com", "GMAIL.COM"])
    if random.random() < 0.06:
        return slug + "@"   # malformed
    return f"{slug}@{domain}"

# ── main generation ──────────────────────────────────────────────
def generate_dataset(n: int = 500) -> pd.DataFrame:
    first_names = ["Alice", "Bob", "Charlie", "Diana", "Evan", "Fiona",
                   "George", "Hannah", "Ivan", "Julia", "Kevin", "Laura",
                   "Mike", "Nancy", "Oscar", "Pam", "Quinn", "Rachel",
                   "Sam", "Tina", "Uma", "Victor", "Wendy", "Xander",
                   "Yara", "Zane"]
    last_names  = ["Smith", "Johnson", "Williams", "Jones", "Brown",
                   "Davis", "Miller", "Wilson", "Moore", "Taylor",
                   "Anderson", "Thomas", "Jackson", "White", "Harris"]

    records = []
    for i in range(1, n + 1):
        first = random.choice(first_names)
        last  = random.choice(last_names)
        name  = f"{first} {last}"

        record = {
            "employee_id":  i,
            "name":         name if random.random() > 0.03 else None,
            "age":          random_age(),
            "gender":       random.choice(GENDERS),
            "email":        random_email(name),
            "department":   random.choice(DEPARTMENTS),
            "city":         random.choice(CITIES),
            "salary":       random_salary() if random.random() > 0.04 else None,
            "hire_date":    random_date(),
            "years_exp":    round(random.uniform(0, 30), 1) if random.random() > 0.05 else None,
            "performance":  random.choice([1, 2, 3, 4, 5, None]),
            "sales_amount": round(np.random.exponential(scale=20_000), 2)
                            if random.random() > 0.06 else None,
        }
        records.append(record)

    df = pd.DataFrame(records)

    # Inject duplicates (~4 %)
    dup_count = int(n * 0.04)
    duplicates = df.sample(dup_count, random_state=SEED)
    df = pd.concat([df, duplicates], ignore_index=True)

    return df


def main():
    print("=" * 55)
    print("  Stage 1 -- Generating raw dataset")
    print("=" * 55)
    df = generate_dataset(n=500)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"[OK]  Raw data saved  -> {OUTPUT_FILE}")
    print(f"   Rows : {len(df):,}   |   Columns : {df.shape[1]}")
    print(f"   Nulls: {df.isnull().sum().sum():,}")
    print(f"   Dupes: {df.duplicated().sum():,}")


if __name__ == "__main__":
    main()
