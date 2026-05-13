# 🚀 Data Pipeline — Pipeline 1

A **three-stage Python data pipeline** that generates random employee/sales data,
cleans it thoroughly, and then processes it into analysis-ready outputs including
feature-engineered datasets, department summaries, and company-wide KPIs.

---

## 📁 Project Structure

```
pipeline_1/
│
├── run_pipeline.py          ← Orchestrator (run this to execute all stages)
├── requirements.txt         ← Python dependencies
│
├── src/
│   ├── generate_data.py     ← Stage 1: Generate messy random data
│   ├── clean_data.py        ← Stage 2: Clean and validate the raw data
│   └── process_data.py      ← Stage 3: Process and enrich clean data
│
└── data/
    ├── raw/
    │   └── raw_data.csv             ← Output of Stage 1
    ├── cleaned/
    │   └── cleaned_data.csv         ← Output of Stage 2
    └── processed/
        ├── processed_data.csv       ← Full enriched & encoded dataset
        ├── dept_summary.csv         ← Department-level KPI rollup
        └── company_kpis.json        ← Scalar company-wide metrics
```

---

## ⚙️ Prerequisites

- **Python 3.11+**
- pip

---

## 🛠️ Setup

```bash
# 1. Navigate to the project directory
cd path/to/pipeline_1

# 2. (Optional but recommended) Create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

---

## ▶️ Running the Pipeline

### Run all 3 stages at once (recommended)

```bash
python run_pipeline.py
```

### Run individual stages

```bash
python src/generate_data.py   # Stage 1 only
python src/clean_data.py      # Stage 2 only
python src/process_data.py    # Stage 3 only
```

> **Note:** Stages must be run in order (1 → 2 → 3), as each stage consumes
> the output of the previous one.

---

## 📋 Pipeline Stages — Detailed Explanation

---

### Stage 1 — Data Generation (`generate_data.py`)

**Purpose:** Create a realistic but intentionally messy dataset that simulates
real-world data quality issues.

**What it does:**

| Action | Detail |
|---|---|
| Generates 500 employee records | Random names, ages, departments, cities, salaries, hire dates |
| Injects **null values** | ~4–8 % per column, randomly distributed |
| Injects **duplicates** | ~4 % of rows are duplicated |
| Adds **inconsistent casing** | e.g. `"Sales"`, `"SALES"`, `"sales"` for the same department |
| Adds **mixed date formats** | e.g. `2021-03-15`, `15/03/2021`, `March 15, 2021` |
| Adds **malformed emails** | e.g. `alice@` (missing domain) |
| Adds **statistical outliers** | Salaries like `$5`, `-$3,000`, `$1,000,000` |
| Adds **impossible ages** | e.g. `-5`, `0`, `150`, `200` |

**Output:** `data/raw/raw_data.csv` — ~520 rows × 12 columns

**Columns generated:**

| Column | Type | Description |
|---|---|---|
| `employee_id` | int | Unique identifier |
| `name` | str | Employee full name |
| `age` | float | Age in years (with nulls/outliers) |
| `gender` | str | M/F/Male/Female (inconsistent) |
| `email` | str | Email address (some malformed) |
| `department` | str | Department (mixed case) |
| `city` | str | City (mixed case/whitespace) |
| `salary` | float | Annual salary USD (with outliers) |
| `hire_date` | str | Date of hire (mixed formats) |
| `years_exp` | float | Years of experience |
| `performance` | int | Rating 1–5 (with nulls) |
| `sales_amount` | float | Total sales generated |

---

### Stage 2 — Data Cleaning (`clean_data.py`)

**Purpose:** Apply a systematic, step-by-step cleaning pipeline to transform
raw messy data into a consistent, reliable dataset.

**Cleaning steps (in order):**

#### Step 1 — Drop Duplicate Rows
Removes all rows that are exact duplicates across all columns.

```
Before: ~520 rows
After:  ~500 rows
```

#### Step 2 — Standardise Text Fields
- Strips leading/trailing whitespace from `name`, `department`, `city`, `gender`
- Applies **Title Case** (e.g. `"SALES"` → `"Sales"`, `"  Chicago  "` → `"Chicago"`)
- Normalises gender abbreviations: `"M"` → `"Male"`, `"F"` → `"Female"`

#### Step 3 — Parse & Unify Mixed Date Formats
Uses `python-dateutil` to intelligently parse all date formats and convert them
to a single standard: **`YYYY-MM-DD`** (ISO 8601).

```
"15/03/2021"      →  2021-03-15
"March 15, 2021"  →  2021-03-15
"03-15-2021"      →  2021-03-15
```
Unparseable dates are set to `NaT`.

#### Step 4 — Validate Email Addresses
Validates each email against the regex pattern:
```
^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$
```
Malformed entries (e.g. `alice@`, missing domain) are set to `null`.

#### Step 5 — Handle Missing Values

| Column | Strategy | Reason |
|---|---|---|
| `name` | **Drop row** | Can't identify the record without a name |
| `age`, `salary`, `years_exp`, `sales_amount` | **Impute with median** | Robust to remaining outliers |
| `gender`, `department`, `city`, `performance` | **Impute with mode** | Most frequent category is most likely |

#### Step 6 — Remove Statistical Outliers (IQR Method)
For `salary`, `age`, and `sales_amount`:
- Compute **Q1** (25th percentile) and **Q3** (75th percentile)
- Calculate **IQR** = Q3 − Q1
- Remove rows where value < Q1 − 1.5×IQR or > Q3 + 1.5×IQR

This eliminates entries like salary = $5 or age = 200.

#### Step 7 — Enforce Correct Data Types
Casts columns to their proper dtypes:
- `employee_id` → `int`
- `age` → `int`
- `performance` → `int`
- `salary`, `sales_amount` → `float` (rounded to 2 dp)
- `hire_date` → `datetime`

**Output:** `data/cleaned/cleaned_data.csv` — ~450–470 rows × 12 columns, 0 nulls

---

### Stage 3 — Data Processing (`process_data.py`)

**Purpose:** Transform clean data into an analysis-ready, enriched dataset with
new features, statistical summaries, and normalised values.

**Processing steps:**

#### Step 1 — Feature Engineering
Creates 7 new derived columns:

| New Column | Description | Example |
|---|---|---|
| `seniority_band` | Experience bucketed | `"Senior"` (7–14 yrs) |
| `salary_band` | Salary quintile label | `"High"` |
| `age_group` | Decade group | `"30s"` |
| `exp_salary_ratio` | years_exp ÷ salary | `0.000231` |
| `hire_year` | Extracted from hire_date | `2021` |
| `hire_month` | Extracted from hire_date | `3` |

#### Step 2 — Department-Level Aggregations
Computes a rollup table (`dept_summary.csv`) per department:

| Metric | Description |
|---|---|
| `headcount` | Number of employees |
| `avg_salary` | Mean salary |
| `median_salary` | Median salary |
| `avg_age` | Mean age |
| `avg_performance` | Mean performance score |
| `avg_years_exp` | Mean years of experience |
| `total_sales` | Sum of all sales amounts |

#### Step 3 — Company-Wide KPIs
Calculates scalar metrics saved to `company_kpis.json`:

```json
{
  "total_employees": 462,
  "avg_salary_usd": 64832.15,
  "median_salary_usd": 63500.00,
  "avg_age_years": 38.4,
  "avg_years_experience": 14.9,
  "top_performer_pct": 41.56,
  "total_sales_usd": 9245831.42,
  "most_common_department": "Engineering",
  "most_common_city": "New York",
  "hire_year_range": "2018–2024"
}
```

#### Step 4 — Feature Normalisation (MinMax Scaling)
Scales `salary`, `sales_amount`, `years_exp` to the **[0, 1]** range using
`scikit-learn`'s `MinMaxScaler`. New columns are named with the `_norm` suffix
(e.g. `salary_norm`). This makes the dataset ML-ready.

#### Step 5 — Categorical Encoding (One-Hot Encoding)
Applies `pd.get_dummies()` to `department`, `city`, and `gender`, creating
binary indicator columns (e.g. `department_Engineering`, `city_New York`).
`performance` is already ordinal (1–5) and is kept as-is.

**Outputs:**
- `data/processed/processed_data.csv` — Full enriched & encoded dataset
- `data/processed/dept_summary.csv` — Department KPI rollup
- `data/processed/company_kpis.json` — Scalar company metrics

---

## 🔄 Pipeline Data Flow

```
                ┌──────────────────────┐
                │   generate_data.py   │  Stage 1
                │  500 records + noise │
                └──────────┬───────────┘
                           │  raw_data.csv
                           ▼
                ┌──────────────────────┐
                │    clean_data.py     │  Stage 2
                │  7-step cleaning     │
                └──────────┬───────────┘
                           │  cleaned_data.csv
                           ▼
                ┌──────────────────────────────────┐
                │         process_data.py          │  Stage 3
                │  Features │ Aggregations │ KPIs  │
                │  Normalize │ Encode              │
                └──────┬───────────┬───────────────┘
                       │           │
          processed_data.csv    dept_summary.csv
                                company_kpis.json
