"""
run_pipeline.py
---
Master pipeline runner.
Executes in order:
  1. Data generation
  2. Data cleaning & feature engineering
  3. EDA plots
  4. Segmentation analysis
  5. Profitability analysis
  6. Offer/campaign analysis
  7. Power BI CSV exports
  8. Excel workbook generation
  9. Prints actual KPIs → used for README & resume bullets
"""

import os, sys

# Ensure scripts/ is importable regardless of CWD
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR    = os.path.dirname(SCRIPTS_DIR)
sys.path.insert(0, SCRIPTS_DIR)

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# --- Paths ---
RAW_DIR   = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR  = os.path.join(BASE_DIR, "data", "processed")
FIG_DIR   = os.path.join(BASE_DIR, "outputs", "figures")
PBI_DIR   = os.path.join(BASE_DIR, "outputs", "powerbi")
XLS_DIR   = os.path.join(BASE_DIR, "outputs", "excel")
for d in [FIG_DIR, PBI_DIR, XLS_DIR]: os.makedirs(d, exist_ok=True)

# --- Style ---
PALETTE = ["#1A3C5E","#2E86AB","#A23B72","#F18F01","#C73E1D","#3B1F2B",
           "#44BBA4","#E94F37","#393E41","#F5A623"]
sns.set_theme(style="whitegrid", palette=PALETTE, font_scale=1.1)
plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.family": "DejaVu Sans",
})


def fmt_cr(x):
    """Format large INR numbers as Cr / L."""
    if abs(x) >= 1e7: return f"Rs.{x/1e7:.2f}Cr"
    if abs(x) >= 1e5: return f"Rs.{x/1e5:.1f}L"
    return f"Rs.{x:,.0f}"


# ===
# PHASE 1 – Generate + Clean
# ===
print("=" * 60)
print("PHASE 1 — Data Generation")
print("=" * 60)
import generate_data as gd
gd.main()

print("\n" + "=" * 60)
print("PHASE 2 — Data Cleaning & Feature Engineering")
print("=" * 60)
import clean_data as cd
cd.main()

# --- Load processed data ---
print("\nLoading processed data ...")
txn   = pd.read_csv(os.path.join(PROC_DIR, "transactions_clean.csv"),
                    parse_dates=["txn_date"])
cust  = pd.read_csv(os.path.join(PROC_DIR, "customer_summary.csv"))
monthly = pd.read_csv(os.path.join(PROC_DIR, "monthly_trends.csv"))
cat_sum = pd.read_csv(os.path.join(PROC_DIR, "category_summary.csv"))
camps   = pd.read_csv(os.path.join(RAW_DIR,  "campaigns.csv"))
asgn    = pd.read_csv(os.path.join(RAW_DIR,  "campaign_assignments.csv"))


# ===
# PHASE 3 – EDA Plots
# ===
print("\n" + "=" * 60)
print("PHASE 3 — Exploratory Data Analysis")
print("=" * 60)

# --- Plot 1: Monthly spend trend ---
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(monthly["year_month"], monthly["total_spend"] / 1e6,
        color=PALETTE[1], linewidth=2.5, marker="o", markersize=4)
ax.fill_between(range(len(monthly)), monthly["total_spend"] / 1e6,
                alpha=0.15, color=PALETTE[1])
ax.set_xticks(range(0, len(monthly), 3))
ax.set_xticklabels(monthly["year_month"].iloc[::3], rotation=45, ha="right")
ax.set_title("Monthly Total Spend (INR Million)", fontsize=14, fontweight="bold")
ax.set_ylabel("Spend (Rs. Mn)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"Rs.{x:.0f}M"))
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "01_monthly_spend_trend.png"), bbox_inches="tight")
plt.close()
print("  ✓ Plot 01: Monthly spend trend")

# --- Plot 2: Category spend breakdown ---
cat_plot = cat_sum.sort_values("total_spend", ascending=True)
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(cat_plot["category"], cat_plot["total_spend"] / 1e6,
               color=PALETTE[:len(cat_plot)])
ax.bar_label(bars, labels=[f"Rs.{v/1e6:.1f}M" for v in cat_plot["total_spend"]],
             padding=4, fontsize=9)
ax.set_title("Total Spend by Category", fontsize=14, fontweight="bold")
ax.set_xlabel("Spend (Rs. Mn)")
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "02_spend_by_category.png"), bbox_inches="tight")
plt.close()
print("  ✓ Plot 02: Spend by category")

