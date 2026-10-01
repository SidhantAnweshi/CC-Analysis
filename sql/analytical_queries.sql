-- =============================================================================
-- analytical_queries.sql
-- Credit Card Spend & Cashback Profitability Analysis
-- 12 Production-Ready PostgreSQL Analytical Queries
-- =============================================================================
SET search_path = cc_analysis;

-- ─────────────────────────────────────────────────────────────────────────────
-- Q1: Portfolio-Level KPIs (Executive Summary)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    COUNT(DISTINCT t.customer_id)                           AS active_customers,
    COUNT(t.txn_id)                                         AS total_transactions,
    ROUND(SUM(t.amount)::NUMERIC,               2)          AS total_spend_inr,
    ROUND(SUM(t.cashback_amt)::NUMERIC,         2)          AS total_cashback_cost,
    ROUND(SUM(t.interchange_revenue)::NUMERIC,  2)          AS total_interchange_rev,
    ROUND(AVG(t.amount)::NUMERIC,               2)          AS avg_txn_amount,
    ROUND(
        SUM(t.cashback_amt) / NULLIF(SUM(t.amount), 0) * 100, 2
    )                                                        AS effective_cashback_rate_pct,
    ROUND(
        SUM(t.interchange_revenue) / NULLIF(SUM(t.amount), 0) * 100, 2
    )                                                        AS effective_interchange_rate_pct
FROM transactions t
WHERE t.is_declined = 0;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q2: Monthly Spend & Cashback Trend (24-Month View)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    TO_CHAR(txn_date, 'YYYY-MM')                AS year_month,
    COUNT(txn_id)                               AS txn_count,
    COUNT(DISTINCT customer_id)                 AS active_customers,
    ROUND(SUM(amount)::NUMERIC,               2) AS total_spend,
    ROUND(SUM(cashback_amt)::NUMERIC,         2) AS total_cashback,
    ROUND(SUM(interchange_revenue)::NUMERIC,  2) AS interchange_rev,
    ROUND(
        (SUM(interchange_revenue) - SUM(cashback_amt))::NUMERIC, 2
    )                                            AS net_revenue,
    ROUND(AVG(amount)::NUMERIC,               2) AS avg_txn_amount
FROM transactions
WHERE is_declined = 0
GROUP BY TO_CHAR(txn_date, 'YYYY-MM')
ORDER BY year_month;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q3: Spend & Cashback by Category (Profitability Breakdown)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    category,
    COUNT(txn_id)                               AS txn_count,
    COUNT(DISTINCT customer_id)                 AS unique_customers,
    ROUND(SUM(amount)::NUMERIC,               2) AS total_spend,
    ROUND(AVG(amount)::NUMERIC,               2) AS avg_txn_amount,
    ROUND(SUM(cashback_amt)::NUMERIC,         2) AS total_cashback_cost,
    ROUND(SUM(interchange_revenue)::NUMERIC,  2) AS interchange_rev,
    ROUND(
        SUM(cashback_amt) / NULLIF(SUM(amount), 0) * 100, 2
    )                                            AS cashback_rate_pct,
    ROUND(
        (SUM(interchange_revenue) - SUM(cashback_amt))::NUMERIC, 2
    )                                            AS net_revenue
FROM transactions
WHERE is_declined = 0
GROUP BY category
ORDER BY total_spend DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q4: Card-Type Performance (Revenue, Cost, Profitability)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    c.card_type,
    COUNT(DISTINCT c.customer_id)               AS customers,
    ROUND(AVG(c.annual_fee)::NUMERIC,         2) AS avg_annual_fee,
    ROUND(SUM(t.amount)::NUMERIC,             2) AS total_spend,
    ROUND(SUM(t.interchange_revenue)::NUMERIC,2) AS total_interchange,
    ROUND(SUM(c.annual_fee * 2)::NUMERIC,     2) AS total_annual_fee_rev,
    ROUND(SUM(t.cashback_amt)::NUMERIC,       2) AS total_cashback_cost,
    ROUND(
        (SUM(t.interchange_revenue) + SUM(c.annual_fee * 2))::NUMERIC, 2
    )                                            AS gross_revenue,
    ROUND(
        (SUM(t.interchange_revenue) + SUM(c.annual_fee * 2)
         - SUM(t.cashback_amt))::NUMERIC, 2
    )                                            AS net_profit_excl_svc
FROM customers c
LEFT JOIN transactions t
    ON c.customer_id = t.customer_id AND t.is_declined = 0