```

---

## 🧪 Example Output Snippet

### `dept_summary.csv`

| department | headcount | avg_salary | avg_performance | total_sales |
|---|---|---|---|---|
| Engineering | 87 | 67,241.32 | 3.12 | 1,842,310.55 |
| Sales | 80 | 63,102.88 | 3.21 | 1,720,445.10 |
| Marketing | 75 | 61,540.72 | 3.08 | 1,601,232.80 |

### `company_kpis.json`

```json
{
  "total_employees": 462,
  "avg_salary_usd": 64832.15,
  "top_performer_pct": 41.56,
  "hire_year_range": "2018–2024"
}
```

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `pandas` | Core data manipulation |
| `numpy` | Numeric operations & random generation |
| `scikit-learn` | MinMaxScaler for normalisation |
| `python-dateutil` | Parsing mixed date formats |

Install all at once:
```bash
pip install -r requirements.txt
```

---

## 🧩 Extending the Pipeline

You can easily extend this pipeline by:

- **Adding new data sources** — modify `generate_data.py` or swap it for a real
  CSV/database reader
- **Adding more cleaning rules** — create a new function in `clean_data.py` and
  add it to `clean_pipeline()`
- **Adding new features** — extend `engineer_features()` in `process_data.py`
- **Connecting to a database** — replace CSV saves with `df.to_sql()` calls
- **Scheduling** — wrap `run_pipeline.py` with a scheduler like `APScheduler`
  or Windows Task Scheduler

---

## 📄 License

This project is for educational purposes.