# --- Plot 3: Channel distribution ---
chan = txn.groupby("channel")["amount"].sum().reset_index()
fig, ax = plt.subplots(figsize=(7, 7))
wedges, texts, autotexts = ax.pie(
    chan["amount"], labels=chan["channel"],
    autopct="%1.1f%%", startangle=140,
    colors=PALETTE[:len(chan)],
    wedgeprops={"edgecolor": "white", "linewidth": 2}
)
ax.set_title("Spend by Channel", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "03_spend_by_channel.png"), bbox_inches="tight")
plt.close()
print("  ✓ Plot 03: Spend by channel")

# --- Plot 4: Card-type spend distribution ---
ct = txn.groupby("card_type")["amount"].agg(["sum", "count"]).reset_index()
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
axes[0].bar(ct["card_type"], ct["sum"] / 1e6, color=PALETTE[:4])
axes[0].set_title("Total Spend by Card Type", fontweight="bold")
axes[0].set_ylabel("Spend (Rs. Mn)")
axes[1].bar(ct["card_type"], ct["count"], color=PALETTE[4:8])
axes[1].set_title("Transaction Count by Card Type", fontweight="bold")
axes[1].set_ylabel("Transactions")
for ax in axes:
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "04_card_type_analysis.png"), bbox_inches="tight")
plt.close()
print("  ✓ Plot 04: Card-type analysis")

# --- Plot 5: Cashback cost vs interchange revenue ---
cat_rev = cat_sum.sort_values("total_spend", ascending=False)
x = range(len(cat_rev))
width = 0.35
fig, ax = plt.subplots(figsize=(13, 6))
ax.bar([i - width/2 for i in x], cat_rev["interchange_rev"] / 1e6,
       width, label="Interchange Revenue", color=PALETTE[1])
ax.bar([i + width/2 for i in x], cat_rev["total_cashback"] / 1e6,
       width, label="Cashback Cost", color=PALETTE[4])
ax.set_xticks(list(x))
ax.set_xticklabels(cat_rev["category"], rotation=30, ha="right")
ax.set_title("Interchange Revenue vs Cashback Cost by Category", fontsize=13, fontweight="bold")
ax.set_ylabel("Amount (Rs. Mn)")
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "05_revenue_vs_cashback_by_category.png"), bbox_inches="tight")
plt.close()
print("  ✓ Plot 05: Revenue vs cashback by category")

# --- Plot 6: Transaction amount distribution ---
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(txn["amount"].clip(upper=20000), bins=80,
        color=PALETTE[0], edgecolor="white", alpha=0.85)
ax.set_title("Transaction Amount Distribution (capped Rs.20K)", fontweight="bold")
ax.set_xlabel("Transaction Amount (Rs.)")
ax.set_ylabel("Count")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"Rs.{x:,.0f}"))
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "06_txn_amount_distribution.png"), bbox_inches="tight")
plt.close()
print("  ✓ Plot 06: Transaction amount distribution")


# ===
# PHASE 4 – Segmentation
# ===
print("\n" + "=" * 60)
print("PHASE 4 — Customer Segmentation (RFM)")
print("=" * 60)

seg_counts = cust["segment"].value_counts().reset_index()
seg_counts.columns = ["segment", "customer_count"]

seg_summary = cust.groupby("segment").agg(
    customers        = ("customer_id",     "count"),
    avg_spend        = ("total_spend",     "mean"),
    avg_txn_count    = ("txn_count",       "mean"),
    avg_recency_days = ("recency_days",    "mean"),
    avg_net_profit   = ("net_profit",      "mean"),
    total_net_profit = ("net_profit",      "sum"),
).reset_index().round(2)

print(seg_summary.to_string(index=False))

# --- Plot 7: Segment distribution ---
fig, axes = plt.subplots(1, 2, figsize=(13, 6))
seg_order = ["Champion", "Loyal", "At-Risk", "Dormant"]
seg_plot  = seg_summary.set_index("segment").reindex(seg_order)

axes[0].barh(seg_order, seg_plot["customers"], color=PALETTE[:4])
axes[0].set_title("Customer Count by Segment", fontweight="bold")
axes[0].set_xlabel("Customers")

axes[1].barh(seg_order, seg_plot["avg_net_profit"] / 1, color=PALETTE[4:8])
axes[1].set_title("Avg Net Profit per Customer (Rs.)", fontweight="bold")
axes[1].set_xlabel("Avg Net Profit (Rs.)")
axes[1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"Rs.{x:,.0f}"))

plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "07_segment_analysis.png"), bbox_inches="tight")
plt.close()
print("  ✓ Plot 07: Segment analysis")

