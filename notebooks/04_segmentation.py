"""
Notebook 04 — Customer Segmentation
Standalone script. All analysis also executed in run_pipeline.py.
"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR.endswith("notebooks"):
    BASE_DIR = os.path.dirname(BASE_DIR)

PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
FIG_DIR  = os.path.join(BASE_DIR, "outputs", "figures")

PALETTE = ["#1A3C5E","#2E86AB","#A23B72","#F18F01","#C73E1D",
           "#3B1F2B","#44BBA4","#E94F37","#393E41","#F5A623"]
sns.set_theme(style="whitegrid", palette=PALETTE, font_scale=1.1)

print("Loading customer summary ...")
cust = pd.read_csv(os.path.join(PROC_DIR, "customer_summary.csv"))

# ── Segment Counts ──────────────────────────────────────────────────────────────
print("\nSegment Distribution:")
print(cust["segment"].value_counts())

# ── Segment P&L Summary ────────────────────────────────────────────────────────
seg = cust.groupby("segment").agg(
    customers        = ("customer_id", "count"),
    avg_spend        = ("total_spend",  "mean"),
    avg_profit       = ("net_profit",   "mean"),
    total_profit     = ("net_profit",   "sum"),
    avg_recency      = ("recency_days", "mean"),
    avg_txn_count    = ("txn_count",    "mean"),
).round(2)
print("\nSegment P&L:")
print(seg.to_string())

# ── Card Type × Segment crosstab ───────────────────────────────────────────────
print("\nCard Type Distribution per Segment:")
print(pd.crosstab(cust["segment"], cust["card_type"]))

# ── Income Band × Segment ──────────────────────────────────────────────────────
print("\nIncome Band vs Segment:")
print(pd.crosstab(cust["segment"], cust["income_band"], normalize="index").round(2))

# ── Plot: Profit by Segment & Card Type (grouped) ─────────────────────────────
pivot = cust.pivot_table(values="net_profit", index="segment",
                         columns="card_type", aggfunc="mean")
pivot.plot(kind="bar", figsize=(11, 5), color=PALETTE[:4])
plt.title("Avg Net Profit per Customer: Segment x Card Type")
plt.ylabel("Avg Net Profit (Rs.)")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "s04_segment_cardtype_bar.png"), dpi=150)
plt.close()
print("\n[+] Saved segment x card type bar chart")
