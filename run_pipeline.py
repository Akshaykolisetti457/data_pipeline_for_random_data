"""
run_pipeline.py — Orchestrator
Runs all three stages in order:
  1. generate_data.py
  2. clean_data.py
  3. process_data.py
"""

import sys
import time
import importlib
from pathlib import Path

# Make sure src/ is on the path
SRC = Path(__file__).parent / "src"
sys.path.insert(0, str(SRC))


def run_stage(module_name: str, stage_label: str) -> None:
    print("\n" + "-" * 55)
    print(f"  >> {stage_label}")
    print("-" * 55)
    t0 = time.perf_counter()
    mod = importlib.import_module(module_name)
    mod.main()
    elapsed = time.perf_counter() - t0
    print(f"  [OK] {stage_label} completed in {elapsed:.2f}s")


def main():
    print("\n" + "=" * 55)
    print("  DATA PIPELINE -- Full Run")
    print("=" * 55)

    total_start = time.perf_counter()

    run_stage("generate_data", "Stage 1 -- Data Generation")
    run_stage("clean_data",    "Stage 2 -- Data Cleaning")
    run_stage("process_data",  "Stage 3 -- Data Processing")

    total = time.perf_counter() - total_start
    print("\n" + "=" * 55)
    print(f"  [OK]  Pipeline finished in {total:.2f}s")
    print("  Outputs:")
    print("    data/raw/raw_data.csv")
    print("    data/cleaned/cleaned_data.csv")
    print("    data/processed/processed_data.csv")
    print("    data/processed/dept_summary.csv")
    print("    data/processed/company_kpis.json")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