# --- Plot 8: RFM score scatter ---
seg_colors = {"Champion": PALETTE[1], "Loyal": PALETTE[3],
              "At-Risk": PALETTE[4], "Dormant": PALETTE[8]}
fig, ax = plt.subplots(figsize=(9, 7))
for seg, grp in cust.groupby("segment"):
    sample = grp.sample(min(500, len(grp)), random_state=42)
    ax.scatter(sample["F_score"] + np.random.uniform(-0.15, 0.15, len(sample)),
               sample["M_score"] + np.random.uniform(-0.15, 0.15, len(sample)),
               c=seg_colors[seg], label=seg, alpha=0.5, s=20)
ax.set_xlabel("Frequency Score")
ax.set_ylabel("Monetary Score")
ax.set_title("RFM Segment Map (F vs M)", fontweight="bold")
ax.legend(title="Segment")
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "08_rfm_scatter.png"), bbox_inches="tight")
plt.close()
print("  ✓ Plot 08: RFM scatter")

# --- Plot 9: Segment × Card type heatmap ---
pivot = cust.groupby(["segment", "card_type"])["net_profit"].mean().unstack(fill_value=0)
fig, ax = plt.subplots(figsize=(10, 5))
sns.heatmap(pivot, annot=True, fmt=".0f", cmap="YlGnBu",
            linewidths=0.5, ax=ax, cbar_kws={"label": "Avg Net Profit (Rs.)"})
ax.set_title("Avg Net Profit: Segment × Card Type (Rs.)", fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "09_segment_cardtype_heatmap.png"), bbox_inches="tight")
plt.close()
print("  ✓ Plot 09: Segment × card type heatmap")


# ===
# PHASE 5 – Profitability Analysis
# ===
print("\n" + "=" * 60)
print("PHASE 5 — Customer Profitability")
print("=" * 60)

total_customers    = len(cust)
profitable_pct     = (cust["net_profit"] > 0).mean() * 100
total_gross_rev    = cust["gross_revenue"].sum()
total_cashback_cost= cust["total_cashback_cost"].sum()
total_svc_cost     = cust["total_service_cost"].sum()
total_net_profit   = cust["net_profit"].sum()
portfolio_margin   = total_net_profit / total_gross_rev * 100

print(f"  Total customers         : {total_customers:,}")
print(f"  Profitable customers    : {profitable_pct:.1f}%")
print(f"  Total gross revenue     : {fmt_cr(total_gross_rev)}")
print(f"  Total cashback cost     : {fmt_cr(total_cashback_cost)}")
print(f"  Total service cost      : {fmt_cr(total_svc_cost)}")
print(f"  Total net profit        : {fmt_cr(total_net_profit)}")
print(f"  Portfolio margin        : {portfolio_margin:.1f}%")

# Top & bottom decile
top10    = cust.nlargest(int(total_customers * 0.10), "net_profit")
bot10    = cust.nsmallest(int(total_customers * 0.10), "net_profit")
top10pct = top10["net_profit"].sum() / total_net_profit * 100

print(f"\n  Top-10% customers contribute {top10pct:.1f}% of total profit")
print(f"  Bottom-10% avg net profit: {fmt_cr(bot10['net_profit'].mean())}")

# --- Plot 10: Profit distribution ---
fig, ax = plt.subplots(figsize=(11, 5))
ax.hist(cust["net_profit"].clip(-5000, 15000), bins=80,
        color=PALETTE[1], edgecolor="white", alpha=0.85)
ax.axvline(0, color=PALETTE[4], linewidth=2, linestyle="--", label="Break-even")
ax.axvline(cust["net_profit"].median(), color=PALETTE[3], linewidth=2,
           linestyle="-.", label=f"Median Rs.{cust['net_profit'].median():,.0f}")
ax.set_title("Customer Net Profit Distribution", fontweight="bold")
ax.set_xlabel("Net Profit (Rs.)")
ax.set_ylabel("Customers")
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "10_profit_distribution.png"), bbox_inches="tight")
plt.close()
print("  ✓ Plot 10: Profit distribution")

# --- Plot 11: P&L waterfall by segment ---
seg_pnl = cust.groupby("segment")[["gross_revenue","total_cashback_cost",
                                    "total_service_cost","net_profit"]].sum()
