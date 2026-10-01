-- =============================================================================
-- schema.sql
-- Credit Card Spend & Cashback Profitability Analysis
-- PostgreSQL DDL — Create tables, indexes, and constraints
-- =============================================================================

-- Drop and recreate schema
DROP SCHEMA IF EXISTS cc_analysis CASCADE;
CREATE SCHEMA cc_analysis;
SET search_path = cc_analysis;

-- =============================================================================
-- TABLE: customers
-- =============================================================================
CREATE TABLE customers (
    customer_id     VARCHAR(10)  PRIMARY KEY,
    age             SMALLINT     NOT NULL CHECK (age BETWEEN 18 AND 80),
    gender          VARCHAR(10)  NOT NULL,
    city_tier       VARCHAR(10)  NOT NULL,
    income_band     VARCHAR(20)  NOT NULL,
    occupation      VARCHAR(20)  NOT NULL,
    card_type       VARCHAR(12)  NOT NULL,
    tenure_months   SMALLINT     NOT NULL CHECK (tenure_months >= 1),
    credit_limit    NUMERIC(12,2)NOT NULL CHECK (credit_limit >= 0),
    annual_fee      NUMERIC(8,2) NOT NULL,
    join_date       DATE         NOT NULL
);

CREATE INDEX idx_customers_card_type  ON customers(card_type);
CREATE INDEX idx_customers_city_tier  ON customers(city_tier);
CREATE INDEX idx_customers_segment    ON customers(income_band);

-- =============================================================================
-- TABLE: transactions
-- =============================================================================
CREATE TABLE transactions (
    txn_id              VARCHAR(12)   PRIMARY KEY,
    customer_id         VARCHAR(10)   NOT NULL REFERENCES customers(customer_id),
    card_type           VARCHAR(12)   NOT NULL,
    txn_date            DATE          NOT NULL,
    amount              NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    category            VARCHAR(20)   NOT NULL,
    channel             VARCHAR(15)   NOT NULL,
    merchant            VARCHAR(50),
    cashback_pct        NUMERIC(6,4)  NOT NULL DEFAULT 0,
    cashback_amt        NUMERIC(10,2) NOT NULL DEFAULT 0,
    interchange_revenue NUMERIC(10,2) NOT NULL DEFAULT 0,
    is_declined         SMALLINT      NOT NULL DEFAULT 0 CHECK (is_declined IN (0,1))
);

CREATE INDEX idx_txn_customer    ON transactions(customer_id);
CREATE INDEX idx_txn_date        ON transactions(txn_date);
CREATE INDEX idx_txn_category    ON transactions(category);
CREATE INDEX idx_txn_card_type   ON transactions(card_type);
CREATE INDEX idx_txn_channel     ON transactions(channel);
CREATE INDEX idx_txn_date_cat    ON transactions(txn_date, category);
CREATE INDEX idx_txn_declined    ON transactions(is_declined);

-- =============================================================================
-- TABLE: cashback_rules
-- =============================================================================
CREATE TABLE cashback_rules (
    rule_id         SERIAL        PRIMARY KEY,
    card_type       VARCHAR(12)   NOT NULL,
    category        VARCHAR(20)   NOT NULL,
    cashback_pct    NUMERIC(6,4)  NOT NULL,
    max_cashback_pm NUMERIC(8,2)  NOT NULL,
    UNIQUE (card_type, category)
);

-- =============================================================================
-- TABLE: campaigns
-- =============================================================================
CREATE TABLE campaigns (
    campaign_id          VARCHAR(10)   PRIMARY KEY,
    campaign_name        VARCHAR(60)   NOT NULL,
    target_category      VARCHAR(20),
    start_date           DATE          NOT NULL,
    end_date             DATE          NOT NULL,
    bonus_cashback_pct   NUMERIC(6,4)  NOT NULL DEFAULT 0,
    campaign_cost_inr    NUMERIC(12,2) NOT NULL DEFAULT 0,
    target_card          VARCHAR(12)   NOT NULL DEFAULT 'All',
    CHECK (end_date >= start_date)
);

-- =============================================================================
-- TABLE: campaign_assignments
-- =============================================================================
CREATE TABLE campaign_assignments (
    assignment_id  SERIAL       PRIMARY KEY,
    campaign_id    VARCHAR(10)  NOT NULL REFERENCES campaigns(campaign_id),
    customer_id    VARCHAR(10)  NOT NULL REFERENCES customers(customer_id),
    enrolled_date  DATE,
    redeemed       SMALLINT     NOT NULL DEFAULT 0 CHECK (redeemed IN (0,1)),
    UNIQUE (campaign_id, customer_id)
);

CREATE INDEX idx_assign_campaign  ON campaign_assignments(campaign_id);
CREATE INDEX idx_assign_customer  ON campaign_assignments(customer_id);

-- =============================================================================
-- VIEW: customer_profitability
-- =============================================================================
CREATE OR REPLACE VIEW customer_profitability AS
WITH txn_agg AS (
    SELECT
        t.customer_id,
        SUM(t.amount)               AS total_spend,
        SUM(t.cashback_amt)         AS total_cashback_cost,
        SUM(t.interchange_revenue)  AS total_interchange,
        COUNT(t.txn_id)             AS txn_count,
        MAX(t.txn_date)             AS last_txn_date,
        COUNT(DISTINCT t.category)  AS unique_categories,
        COUNT(DISTINCT t.channel)   AS unique_channels
    FROM transactions t
    WHERE t.is_declined = 0
    GROUP BY t.customer_id
)
SELECT
    c.customer_id,
    c.card_type,
    c.age,
    c.gender,
    c.city_tier,
    c.income_band,
    c.occupation,
    c.tenure_months,
    c.annual_fee,
    COALESCE(a.total_spend,           0) AS total_spend,
    COALESCE(a.total_cashback_cost,   0) AS total_cashback_cost,
    COALESCE(a.total_interchange,     0) AS total_interchange,
    COALESCE(a.txn_count,             0) AS txn_count,
    COALESCE(a.last_txn_date, c.join_date) AS last_txn_date,
    COALESCE(a.unique_categories,     0) AS unique_categories,
    COALESCE(a.unique_channels,       0) AS unique_channels,
    -- Revenue
    COALESCE(a.total_interchange, 0) + (c.annual_fee * 2)  AS gross_revenue,
    -- Costs
    COALESCE(a.total_cashback_cost, 0)
        + (CASE c.card_type
               WHEN 'Classic'   THEN 30
               WHEN 'Gold'      THEN 55
               WHEN 'Platinum'  THEN 90
               WHEN 'Signature' THEN 150
           END * 24)                                        AS total_cost,
    -- Net Profit
    (COALESCE(a.total_interchange, 0) + (c.annual_fee * 2))
    - (COALESCE(a.total_cashback_cost, 0)
        + (CASE c.card_type
               WHEN 'Classic'   THEN 30
               WHEN 'Gold'      THEN 55
               WHEN 'Platinum'  THEN 90
               WHEN 'Signature' THEN 150
           END * 24))                                       AS net_profit
FROM customers c
LEFT JOIN txn_agg a ON c.customer_id = a.customer_id;

COMMENT ON VIEW customer_profitability IS
    'Per-customer P&L: Gross Revenue - Cashback Cost - Service Cost = Net Profit';
