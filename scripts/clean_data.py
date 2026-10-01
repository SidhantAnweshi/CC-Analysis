"""
clean_data.py
---
Cleans raw datasets and engineers features required by EDA,
segmentation, profitability, and offer-analysis notebooks.

Outputs (data/processed/):
    customers_clean.csv
    transactions_clean.csv
    customer_summary.csv   – per-customer aggregated metrics + profitability
    monthly_trends.csv
    category_summary.csv
"""

import os
import numpy as np
import pandas as pd

# --- Paths ---
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR    = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR   = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROC_DIR, exist_ok=True)

# --- Service cost per customer (monthly, INR) ---
SERVICE_COST_PM = {"Classic": 30, "Gold": 55, "Platinum": 90, "Signature": 150}
ANNUAL_FEE      = {"Classic": 500, "Gold": 1500, "Platinum": 3000, "Signature": 7500}
ANALYSIS_MONTHS = 24  # Jan 2023 – Dec 2024


def load_raw():
    print("Loading raw data ...")
    cust  = pd.read_csv(os.path.join(RAW_DIR, "customers.csv"))
    txn   = pd.read_csv(os.path.join(RAW_DIR, "transactions.csv"),
                        parse_dates=["txn_date"])
    camps = pd.read_csv(os.path.join(RAW_DIR, "campaigns.csv"))
    asgn  = pd.read_csv(os.path.join(RAW_DIR, "campaign_assignments.csv"))
    return cust, txn, camps, asgn


# --- STEP 1: Clean customers ---
def clean_customers(cust: pd.DataFrame) -> pd.DataFrame:
    print("Cleaning customers ...")
    cust = cust.drop_duplicates(subset=["customer_id"])
    cust = cust.dropna(subset=["customer_id", "card_type"])
    cust["credit_limit"] = cust["credit_limit"].clip(lower=0)
    cust["tenure_months"] = cust["tenure_months"].clip(lower=1)
    return cust


# --- STEP 2: Clean transactions ---
def clean_transactions(txn: pd.DataFrame) -> pd.DataFrame:
    print("Cleaning transactions ...")
    txn = txn.drop_duplicates(subset=["txn_id"])
    txn = txn.dropna(subset=["txn_id", "customer_id", "txn_date", "amount"])

    # Remove declined transactions from spend analysis (keep flag for decline rate KPI)
    txn_valid = txn[txn["is_declined"] == 0].copy()

    # Outlier capping: cap amount at 99.5th percentile
    cap = txn_valid["amount"].quantile(0.995)
    txn_valid["amount"] = txn_valid["amount"].clip(upper=cap)
    txn_valid["cashback_amt"] = txn_valid["amount"] * txn_valid["cashback_pct"]
    txn_valid["interchange_revenue"] = txn_valid["amount"] * txn_valid.apply(
        lambda r: {"Classic": 0.013, "Gold": 0.015, "Platinum": 0.018,
                   "Signature": 0.022}[r["card_type"]], axis=1
    )

    # Time features
    txn_valid["year"]    = txn_valid["txn_date"].dt.year
    txn_valid["month"]   = txn_valid["txn_date"].dt.month
    txn_valid["quarter"] = txn_valid["txn_date"].dt.quarter
    txn_valid["year_month"] = txn_valid["txn_date"].dt.to_period("M").astype(str)
    txn_valid["day_of_week"] = txn_valid["txn_date"].dt.day_name()

    print(f"  Valid transactions after cleaning: {len(txn_valid):,}")
    return txn_valid