seg_pnl = seg_pnl.reindex(["Champion","Loyal","At-Risk","Dormant"])
x = range(len(seg_pnl))
width = 0.2
fig, ax = plt.subplots(figsize=(13, 6))
ax.bar([i - width for i in x],      seg_pnl["gross_revenue"] / 1e6,      width, label="Gross Revenue",    color=PALETTE[1])
ax.bar([i         for i in x],      seg_pnl["total_cashback_cost"] / 1e6, width, label="Cashback Cost",    color=PALETTE[4])
ax.bar([i + width for i in x],      seg_pnl["total_service_cost"] / 1e6,  width, label="Service Cost",     color=PALETTE[2])
ax.plot(list(x), seg_pnl["net_profit"] / 1e6, "D--", color=PALETTE[3],
        linewidth=2, markersize=8, label="Net Profit", zorder=5)
ax.set_xticks(list(x))
ax.set_xticklabels(seg_pnl.index)
ax.set_title("P&L by Customer Segment (Rs. Mn)", fontweight="bold")
ax.set_ylabel("Amount (Rs. Mn)")
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "11_pnl_by_segment.png"), bbox_inches="tight")
plt.close()
print("  ✓ Plot 11: P&L by segment")

# --- Plot 12: Root-cause — bottom decile cashback rate ---
bot10_cb = bot10["total_cashback_cost"] / bot10["total_spend"].replace(0, np.nan) * 100
top10_cb = top10["total_cashback_cost"] / top10["total_spend"].replace(0, np.nan) * 100

fig, ax = plt.subplots(figsize=(9, 5))
ax.boxplot([bot10_cb.dropna(), top10_cb.dropna()], tick_labels=["Bottom 10%", "Top 10%"],
           patch_artist=True,
           boxprops=dict(facecolor=PALETTE[4], color=PALETTE[0]),
           medianprops=dict(color="white", linewidth=2))
ax.set_title("Cashback Rate: Bottom vs Top 10% Customers", fontweight="bold")
ax.set_ylabel("Effective Cashback Rate (%)")
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "12_rootcause_cashback_rate.png"), bbox_inches="tight")
plt.close()
print("  ✓ Plot 12: Root-cause cashback rate")

# --- Plot 13: Profitability by card type ---
ct_pnl = cust.groupby("card_type")[["gross_revenue","total_cost","net_profit"]].sum().round(2)
fig, ax = plt.subplots(figsize=(10, 5))
ct_pnl["net_profit_M"] = ct_pnl["net_profit"] / 1e6
bars = ax.bar(ct_pnl.index, ct_pnl["net_profit_M"], color=PALETTE[:4])
ax.bar_label(bars, labels=[f"Rs.{v:.2f}M" for v in ct_pnl["net_profit_M"]], padding=4)
ax.set_title("Total Net Profit by Card Type (Rs. Mn)", fontweight="bold")
ax.set_ylabel("Net Profit (Rs. Mn)")
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "13_profit_by_card_type.png"), bbox_inches="tight")
plt.close()
print("  ✓ Plot 13: Profit by card type")


# ===
# PHASE 6 – Campaign / Offer Analysis
# ===
print("\n" + "=" * 60)
print("PHASE 6 — Offer & Campaign Analysis")
print("=" * 60)

camp_results = []
for _, camp in camps.iterrows():
    enrolled = asgn[asgn["campaign_id"] == camp["campaign_id"]]
    enrolled_ids = enrolled["customer_id"].values
    redeemed_ids = enrolled[enrolled["redeemed"] == 1]["customer_id"].values

    start = pd.to_datetime(camp["start_date"])
    end   = pd.to_datetime(camp["end_date"])

    # Transactions in campaign window, for target category
    mask_cat  = (txn["category"] == camp["target_category"])
    mask_date = (txn["txn_date"] >= start) & (txn["txn_date"] <= end)

    txn_target   = txn[mask_cat & mask_date]
    spend_redeem = txn_target[txn_target["customer_id"].isin(redeemed_ids)]["amount"].sum()
    spend_non    = txn_target[~txn_target["customer_id"].isin(enrolled_ids)]["amount"].sum()

    n_enrolled  = len(enrolled_ids)
    n_redeemed  = len(redeemed_ids)
    n_non       = txn[~txn["customer_id"].isin(enrolled_ids)]["customer_id"].nunique()

    avg_redeem = spend_redeem / max(n_redeemed, 1)
    avg_non    = spend_non    / max(n_non, 1)
    lift_pct   = ((avg_redeem - avg_non) / max(avg_non, 1)) * 100

    extra_spend      = max(0, (avg_redeem - avg_non) * n_redeemed)
    interchange_rate = 0.015  # blended avg
    incremental_rev  = extra_spend * interchange_rate
    extra_cashback   = extra_spend * camp["bonus_cashback_pct"]
    campaign_cost    = camp["campaign_cost_inr"]
    net_campaign_pnl = incremental_rev - extra_cashback - campaign_cost
    roi_pct          = net_campaign_pnl / max(campaign_cost, 1) * 100

    camp_results.append({
        "campaign_id":        camp["campaign_id"],
        "campaign_name":      camp["campaign_name"],
        "target_category":    camp["target_category"],
        "n_enrolled":         n_enrolled,
        "n_redeemed":         n_redeemed,
        "redemption_rate_pct": round(n_redeemed / max(n_enrolled, 1) * 100, 1),
        "spend_lift_pct":     round(lift_pct, 2),
        "incremental_revenue":round(incremental_rev, 2),
        "extra_cashback_cost":round(extra_cashback, 2),
        "campaign_cost_inr":  campaign_cost,
        "net_campaign_pnl":   round(net_campaign_pnl, 2),
        "roi_pct":            round(roi_pct, 2),
    })

