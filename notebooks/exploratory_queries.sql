-- Nifty 100 Financial Intelligence Platform
-- Exploratory Queries — Sprint 1, Day 07
-- Run against data/nifty100.db

-- 1. Row counts across all 12 tables
SELECT 'companies' AS table_name, COUNT(*) AS row_count FROM companies
UNION ALL SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL SELECT 'market_cap', COUNT(*) FROM market_cap
UNION ALL SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL SELECT 'peer_groups', COUNT(*) FROM peer_groups;

-- 2. Companies with fewer than 5 years of P&L history (per DQ-16)
SELECT company_id, COUNT(*) AS years_available
FROM profitandloss
WHERE year != 'TTM'
GROUP BY company_id
HAVING COUNT(*) < 5;

-- 3. Null/missing value counts in key P&L fields
SELECT
    SUM(CASE WHEN sales IS NULL THEN 1 ELSE 0 END) AS null_sales,
    SUM(CASE WHEN net_profit IS NULL THEN 1 ELSE 0 END) AS null_net_profit,
    SUM(CASE WHEN eps IS NULL THEN 1 ELSE 0 END) AS null_eps
FROM profitandloss;

-- 4. Year coverage range per company (earliest to latest fiscal year)
SELECT company_id, MIN(year) AS first_year, MAX(year) AS last_year, COUNT(*) AS total_years
FROM profitandloss
WHERE year != 'TTM'
GROUP BY company_id
ORDER BY total_years ASC
LIMIT 10;

-- 5. Companies per broad sector
SELECT broad_sector, COUNT(*) AS company_count
FROM sectors
GROUP BY broad_sector
ORDER BY company_count DESC;

-- 6. Top 10 companies by latest year net profit
SELECT company_id, year, net_profit
FROM profitandloss
WHERE year = (SELECT MAX(year) FROM profitandloss WHERE year != 'TTM')
ORDER BY net_profit DESC
LIMIT 10;

-- 7. Companies with negative net profit in the most recent fiscal year
SELECT company_id, year, net_profit
FROM profitandloss
WHERE year = (SELECT MAX(year) FROM profitandloss WHERE year != 'TTM')
  AND net_profit < 0;

-- 8. Debt-free companies (borrowings = 0) in the latest year
SELECT company_id, year, borrowings
FROM balancesheet
WHERE year = (SELECT MAX(year) FROM balancesheet WHERE year != 'TTM')
  AND borrowings = 0;

-- 9. Companies missing from peer_groups (not in any peer comparison group)
SELECT c.id, c.company_name
FROM companies c
LEFT JOIN peer_groups pg ON c.id = pg.company_id
WHERE pg.company_id IS NULL;

-- 10. Average dividend yield by sector (2024 market data)
SELECT s.broad_sector, ROUND(AVG(mc.dividend_yield_pct), 2) AS avg_dividend_yield
FROM market_cap mc
JOIN sectors s ON mc.company_id = s.company_id
WHERE mc.year = 2024
GROUP BY s.broad_sector
ORDER BY avg_dividend_yield DESC;

-- 11. Rows with unparseable year values still present in the database (should be 0 after fix)
SELECT company_id, year FROM profitandloss WHERE year IN ('PARSE_ERROR', 'TTM');

-- 12. Check for remaining PARSE_ERROR rows in balancesheet and cashflow
SELECT 'balancesheet' AS tbl, company_id, year FROM balancesheet WHERE year = 'PARSE_ERROR'
UNION ALL
SELECT 'cashflow' AS tbl, company_id, year FROM cashflow WHERE year = 'PARSE_ERROR';

-- 13. Confirm: were the original 5 balance sheet PARSE_ERROR companies among our known orphans?
SELECT DISTINCT company_id FROM balancesheet
WHERE company_id IN ('ZYDUSLIFE', 'ZOMATO', 'WIPRO', 'VEDL', 'UNITDSPR');

-- 14. How many rows across all three time-series tables have non-standard "year" values (not ending in -03)?
SELECT 'profitandloss' AS tbl, year, COUNT(*) AS cnt FROM profitandloss WHERE year NOT LIKE '%-03' AND year != 'TTM' GROUP BY year
UNION ALL
SELECT 'balancesheet', year, COUNT(*) FROM balancesheet WHERE year NOT LIKE '%-03' AND year != 'TTM' GROUP BY year
UNION ALL
SELECT 'cashflow', year, COUNT(*) FROM cashflow WHERE year NOT LIKE '%-03' AND year != 'TTM' GROUP BY year;

-- 14b. Summary: how many rows are "-03" (standard March year-end) vs other months, across all 3 tables?
SELECT 'profitandloss' AS tbl,
    SUM(CASE WHEN year LIKE '%-03' THEN 1 ELSE 0 END) AS march_rows,
    SUM(CASE WHEN year = 'TTM' THEN 1 ELSE 0 END) AS ttm_rows,
    SUM(CASE WHEN year NOT LIKE '%-03' AND year != 'TTM' THEN 1 ELSE 0 END) AS other_month_rows
FROM profitandloss
UNION ALL
SELECT 'balancesheet',
    SUM(CASE WHEN year LIKE '%-03' THEN 1 ELSE 0 END),
    SUM(CASE WHEN year = 'TTM' THEN 1 ELSE 0 END),
    SUM(CASE WHEN year NOT LIKE '%-03' AND year != 'TTM' THEN 1 ELSE 0 END)
FROM balancesheet
UNION ALL
SELECT 'cashflow',
    SUM(CASE WHEN year LIKE '%-03' THEN 1 ELSE 0 END),
    SUM(CASE WHEN year = 'TTM' THEN 1 ELSE 0 END),
    SUM(CASE WHEN year NOT LIKE '%-03' AND year != 'TTM' THEN 1 ELSE 0 END)
FROM cashflow;