# --- STEP 3: RFM + customer summary ---
def build_customer_summary(
    cust: pd.DataFrame, txn: pd.DataFrame
) -> pd.DataFrame:
    print("Building customer summary with RFM & profitability ...")

    REFERENCE_DATE = pd.Timestamp("2025-01-01")

    # Aggregate per customer
    agg = txn.groupby("customer_id").agg(
        total_spend          = ("amount",              "sum"),
        total_cashback_cost  = ("cashback_amt",        "sum"),
        total_interchange    = ("interchange_revenue", "sum"),
        txn_count            = ("txn_id",              "count"),
        last_txn_date        = ("txn_date",            "max"),
        first_txn_date       = ("txn_date",            "min"),
        avg_txn_amount       = ("amount",              "mean"),
        unique_categories    = ("category",            "nunique"),
        unique_channels      = ("channel",             "nunique"),
    ).reset_index()

    agg["recency_days"]  = (REFERENCE_DATE - agg["last_txn_date"]).dt.days
    agg["active_months"] = (
        (agg["last_txn_date"] - agg["first_txn_date"]).dt.days / 30
    ).clip(lower=1).round(1)

    # Merge customer demographics
    df = cust.merge(agg, on="customer_id", how="left")
    df["total_spend"]         = df["total_spend"].fillna(0)
    df["total_cashback_cost"] = df["total_cashback_cost"].fillna(0)
    df["total_interchange"]   = df["total_interchange"].fillna(0)
    df["txn_count"]           = df["txn_count"].fillna(0).astype(int)
    df["recency_days"]        = df["recency_days"].fillna(999).astype(int)

    # Annual fee revenue (total over analysis period)
    df["annual_fee_revenue"] = df["card_type"].map(ANNUAL_FEE) * (ANALYSIS_MONTHS / 12)

    # Service cost (monthly × 24 months)
    df["total_service_cost"] = df["card_type"].map(SERVICE_COST_PM) * ANALYSIS_MONTHS

    # Gross profit
    df["gross_revenue"] = df["total_interchange"] + df["annual_fee_revenue"]
    df["total_cost"]    = df["total_cashback_cost"] + df["total_service_cost"]
    df["net_profit"]    = df["gross_revenue"] - df["total_cost"]
    df["profit_margin_pct"] = np.where(
        df["gross_revenue"] > 0,
        (df["net_profit"] / df["gross_revenue"]) * 100,
        0
    ).round(2)

    # --- RFM Scoring (1–4 quartile, 4 = best) ---
    # Recency: lower days = better
    df["R_score"] = pd.qcut(df["recency_days"], 4, labels=[4, 3, 2, 1]).astype(int)
    # Frequency
    df["F_score"] = pd.qcut(df["txn_count"].rank(method="first"), 4,
                            labels=[1, 2, 3, 4]).astype(int)
    # Monetary
    df["M_score"] = pd.qcut(df["total_spend"].rank(method="first"), 4,
                            labels=[1, 2, 3, 4]).astype(int)
    df["RFM_score"] = df["R_score"] + df["F_score"] + df["M_score"]

    # --- Segment labels ---
    def segment(row):
        s = row["RFM_score"]
        if s >= 10:
            return "Champion"
        elif s >= 7:
            return "Loyal"
        elif s >= 4:
            return "At-Risk"
        else:
            return "Dormant"

    df["segment"] = df.apply(segment, axis=1)

    return df.round({"total_spend": 2, "total_cashback_cost": 2,
                     "total_interchange": 2, "gross_revenue": 2,
                     "total_cost": 2, "net_profit": 2})


# --- STEP 4: Monthly aggregation ---
def build_monthly_trends(txn: pd.DataFrame) -> pd.DataFrame:
    print("Building monthly trends ...")
    m = txn.groupby("year_month").agg(
        total_spend      = ("amount",              "sum"),
        total_cashback   = ("cashback_amt",        "sum"),
        interchange_rev  = ("interchange_revenue", "sum"),
        txn_count        = ("txn_id",              "count"),
        active_customers = ("customer_id",         "nunique"),
        avg_txn_amount   = ("amount",              "mean"),
    ).reset_index().sort_values("year_month")
    m["net_revenue"] = m["interchange_rev"] - m["total_cashback"]
    return m.round(2)


# --- STEP 5: Category summary ---
def build_category_summary(txn: pd.DataFrame) -> pd.DataFrame:
    print("Building category summary ...")
    c = txn.groupby("category").agg(
        total_spend     = ("amount",              "sum"),
        total_cashback  = ("cashback_amt",        "sum"),
        interchange_rev = ("interchange_revenue", "sum"),
        txn_count       = ("txn_id",              "count"),
        avg_txn_amount  = ("amount",              "mean"),
        customers       = ("customer_id",         "nunique"),
    ).reset_index()
    c["cashback_pct_of_spend"] = (c["total_cashback"] / c["total_spend"] * 100).round(2)
    c["net_revenue"]           = (c["interchange_rev"] - c["total_cashback"]).round(2)
    return c.round(2)


# --- MAIN ---
def main():
    cust, txn, camps, asgn = load_raw()

    cust_clean = clean_customers(cust)
    txn_clean  = clean_transactions(txn)
    cust_sum   = build_customer_summary(cust_clean, txn_clean)
    monthly    = build_monthly_trends(txn_clean)
    category   = build_category_summary(txn_clean)

    cust_clean.to_csv(os.path.join(PROC_DIR, "customers_clean.csv"),      index=False)
    txn_clean.to_csv(os.path.join(PROC_DIR,  "transactions_clean.csv"),   index=False)
    cust_sum.to_csv(os.path.join(PROC_DIR,   "customer_summary.csv"),     index=False)
    monthly.to_csv(os.path.join(PROC_DIR,    "monthly_trends.csv"),       index=False)
    category.to_csv(os.path.join(PROC_DIR,   "category_summary.csv"),     index=False)

    print("\n[OK] Cleaning & feature engineering complete!")
    print(f"   Customer summary rows : {len(cust_sum):,}")
    print(f"   Monthly trend rows    : {len(monthly):,}")
    print(f"   Category rows         : {len(category):,}")
    print(f"\nFiles saved to: {PROC_DIR}")


if __name__ == "__main__":
    main()