camp_df = pd.DataFrame(camp_results)
print(camp_df[["campaign_name","n_enrolled","redemption_rate_pct",
               "spend_lift_pct","roi_pct"]].to_string(index=False))
camp_df.to_csv(os.path.join(PROC_DIR, "campaign_performance.csv"), index=False)

# --- Plot 14: Campaign ROI comparison ---
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
camp_plot = camp_df.sort_values("roi_pct", ascending=False)
c_colors  = [PALETTE[1] if r >= 0 else PALETTE[4] for r in camp_plot["roi_pct"]]
axes[0].barh(camp_plot["campaign_name"], camp_plot["roi_pct"], color=c_colors)
axes[0].axvline(0, color="black", linewidth=1)
axes[0].set_title("Campaign ROI (%)", fontweight="bold")
axes[0].set_xlabel("ROI (%)")

axes[1].barh(camp_plot["campaign_name"], camp_plot["redemption_rate_pct"], color=PALETTE[2:7])
axes[1].set_title("Redemption Rate (%)", fontweight="bold")
axes[1].set_xlabel("Redemption Rate (%)")

plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "14_campaign_roi.png"), bbox_inches="tight")
plt.close()
print("  ✓ Plot 14: Campaign ROI")


# ===
# PHASE 7 – Power BI Export CSVs
# ===
print("\n" + "=" * 60)
print("PHASE 7 — Power BI Dataset Export")
print("=" * 60)

# Executive Overview
exec_kpis = pd.DataFrame([{
    "KPI":   "Total Customers",           "Value": total_customers,
    "Format": "number"},
    {"KPI": "Total Transactions",          "Value": len(txn),             "Format": "number"},
    {"KPI": "Total Spend (INR)",           "Value": round(txn["amount"].sum(), 2), "Format": "currency"},
    {"KPI": "Total Cashback Cost (INR)",   "Value": round(txn["cashback_amt"].sum(), 2), "Format": "currency"},
    {"KPI": "Total Interchange Revenue",   "Value": round(txn["interchange_revenue"].sum(), 2), "Format": "currency"},
    {"KPI": "Total Net Profit (INR)",      "Value": round(total_net_profit, 2), "Format": "currency"},
    {"KPI": "Portfolio Margin (%)",        "Value": round(portfolio_margin, 2), "Format": "percent"},
    {"KPI": "Profitable Customers (%)",    "Value": round(profitable_pct, 2),  "Format": "percent"},
    {"KPI": "Avg Txn Amount (INR)",        "Value": round(txn["amount"].mean(), 2), "Format": "currency"},
    {"KPI": "Top-10% Profit Contribution", "Value": round(top10pct, 2), "Format": "percent"},
])
exec_kpis.to_csv(os.path.join(PBI_DIR, "pbi_executive_kpis.csv"), index=False)

# Monthly trends (already built)
monthly.to_csv(os.path.join(PBI_DIR, "pbi_monthly_trends.csv"), index=False)

# Customer & portfolio CSV (subset columns)
cust_pbi = cust[[
    "customer_id","age","gender","city_tier","income_band","occupation",
    "card_type","tenure_months","credit_limit","annual_fee",
    "total_spend","total_cashback_cost","total_interchange",
    "annual_fee_revenue","total_service_cost","gross_revenue",
    "total_cost","net_profit","profit_margin_pct",
    "txn_count","avg_txn_amount","recency_days","active_months",
    "R_score","F_score","M_score","RFM_score","segment",
    "unique_categories","unique_channels",
]].copy()
cust_pbi.to_csv(os.path.join(PBI_DIR, "pbi_customer_portfolio.csv"), index=False)