GROUP BY c.card_type
ORDER BY net_profit_excl_svc DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q5: Customer Profitability Deciles
-- ─────────────────────────────────────────────────────────────────────────────
WITH customer_pnl AS (
    SELECT
        customer_id,
        net_profit,
        NTILE(10) OVER (ORDER BY net_profit) AS profit_decile
    FROM customer_profitability
),
decile_summary AS (
    SELECT
        profit_decile,
        COUNT(*)                                    AS customers,
        ROUND(AVG(net_profit)::NUMERIC, 2)          AS avg_net_profit,
        ROUND(SUM(net_profit)::NUMERIC, 2)          AS total_net_profit,
        ROUND(MIN(net_profit)::NUMERIC, 2)          AS min_profit,
        ROUND(MAX(net_profit)::NUMERIC, 2)          AS max_profit
    FROM customer_pnl
    GROUP BY profit_decile
)
SELECT
    profit_decile,
    customers,
    avg_net_profit,
    total_net_profit,
    min_profit,
    max_profit,
    ROUND(
        total_net_profit / SUM(total_net_profit) OVER () * 100, 2
    ) AS pct_of_total_profit
FROM decile_summary
ORDER BY profit_decile;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q6: RFM-Based Customer Segmentation
-- ─────────────────────────────────────────────────────────────────────────────
WITH rfm_raw AS (
    SELECT
        customer_id,
        MAX(txn_date)           AS last_txn_date,
        COUNT(txn_id)           AS frequency,
        SUM(amount)             AS monetary,
        CURRENT_DATE - MAX(txn_date) AS recency_days
    FROM transactions
    WHERE is_declined = 0
    GROUP BY customer_id
),
rfm_scored AS (
    SELECT
        customer_id,
        recency_days,
        frequency,
        ROUND(monetary::NUMERIC, 2) AS monetary,
        NTILE(4) OVER (ORDER BY recency_days DESC)  AS r_score,
        NTILE(4) OVER (ORDER BY frequency ASC)      AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC)       AS m_score
    FROM rfm_raw
),
segmented AS (
    SELECT *,
        (r_score + f_score + m_score) AS rfm_total,
        CASE
            WHEN (r_score + f_score + m_score) >= 10 THEN 'Champion'
            WHEN (r_score + f_score + m_score) >= 7  THEN 'Loyal'
            WHEN (r_score + f_score + m_score) >= 4  THEN 'At-Risk'
            ELSE 'Dormant'
        END AS segment
    FROM rfm_scored
)
SELECT
    segment,
    COUNT(*)                                    AS customers,
    ROUND(AVG(recency_days)::NUMERIC, 1)        AS avg_recency_days,
    ROUND(AVG(frequency)::NUMERIC, 1)           AS avg_txn_count,
    ROUND(AVG(monetary)::NUMERIC, 2)            AS avg_spend
FROM segmented
GROUP BY segment
ORDER BY avg_spend DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q7: Channel Analysis (Spend, Cashback, Count)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    channel,
    COUNT(txn_id)                               AS txn_count,
    ROUND(SUM(amount)::NUMERIC,               2) AS total_spend,
    ROUND(AVG(amount)::NUMERIC,               2) AS avg_txn_amount,
    ROUND(SUM(cashback_amt)::NUMERIC,         2) AS total_cashback,
    ROUND(SUM(interchange_revenue)::NUMERIC,  2) AS interchange_rev,
    ROUND(
        SUM(cashback_amt) / NULLIF(SUM(amount), 0) * 100, 2
    )                                            AS effective_cb_rate_pct,
    COUNT(DISTINCT customer_id)                  AS unique_customers
FROM transactions
WHERE is_declined = 0
GROUP BY channel
ORDER BY total_spend DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q8: High-Value Customer Identification (Top 500 by Profitability)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    cp.customer_id,
    cp.card_type,
    cp.age,
    cp.city_tier,
    cp.income_band,
    ROUND(cp.total_spend::NUMERIC,        2) AS total_spend,
    ROUND(cp.gross_revenue::NUMERIC,      2) AS gross_revenue,
    ROUND(cp.total_cashback_cost::NUMERIC,2) AS cashback_cost,
    ROUND(cp.net_profit::NUMERIC,         2) AS net_profit,
    cp.txn_count,
    cp.unique_categories
FROM customer_profitability cp
ORDER BY cp.net_profit DESC
LIMIT 500;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q9: Root-Cause Analysis — Bottom-Decile Unprofitable Customers
-- ─────────────────────────────────────────────────────────────────────────────
WITH ranked AS (
    SELECT
        customer_id,
        card_type,
        income_band,
        city_tier,
        total_spend,
        total_cashback_cost,
        total_interchange,
        gross_revenue,
        total_cost,
        net_profit,
        CASE WHEN total_spend > 0
             THEN ROUND((total_cashback_cost / total_spend * 100)::NUMERIC, 2)
             ELSE 0 END                   AS eff_cashback_rate_pct,
        NTILE(10) OVER (ORDER BY net_profit) AS decile
    FROM customer_profitability
)
SELECT
    card_type,
    income_band,
    city_tier,
    COUNT(*)                                    AS customer_count,
    ROUND(AVG(total_spend)::NUMERIC,          2) AS avg_spend,
    ROUND(AVG(total_cashback_cost)::NUMERIC,  2) AS avg_cashback_cost,
    ROUND(AVG(total_interchange)::NUMERIC,    2) AS avg_interchange,
    ROUND(AVG(net_profit)::NUMERIC,           2) AS avg_net_profit,
    ROUND(AVG(eff_cashback_rate_pct)::NUMERIC,2) AS avg_cb_rate_pct
