CREATE DATABASE B2BSales;
USE B2BSales;

CREATE TABLE dbo.b2b_sales (
    Product        nvarchar(50) NULL,
    Seller         nvarchar(50) NULL,
    Authority      nvarchar(50) NULL,
    Comp_size      nvarchar(50) NULL,
    Competitors    nvarchar(50) NULL,
    Purch_dept     nvarchar(50) NULL,
    Partnership    nvarchar(50) NULL,
    Budgt_alloc    nvarchar(50) NULL,
    Forml_tend     nvarchar(50) NULL,
    RFI            nvarchar(50) NULL,
    RFP            nvarchar(50) NULL,
    Growth         nvarchar(50) NULL,
    Posit_statm    nvarchar(50) NULL,
    Source         nvarchar(50) NULL,
    Client         nvarchar(50) NULL,
    Scope          nvarchar(50) NULL,
    Strat_deal     nvarchar(50) NULL,
    Cross_sale     nvarchar(50) NULL,
    Up_sale        nvarchar(50) NULL,
    Deal_type      nvarchar(50) NULL,
    Needs_def      nvarchar(50) NULL,
    Att_t_client   nvarchar(50) NULL,
    Status         nvarchar(50) NULL,
    won            int          NULL
);
GO

BULK INSERT dbo.b2b_sales
FROM 'C:\Temp\b2b_sales_clean.csv'
WITH (
    FORMAT = 'CSV',
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    KEEPNULLS,
    TABLOCK
);
GO

SELECT COUNT(*) AS total_rows,
       SUM(won) AS total_won,
       CAST(100.0 * SUM(won) / COUNT(*) AS decimal(5,2)) AS win_rate_pct
FROM dbo.b2b_sales;
GO

CREATE OR ALTER VIEW dbo.vw_b2b_driver_summary AS
WITH long_form AS (
    SELECT 'Authority' AS dimension, Authority AS [level], won FROM dbo.b2b_sales
    UNION ALL SELECT 'Company size', Comp_size, won FROM dbo.b2b_sales
    UNION ALL SELECT 'Competitors present', Competitors, won FROM dbo.b2b_sales
    UNION ALL SELECT 'Purchasing dept involved', Purch_dept, won FROM dbo.b2b_sales
    UNION ALL SELECT 'Existing partnership', Partnership, won FROM dbo.b2b_sales
    UNION ALL SELECT 'Budget allocated', Budgt_alloc, won FROM dbo.b2b_sales
    UNION ALL SELECT 'Formal tender', Forml_tend, won FROM dbo.b2b_sales
    UNION ALL SELECT 'Client growth trend', Growth, won FROM dbo.b2b_sales
    UNION ALL SELECT 'Positioning statement', Posit_statm, won FROM dbo.b2b_sales
    UNION ALL SELECT 'Lead source', Source, won FROM dbo.b2b_sales
    UNION ALL SELECT 'Client relationship', Client, won FROM dbo.b2b_sales
    UNION ALL SELECT 'Scope clarity', Scope, won FROM dbo.b2b_sales
    UNION ALL SELECT 'Strategic importance', Strat_deal, won FROM dbo.b2b_sales
    UNION ALL SELECT 'Cross-sell opportunity', Cross_sale, won FROM dbo.b2b_sales
    UNION ALL SELECT 'Up-sell opportunity', Up_sale, won FROM dbo.b2b_sales
    UNION ALL SELECT 'Deal type', Deal_type, won FROM dbo.b2b_sales
    UNION ALL SELECT 'Needs definition', Needs_def, won FROM dbo.b2b_sales
    UNION ALL SELECT 'Client classification', Att_t_client, won FROM dbo.b2b_sales
),
agg AS (
    SELECT dimension, [level], COUNT(*) AS deals, SUM(won) AS wins
    FROM long_form
    GROUP BY dimension, [level]
)
SELECT dimension,
       [level],
       deals,
       wins,
       CAST(100.0 * wins / deals AS decimal(5,2)) AS win_rate_pct,
       CAST(100.0 * wins / deals
            - 100.0 * SUM(wins) OVER (PARTITION BY dimension)
                    / SUM(deals) OVER (PARTITION BY dimension) AS decimal(6,2)) AS gap_vs_overall_pp,
       CAST(100.0 * wins / SUM(wins) OVER (PARTITION BY dimension) AS decimal(5,1)) AS share_of_wins_pct
FROM agg;
GO

SELECT dimension, [level], deals, wins, win_rate_pct, gap_vs_overall_pp, share_of_wins_pct
FROM dbo.vw_b2b_driver_summary
ORDER BY dimension, win_rate_pct DESC;

SELECT TOP 15 dimension, [level], deals, wins, win_rate_pct, gap_vs_overall_pp, share_of_wins_pct
FROM dbo.vw_b2b_driver_summary
WHERE deals >= 15
ORDER BY gap_vs_overall_pp DESC;

SELECT TOP 15 dimension, [level], deals, wins, win_rate_pct, gap_vs_overall_pp, share_of_wins_pct
FROM dbo.vw_b2b_driver_summary
WHERE deals >= 15
ORDER BY gap_vs_overall_pp ASC;

SELECT Seller, COUNT(*) AS deals, SUM(won) AS wins,
       CAST(100.0 * SUM(won) / COUNT(*) AS decimal(5,2)) AS win_rate_pct
FROM dbo.b2b_sales
GROUP BY Seller
HAVING COUNT(*) >= 10
ORDER BY win_rate_pct DESC;

SELECT Product, COUNT(*) AS deals, SUM(won) AS wins,
       CAST(100.0 * SUM(won) / COUNT(*) AS decimal(5,2)) AS win_rate_pct
FROM dbo.b2b_sales
GROUP BY Product
HAVING COUNT(*) >= 10
ORDER BY win_rate_pct DESC;