# Category & cashback CSV
cat_sum.to_csv(os.path.join(PBI_DIR, "pbi_category_cashback.csv"), index=False)

# Segment summary
seg_summary.to_csv(os.path.join(PBI_DIR, "pbi_segment_summary.csv"), index=False)

# Campaign performance
camp_df.to_csv(os.path.join(PBI_DIR, "pbi_campaign_performance.csv"), index=False)

# Channel summary
chan_sum = txn.groupby("channel").agg(
    total_spend = ("amount","sum"), txn_count = ("txn_id","count"),
    cashback    = ("cashback_amt","sum"), interchange = ("interchange_revenue","sum")
).reset_index()
chan_sum.to_csv(os.path.join(PBI_DIR, "pbi_channel_summary.csv"), index=False)

print("  ✓ Power BI CSVs exported (6 files)")


# ===
# PHASE 8 – Excel Workbook
# ===
print("\n" + "=" * 60)
print("PHASE 8 — Excel Workbook Generation")
print("=" * 60)

XLS_PATH = os.path.join(XLS_DIR, "Credit_Card_Analysis_Summary.xlsx")

with pd.ExcelWriter(XLS_PATH, engine="xlsxwriter") as writer:
    wb  = writer.book

    # --- Formats ---
    hdr_fmt   = wb.add_format({"bold": True, "bg_color": "#1A3C5E",
                               "font_color": "white", "border": 1,
                               "align": "center", "valign": "vcenter"})
    kpi_lbl   = wb.add_format({"bold": True, "font_size": 12,
                               "bg_color": "#EAF4FB", "border": 1})
    kpi_val   = wb.add_format({"num_format": "#,##0", "font_size": 12,
                               "bold": True, "bg_color": "#D6EAF8",
                               "border": 1, "align": "right"})
    kpi_cur   = wb.add_format({"num_format": "Rs.#,##0.00", "font_size": 12,
                               "bold": True, "bg_color": "#D6EAF8",
                               "border": 1, "align": "right"})
    kpi_pct   = wb.add_format({"num_format": "0.00%", "font_size": 12,
                               "bold": True, "bg_color": "#D6EAF8",
                               "border": 1, "align": "right"})
    num_fmt   = wb.add_format({"num_format": "#,##0.00", "border": 1})
    pct_fmt   = wb.add_format({"num_format": "0.00%", "border": 1})
    bold_bdr  = wb.add_format({"bold": True, "border": 1, "bg_color": "#F2F3F4"})

    # --- Sheet 1: Executive KPIs Dashboard ---
    ws = wb.add_worksheet("Executive Dashboard")
    ws.set_zoom(90)
    ws.set_column("A:A", 35)
    ws.set_column("B:B", 22)

    ws.merge_range("A1:B1",
                   "Credit Card Profitability Analysis — Executive Dashboard",
                   wb.add_format({"bold": True, "font_size": 16,
                                  "bg_color": "#1A3C5E", "font_color": "white",
                                  "align": "center", "valign": "vcenter"}))
    ws.set_row(0, 35)

    kpis_display = [
        ("Total Customers",             total_customers,             "num"),
        ("Total Transactions",          len(txn),                    "num"),
        ("Total Spend (INR)",           txn["amount"].sum(),          "cur"),
        ("Total Cashback Cost (INR)",   txn["cashback_amt"].sum(),    "cur"),
        ("Total Interchange Revenue",   txn["interchange_revenue"].sum(), "cur"),
        ("Total Net Profit (INR)",      total_net_profit,             "cur"),
        ("Portfolio Margin (%)",        portfolio_margin / 100,       "pct"),
        ("Profitable Customers (%)",    profitable_pct / 100,         "pct"),
        ("Avg Transaction Amount (INR)",txn["amount"].mean(),          "cur"),
        ("Top-10% Profit Contribution", top10pct / 100,               "pct"),
    ]

    for row_i, (label, val, fmt_type) in enumerate(kpis_display):
        ws.write(row_i + 1, 0, label, kpi_lbl)
        vfmt = kpi_pct if fmt_type == "pct" else kpi_cur if fmt_type == "cur" else kpi_val
        ws.write(row_i + 1, 1, val, vfmt)
        ws.set_row(row_i + 1, 22)

    # --- Sheet 2: Segment P&L ---
    seg_pnl2 = cust.groupby("segment").agg(
        Customers       = ("customer_id",         "count"),
        Avg_Spend       = ("total_spend",         "mean"),
        Avg_Txn_Count   = ("txn_count",           "mean"),
        Avg_Recency     = ("recency_days",         "mean"),
        Total_Revenue   = ("gross_revenue",       "sum"),
        Total_Cashback  = ("total_cashback_cost", "sum"),
        Total_Svc_Cost  = ("total_service_cost",  "sum"),
        Total_Profit    = ("net_profit",          "sum"),
        Avg_Profit      = ("net_profit",          "mean"),
        Profit_Margin   = ("profit_margin_pct",   "mean"),
    ).reset_index().round(2)
    seg_pnl2.to_excel(writer, sheet_name="Segment P&L", index=False, startrow=1)
    ws2 = writer.sheets["Segment P&L"]
    ws2.set_column("A:A", 14); ws2.set_column("B:K", 18)
    for col_i, col_name in enumerate(seg_pnl2.columns):
        ws2.write(1, col_i, col_name, hdr_fmt)

    # --- Sheet 3: Category Summary ---
    cat_sum.to_excel(writer, sheet_name="Category Summary", index=False, startrow=1)
    ws3 = writer.sheets["Category Summary"]
    ws3.set_column("A:A", 16); ws3.set_column("B:I", 20)
    for col_i, col_name in enumerate(cat_sum.columns):
        ws3.write(1, col_i, col_name, hdr_fmt)

    # --- Sheet 4: Campaign Performance ---
    camp_df.to_excel(writer, sheet_name="Campaign Performance", index=False, startrow=1)
    ws4 = writer.sheets["Campaign Performance"]
    ws4.set_column("A:A", 10); ws4.set_column("B:L", 22)
    for col_i, col_name in enumerate(camp_df.columns):
        ws4.write(1, col_i, col_name, hdr_fmt)

    # --- Sheet 5: What-If Cashback Analysis ---
    ws5 = wb.add_worksheet("What-If Cashback")
    ws5.set_column("A:A", 28); ws5.set_column("B:F", 20)
    ws5.merge_range("A1:F1", "What-If: Impact of Changing Cashback Rate",
                    wb.add_format({"bold": True, "font_size": 14,
                                   "bg_color": "#1A3C5E", "font_color": "white",
                                   "align": "center"}))
    ws5.set_row(0, 30)

    base_cb_rate   = txn["cashback_amt"].sum() / txn["amount"].sum()
    base_interch   = txn["interchange_revenue"].sum()
    base_ann_fees  = cust["annual_fee_revenue"].sum()
    base_svc_cost  = cust["total_service_cost"].sum()
    base_spend     = txn["amount"].sum()

    headers = ["Cashback Rate (%)", "Total Cashback Cost",
               "Gross Revenue", "Net Profit", "Portfolio Margin (%)"]
    for col_i, h in enumerate(headers):
        ws5.write(1, col_i, h, hdr_fmt)

    rates = [0.005, 0.008, 0.010, 0.012, 0.015, 0.018, 0.020, 0.025, 0.030]
    for row_i, rate in enumerate(rates):
        cb_cost   = base_spend * rate
        gross_rev = base_interch + base_ann_fees
        net_p     = gross_rev - cb_cost - base_svc_cost
        margin    = net_p / gross_rev * 100
        ws5.write(row_i + 2, 0, f"{rate*100:.1f}%", bold_bdr)
        ws5.write(row_i + 2, 1, round(cb_cost,   2), num_fmt)
        ws5.write(row_i + 2, 2, round(gross_rev, 2), num_fmt)
        ws5.write(row_i + 2, 3, round(net_p,     2), num_fmt)
        ws5.write(row_i + 2, 4, round(margin,    2), num_fmt)

    # --- Sheet 6: Monthly Trends ---
    monthly.to_excel(writer, sheet_name="Monthly Trends", index=False, startrow=1)
    ws6 = writer.sheets["Monthly Trends"]
    ws6.set_column("A:A", 14); ws6.set_column("B:I", 20)
    for col_i, col_name in enumerate(monthly.columns):
        ws6.write(1, col_i, col_name, hdr_fmt)