FROM ranked
WHERE decile = 1     -- bottom 10%
GROUP BY card_type, income_band, city_tier
ORDER BY avg_net_profit ASC
LIMIT 20;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q10: Campaign Performance & ROI
-- ─────────────────────────────────────────────────────────────────────────────
WITH campaign_spend AS (
    SELECT
        ca.campaign_id,
        COUNT(DISTINCT ca.customer_id)      AS enrolled,
        COUNT(DISTINCT CASE WHEN ca.redeemed = 1
                       THEN ca.customer_id END) AS redeemed,
        SUM(CASE WHEN ca.redeemed = 1
                 THEN t.amount ELSE 0 END)  AS redeemed_spend,
        SUM(t.cashback_amt)                 AS cashback_on_enrolled
    FROM campaign_assignments ca
    LEFT JOIN transactions t
        ON ca.customer_id = t.customer_id
        AND t.is_declined = 0
        AND t.txn_date BETWEEN
            (SELECT start_date FROM campaigns WHERE campaign_id = ca.campaign_id)
            AND
            (SELECT end_date   FROM campaigns WHERE campaign_id = ca.campaign_id)
        AND t.category =
            (SELECT target_category FROM campaigns WHERE campaign_id = ca.campaign_id)
    GROUP BY ca.campaign_id
)
SELECT
    c.campaign_id,
    c.campaign_name,
    c.target_category,
    c.start_date,
    c.end_date,
    cs.enrolled,
    cs.redeemed,
    ROUND(cs.redeemed::NUMERIC / NULLIF(cs.enrolled, 0) * 100, 2) AS redemption_rate_pct,
    ROUND(cs.redeemed_spend::NUMERIC,         2)                   AS redeemed_spend,
    ROUND(cs.cashback_on_enrolled::NUMERIC,   2)                   AS cashback_cost,
    c.campaign_cost_inr,
    ROUND(
        (cs.redeemed_spend * 0.015 - cs.cashback_on_enrolled - c.campaign_cost_inr)::NUMERIC, 2
    )                                                               AS net_campaign_pnl
FROM campaigns c
JOIN campaign_spend cs ON c.campaign_id = cs.campaign_id
ORDER BY net_campaign_pnl DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q11: Geographic (City Tier) Performance
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    c.city_tier,
    COUNT(DISTINCT c.customer_id)              AS customers,
    ROUND(SUM(t.amount)::NUMERIC,            2) AS total_spend,
    ROUND(AVG(t.amount)::NUMERIC,            2) AS avg_txn_amount,
    ROUND(SUM(t.cashback_amt)::NUMERIC,      2) AS total_cashback,
    ROUND(SUM(t.interchange_revenue)::NUMERIC,2) AS interchange_rev,
    ROUND(
        (SUM(t.interchange_revenue) - SUM(t.cashback_amt))::NUMERIC, 2
    )                                           AS net_revenue,
    ROUND(
        SUM(t.amount) / NULLIF(COUNT(DISTINCT c.customer_id), 0)::NUMERIC, 2
    )                                           AS spend_per_customer
FROM customers c
LEFT JOIN transactions t
    ON c.customer_id = t.customer_id AND t.is_declined = 0
GROUP BY c.city_tier
ORDER BY total_spend DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q12: YoY Spend Growth by Category
-- ─────────────────────────────────────────────────────────────────────────────
WITH yearly AS (
    SELECT
        category,
        EXTRACT(YEAR FROM txn_date) AS yr,
        SUM(amount)                 AS total_spend
    FROM transactions
    WHERE is_declined = 0
    GROUP BY category, EXTRACT(YEAR FROM txn_date)
),
pivoted AS (
    SELECT
        category,
        MAX(CASE WHEN yr = 2023 THEN total_spend ELSE 0 END) AS spend_2023,
        MAX(CASE WHEN yr = 2024 THEN total_spend ELSE 0 END) AS spend_2024
    FROM yearly
    GROUP BY category
)
SELECT
    category,
    ROUND(spend_2023::NUMERIC, 2)             AS spend_2023,
    ROUND(spend_2024::NUMERIC, 2)             AS spend_2024,
    ROUND(
        (spend_2024 - spend_2023) / NULLIF(spend_2023, 0) * 100, 2
    )                                          AS yoy_growth_pct
FROM pivoted
ORDER BY yoy_growth_pct DESC;
