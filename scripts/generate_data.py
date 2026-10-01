"""
generate_data.py
----------------
Generates all synthetic datasets for the Credit Card Spend & Cashback
Profitability Analysis project.

Outputs (data/raw/):
    customers.csv          - 20,000 customers with demographics
    transactions.csv       - 500,000+ transactions
    cashback_rules.csv     - cashback % by card type & category
    campaigns.csv          - 5 marketing campaigns
    campaign_assignments.csv - customer <-> campaign mapping
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ── Reproducibility ────────────────────────────────────────────────────────────
SEED = 42
np.random.seed(SEED)
random.seed(SEED)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR  = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

# ── Constants ──────────────────────────────────────────────────────────────────
N_CUSTOMERS    = 20_000
N_TRANSACTIONS = 500_000
START_DATE     = datetime(2023, 1, 1)
END_DATE       = datetime(2024, 12, 31)
DATE_RANGE_DAYS = (END_DATE - START_DATE).days

CARD_TYPES     = ["Classic", "Gold", "Platinum", "Signature"]
CARD_WEIGHTS   = [0.40, 0.30, 0.20, 0.10]

CATEGORIES     = [
    "Groceries", "Dining", "Travel", "Fuel", "Entertainment",
    "Shopping", "Utilities", "Healthcare", "Education", "Others"
]
CAT_WEIGHTS    = [0.22, 0.15, 0.08, 0.10, 0.07,
                  0.16, 0.08, 0.06, 0.03, 0.05]

CHANNELS       = ["Online", "POS", "Contactless", "ATM"]
CHAN_WEIGHTS   = [0.35, 0.40, 0.20, 0.05]

CITY_TIERS     = ["Tier 1", "Tier 2", "Tier 3"]
CITY_W         = [0.45, 0.35, 0.20]

GENDERS        = ["Male", "Female", "Other"]
GENDER_W       = [0.52, 0.46, 0.02]

INCOME_BANDS   = ["Low (<3L)", "Mid (3-8L)", "High (8-20L)", "Premium (>20L)"]
INCOME_W       = [0.20, 0.40, 0.30, 0.10]

OCCUPATION     = ["Salaried", "Self-Employed", "Student", "Retired"]
OCC_W          = [0.55, 0.25, 0.12, 0.08]

# Cashback % matrix  {card_type: {category: cashback_pct}}
CASHBACK_MATRIX = {
    "Classic":   {"Groceries": 0.005, "Dining": 0.005, "Travel": 0.005,
                  "Fuel": 0.005, "Entertainment": 0.005, "Shopping": 0.005,
                  "Utilities": 0.005, "Healthcare": 0.005, "Education": 0.005,
                  "Others": 0.005},
    "Gold":      {"Groceries": 0.010, "Dining": 0.015, "Travel": 0.010,
                  "Fuel": 0.010, "Entertainment": 0.010, "Shopping": 0.010,
                  "Utilities": 0.005, "Healthcare": 0.010, "Education": 0.005,
                  "Others": 0.005},
    "Platinum":  {"Groceries": 0.015, "Dining": 0.020, "Travel": 0.025,
                  "Fuel": 0.015, "Entertainment": 0.015, "Shopping": 0.015,
                  "Utilities": 0.010, "Healthcare": 0.015, "Education": 0.010,
                  "Others": 0.010},
    "Signature": {"Groceries": 0.020, "Dining": 0.030, "Travel": 0.040,
                  "Fuel": 0.020, "Entertainment": 0.020, "Shopping": 0.020,
                  "Utilities": 0.010, "Healthcare": 0.020, "Education": 0.010,
                  "Others": 0.015},
}

# Interchange rate (revenue) by card type
INTERCHANGE = {"Classic": 0.013, "Gold": 0.015, "Platinum": 0.018, "Signature": 0.022}

# Annual fee by card type (INR)
ANNUAL_FEE  = {"Classic": 500, "Gold": 1500, "Platinum": 3000, "Signature": 7500}

# Monthly service cost per customer (INR)
SERVICE_COST_PM = {"Classic": 30, "Gold": 55, "Platinum": 90, "Signature": 150}


# ── 1. CUSTOMERS ───────────────────────────────────────────────────────────────
def generate_customers() -> pd.DataFrame:
    print("Generating customers …")
    customer_ids = [f"C{str(i).zfill(6)}" for i in range(1, N_CUSTOMERS + 1)]

    ages = np.random.randint(21, 71, size=N_CUSTOMERS)

    # Assign income band correlated with age (older → more likely high income)
    income_bands = np.where(
        ages < 30, np.random.choice(INCOME_BANDS[:3], N_CUSTOMERS, p=[0.35, 0.50, 0.15]),
        np.where(ages < 50,
                 np.random.choice(INCOME_BANDS, N_CUSTOMERS, p=[0.10, 0.40, 0.35, 0.15]),
                 np.random.choice(INCOME_BANDS, N_CUSTOMERS, p=[0.10, 0.35, 0.35, 0.20]))
    )

    card_types  = np.random.choice(CARD_TYPES, N_CUSTOMERS, p=CARD_WEIGHTS)

    df = pd.DataFrame({
        "customer_id":   customer_ids,
        "age":           ages,
        "gender":        np.random.choice(GENDERS,      N_CUSTOMERS, p=GENDER_W),
        "city_tier":     np.random.choice(CITY_TIERS,   N_CUSTOMERS, p=CITY_W),
        "income_band":   income_bands,
        "occupation":    np.random.choice(OCCUPATION,   N_CUSTOMERS, p=OCC_W),
        "card_type":     card_types,
        "tenure_months": np.random.randint(1, 121, size=N_CUSTOMERS),  # 1–10 yrs
        "credit_limit":  np.where(
            card_types == "Classic",   np.random.randint(50_000,  200_000, N_CUSTOMERS),
            np.where(card_types == "Gold",
                     np.random.randint(100_000, 500_000, N_CUSTOMERS),
            np.where(card_types == "Platinum",
                     np.random.randint(300_000, 1_000_000, N_CUSTOMERS),
                     np.random.randint(500_000, 3_000_000, N_CUSTOMERS)))
        ),
        "annual_fee":    [ANNUAL_FEE[c] for c in card_types],
        "join_date":     [
            (START_DATE - timedelta(days=int(t * 30))).strftime("%Y-%m-%d")
            for t in np.random.randint(1, 121, size=N_CUSTOMERS)
        ],
    })
    return df


# ── 2. CASHBACK RULES ──────────────────────────────────────────────────────────
def generate_cashback_rules() -> pd.DataFrame:
    print("Generating cashback rules …")
    rows = []
    for card, cats in CASHBACK_MATRIX.items():
        for cat, pct in cats.items():
            rows.append({
                "card_type":       card,
                "category":        cat,
                "cashback_pct":    pct,
                "max_cashback_pm": {  # cap per month per customer (INR)
                    "Classic": 200, "Gold": 500, "Platinum": 1500, "Signature": 5000
                }[card],
            })
    return pd.DataFrame(rows)


# ── 3. TRANSACTIONS ────────────────────────────────────────────────────────────
def generate_transactions(customers: pd.DataFrame) -> pd.DataFrame:
    print("Generating 500,000+ transactions... (this may take a minute)")

    cust_ids  = customers["customer_id"].values
    cust_card = dict(zip(customers["customer_id"], customers["card_type"]))

    # Each customer gets a base activity level (drives transaction count)
    cust_activity = np.random.gamma(shape=2.5, scale=10, size=N_CUSTOMERS).clip(1, 80)
    cust_activity = dict(zip(cust_ids, cust_activity))

    # Build per-customer transaction counts summing to ≥ 500,000
    txn_counts = {c: max(1, int(cust_activity[c])) for c in cust_ids}
    total = sum(txn_counts.values())
    if total < 500_000:
        extra = 500_000 - total
        bonus_custs = np.random.choice(cust_ids, extra, replace=True)
        for c in bonus_custs:
            txn_counts[c] += 1

    # Build merchant names per category
    merchants = {
        "Groceries":     ["BigBasket", "DMart", "Reliance Fresh", "More Supermarket", "Star Bazaar"],
        "Dining":        ["Zomato", "Swiggy", "McDonald's", "Domino's", "Cafe Coffee Day"],
        "Travel":        ["MakeMyTrip", "IndiGo", "Air India", "IRCTC", "OYO Rooms"],
        "Fuel":          ["HPCL", "BPCL", "Indian Oil", "Shell", "Bharat Petroleum"],
        "Entertainment": ["BookMyShow", "Netflix", "Amazon Prime", "PVR Cinemas", "Hotstar"],
        "Shopping":      ["Amazon", "Flipkart", "Myntra", "Ajio", "Nykaa"],
        "Utilities":     ["BESCOM", "Airtel", "Jio", "BWSSB", "MSEDCL"],
        "Healthcare":    ["Apollo Pharmacy", "MedPlus", "Netmeds", "Practo", "1mg"],
        "Education":     ["BYJU'S", "Unacademy", "Coursera", "Udemy", "Vedantu"],
        "Others":        ["PayTM", "PhonePe", "BookAnywhere", "LocalStore", "Misc"],
    }

    txn_rows = []
    txn_id   = 1

    # Mean spend varies by category
    cat_mean_spend = {
        "Groceries": 2500, "Dining": 800, "Travel": 8000, "Fuel": 1500,
        "Entertainment": 500, "Shopping": 3000, "Utilities": 1200,
        "Healthcare": 1500, "Education": 4000, "Others": 600,
    }

    for cust_id in cust_ids:
        card  = cust_card[cust_id]
        n     = txn_counts[cust_id]
        cats  = np.random.choice(CATEGORIES, n, p=CAT_WEIGHTS)
        chans = np.random.choice(CHANNELS,   n, p=CHAN_WEIGHTS)

        # Random dates across the 2-year window, slightly clustered (weekend effect)
        raw_days = np.random.randint(0, DATE_RANGE_DAYS, n)
        dates    = [START_DATE + timedelta(days=int(d)) for d in raw_days]

        for i in range(n):
            cat      = cats[i]
            mean_amt = cat_mean_spend[cat]
            amount   = round(abs(np.random.lognormal(
                mean=np.log(mean_amt) - 0.5 * 0.6**2, sigma=0.6
            )), 2)
            amount   = max(10.0, min(amount, 500_000.0))

            cb_pct   = CASHBACK_MATRIX[card][cat]
            cashback = round(amount * cb_pct, 2)

            txn_rows.append({
                "txn_id":        f"T{str(txn_id).zfill(8)}",
                "customer_id":   cust_id,
                "card_type":     card,
                "txn_date":      dates[i].strftime("%Y-%m-%d"),
                "amount":        amount,
                "category":      cat,
                "channel":       chans[i],
                "merchant":      random.choice(merchants[cat]),
                "cashback_pct":  cb_pct,
                "cashback_amt":  cashback,
                "interchange_revenue": round(amount * INTERCHANGE[card], 2),
                "is_declined":   int(np.random.random() < 0.02),  # 2% decline rate
            })
            txn_id += 1

    df = pd.DataFrame(txn_rows)
    df["txn_date"] = pd.to_datetime(df["txn_date"])
    return df


# ── 4. CAMPAIGNS ───────────────────────────────────────────────────────────────
def generate_campaigns() -> pd.DataFrame:
    print("Generating campaigns …")
    campaigns = [
        {"campaign_id": "CP001", "campaign_name": "New Year Dining Boost",
         "target_category": "Dining",   "start_date": "2023-01-01",
         "end_date": "2023-01-31", "bonus_cashback_pct": 0.05,
         "campaign_cost_inr": 500_000,  "target_card": "Gold"},
        {"campaign_id": "CP002", "campaign_name": "Travel Season Offer",
         "target_category": "Travel",   "start_date": "2023-05-01",
         "end_date": "2023-06-30", "bonus_cashback_pct": 0.04,
         "campaign_cost_inr": 800_000,  "target_card": "Platinum"},
        {"campaign_id": "CP003", "campaign_name": "Festive Shopping Cashback",
         "target_category": "Shopping", "start_date": "2023-10-01",
         "end_date": "2023-10-31", "bonus_cashback_pct": 0.03,
         "campaign_cost_inr": 1_200_000, "target_card": "All"},
        {"campaign_id": "CP004", "campaign_name": "Fuel Saver Program",
         "target_category": "Fuel",     "start_date": "2024-04-01",
         "end_date": "2024-06-30", "bonus_cashback_pct": 0.025,
         "campaign_cost_inr": 400_000,  "target_card": "Classic"},
        {"campaign_id": "CP005", "campaign_name": "Premium Dining Rewards",
         "target_category": "Dining",   "start_date": "2024-09-01",
         "end_date": "2024-10-31", "bonus_cashback_pct": 0.06,
         "campaign_cost_inr": 750_000,  "target_card": "Signature"},
    ]
    return pd.DataFrame(campaigns)


def generate_campaign_assignments(
    customers: pd.DataFrame, campaigns: pd.DataFrame
) -> pd.DataFrame:
    print("Generating campaign assignments …")
    rows = []
    for _, camp in campaigns.iterrows():
        if camp["target_card"] == "All":
            eligible = customers["customer_id"].values
        else:
            eligible = customers.loc[
                customers["card_type"] == camp["target_card"], "customer_id"
            ].values

        # Assign ~40% of eligible customers to campaign
        n_assign = max(1, int(len(eligible) * 0.40))
        assigned = np.random.choice(eligible, n_assign, replace=False)
        for cust in assigned:
            rows.append({
                "campaign_id":  camp["campaign_id"],
                "customer_id":  cust,
                "enrolled_date": camp["start_date"],
                "redeemed":     int(np.random.random() < 0.65),  # 65% redeem rate
            })
    return pd.DataFrame(rows)


# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    customers    = generate_customers()
    cashback_rules = generate_cashback_rules()
    transactions = generate_transactions(customers)
    campaigns    = generate_campaigns()
    assignments  = generate_campaign_assignments(customers, campaigns)

    customers.to_csv(os.path.join(RAW_DIR, "customers.csv"),           index=False)
    cashback_rules.to_csv(os.path.join(RAW_DIR, "cashback_rules.csv"), index=False)
    transactions.to_csv(os.path.join(RAW_DIR, "transactions.csv"),     index=False)
    campaigns.to_csv(os.path.join(RAW_DIR, "campaigns.csv"),           index=False)
    assignments.to_csv(os.path.join(RAW_DIR, "campaign_assignments.csv"), index=False)

    print("\n[OK] Data generation complete!")
    print(f"   Customers:    {len(customers):,}")
    print(f"   Transactions: {len(transactions):,}")
    print(f"   Campaigns:    {len(campaigns)}")
    print(f"   Assignments:  {len(assignments):,}")
    print(f"\nFiles saved to: {RAW_DIR}")


if __name__ == "__main__":
    main()