print(f"  ✓ Excel workbook saved: {XLS_PATH}")


# ===
# PHASE 9 – Final KPIs & Resume Bullets
# ===
print("\n" + "=" * 60)
print("FINAL KPIs — Use These in README & Resume")
print("=" * 60)

total_spend_cr    = txn["amount"].sum() / 1e7
total_cashback_cr = txn["cashback_amt"].sum() / 1e7
total_profit_cr   = total_net_profit / 1e7
best_camp         = camp_df.loc[camp_df["roi_pct"].idxmax(), "campaign_name"]
best_camp_roi     = camp_df["roi_pct"].max()
worst_camp        = camp_df.loc[camp_df["roi_pct"].idxmin(), "campaign_name"]
worst_camp_roi    = camp_df["roi_pct"].min()
champion_avg_prof = cust.loc[cust["segment"] == "Champion", "net_profit"].mean()
dormant_avg_prof  = cust.loc[cust["segment"] == "Dormant",  "net_profit"].mean()
n_txn             = len(txn)
top_cat_spend     = cat_sum.loc[cat_sum["total_spend"].idxmax(), "category"]
top_cat_cashback  = cat_sum.loc[cat_sum["total_cashback"].idxmax(), "category"]
champion_count    = (cust["segment"] == "Champion").sum()
dormant_count     = (cust["segment"] == "Dormant").sum()
loyal_count       = (cust["segment"] == "Loyal").sum()
at_risk_count     = (cust["segment"] == "At-Risk").sum()

kpi_data = {
    "Total Customers":         total_customers,
    "Total Transactions":      n_txn,
    "Total Spend (Cr)":        round(total_spend_cr, 2),
    "Total Cashback Cost (Cr)":round(total_cashback_cr, 2),
    "Total Net Profit (Cr)":   round(total_profit_cr, 2),
    "Portfolio Margin (%)":    round(portfolio_margin, 2),
    "Profitable Customers (%)":round(profitable_pct, 2),
    "Top-10% Profit Share (%)":round(top10pct, 2),
    "Best Campaign":           best_camp,
    "Best Campaign ROI (%)":   round(best_camp_roi, 2),
    "Champion Customers":      champion_count,
    "Dormant Customers":       dormant_count,
    "Top Spend Category":      top_cat_spend,
    "Top Cashback Category":   top_cat_cashback,
    "Avg Txn Amount (INR)":    round(txn["amount"].mean(), 2),
}

for k, v in kpi_data.items():
    print(f"  {k:<35} {v}")

# Save KPIs for README generation
kpi_df = pd.DataFrame(list(kpi_data.items()), columns=["KPI", "Value"])
kpi_df.to_csv(os.path.join(PROC_DIR, "final_kpis.csv"), index=False)

print("\n" + "=" * 60)
print("RESUME BULLETS (based on actual results)")
print("=" * 60)
bullet1 = (
    f"• Engineered an end-to-end banking analytics pipeline on {total_customers:,} customers "
    f"and {n_txn:,} credit-card transactions (Rs.{total_spend_cr:.1f}Cr total spend) using "
    f"Python (Pandas/NumPy/Matplotlib), SQL (PostgreSQL), and Power BI; "
    f"delivered a {portfolio_margin:.1f}% portfolio margin insight to stakeholders."
)
bullet2 = (
    f"• Applied RFM-based customer segmentation to classify {champion_count:,} Champions "
    f"and {dormant_count:,} Dormant customers; identified that the top 10% of customers "
    f"generate {top10pct:.1f}% of total profit, enabling targeted retention strategy "
    f"recommendations for at-risk segments."
)
bullet3 = (
    f"• Conducted cashback & campaign profitability analysis across 5 marketing offers; "
    f"'{best_camp}' achieved {best_camp_roi:.1f}% ROI while '{worst_camp}' posted "
    f"{worst_camp_roi:.1f}% ROI — built a what-if Excel model showing ±2% cashback rate "
    f"change impacts net profit by Rs.{abs(base_spend * 0.02 / 1e7):.1f}Cr."
)
print("\n" + bullet1)
print("\n" + bullet2)
print("\n" + bullet3)

# Save bullets
with open(os.path.join(BASE_DIR, "RESUME_BULLETS.txt"), "w") as f:
    f.write("RESUME BULLETS — Credit Card Spend & Cashback Profitability Analysis\n")
    f.write("=" * 70 + "\n\n")
    f.write(bullet1 + "\n\n")
    f.write(bullet2 + "\n\n")
    f.write(bullet3 + "\n")

print("\n\n[OK] FULL PIPELINE COMPLETE!")
print(f"   Figures    : {FIG_DIR}")
print(f"   Power BI   : {PBI_DIR}")
print(f"   Excel      : {XLS_PATH}")
print(f"   Bullets    : {os.path.join(BASE_DIR, 'RESUME_BULLETS.txt')}")
