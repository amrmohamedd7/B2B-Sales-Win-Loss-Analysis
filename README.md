# B2B Sales Win/Loss Analysis

**Which factors predict whether a B2B sales opportunity is won or lost, and how should a sales team prioritize its pipeline?**

A data-analyst case study using a real, anonymized B2B software-sales dataset — SQL for exploration, Python for statistical validation and win-probability modeling.

## Problem

Sales teams have limited time and need to know where to focus it: which open deals are worth the effort, which deal patterns predict a loss early enough to act, and whether performance gaps between reps are real or just a product of who gets the harder deals. This project answers those questions using historical won/lost outcomes.

## Data

- Source: [Salvirt B2B Sales dataset](https://huggingface.co/datasets/markobo/B2B_Sales_data) (real, anonymized software-sales opportunities), license CC-BY-4.0
- **448 deals, 22 categorical attributes** describing each opportunity (client authority, company size, competitors present, lead source, deal type, etc.) plus the outcome (Won/Lost)
- No missing data in the traditional sense: "Unknown" is a genuine, informative answer category (e.g. "we don't know if there's a budget allocated"), not a blank to fill in
- **Baseline win rate: 50.7%**

## Method

| Stage | Tool |
|---|---|
| Load, define target, data-quality check | Python (pandas) |
| Driver analysis (win rate, gap vs. overall, share of wins per group) | SQL Server (T-SQL: a reporting view across 18 dimensions) |
| Hypothesis testing + a duplicate-row robustness check | Python (scipy: chi-square, Cramér's V) |
| Win-probability model | Python (scikit-learn: logistic regression, EPV-aware feature selection) |

## Key findings

**1. Up-sell opportunity is the single strongest signal.** Deals flagged as having up-sell potential win at 74% vs. 23% for those without (odds ratio ≈ 2.9, confirmed by logistic regression after controlling for other factors).

**2. Competitors and new clients both cut win rate roughly in half.** Deals with a known competitor win at ~21% vs. ~67% with none (odds ratio ≈ 0.38–0.48). New clients win at ~17% vs. ~70% for current clients (odds ratio ≈ 0.34–0.54).

**3. "Unknown" answers are themselves a warning sign.** Whenever budget allocation, purchasing-department involvement, or competitor presence was marked "Unknown" rather than a real Yes/No, win rate dropped to 14–25% — far below either actual answer. This suggests **incomplete deal qualification predicts a loss on its own**, independent of what the real answer would have been.

**4. A real, persistent sales-rep performance gap exists.** Seller 1 wins 67% of deals vs. Seller 9 at 33% — and this gap survives even after controlling for client type, lead source, and competitive situation in the logistic regression (Seller 9 and Seller 2 both keep odds ratios below 1). This is not fully explained by "harder deals."

**5. Product D is a volume problem, not just a weak spot.** It's the highest-volume product (31% of all deals) but has the lowest win rate among high-volume products (39% vs. a 51% overall average).

**6. Authority level and cross-sell flag show no meaningful relationship with outcome** (Cramér's V ≈ 0.02–0.03, not statistically significant). This is a genuine null finding, not a gap in the analysis.

**Effect size ranking (Cramér's V, strongest to weakest):**
`Up_sale (0.50) ≈ Client (0.50) > Competitors (0.44) > Source (0.41) > Seller (0.37) > Att_t_client (0.32) > Posit_statm (0.27) > Deal_type (0.25) > Purch_dept (0.23) > Budgt_alloc (0.22) > Comp_size (0.21) > Product (0.22) > Forml_tend/Strat_deal (0.19) > Scope (0.16) > Needs_def/Partnership/Growth (0.10–0.13, weak/borderline) > Cross_sale/Authority (0.02–0.03, not significant)`

**Robustness check:** 83 of 448 rows (18.5%) were exact duplicates. Removing them shifted the overall win rate from 50.7% to 47.4%, but the top 5 drivers stayed identical in rank order — the conclusions are not an artifact of duplicate records.

## Win-probability model

With only 448 deals (≈227 wins), the Events-Per-Variable rule limits how many predictors a logistic regression can support reliably (roughly 10–20 wins per parameter). Rather than use all 18 significant variables, the model uses the **6 strongest** (Up_sale, Client, Competitors, Source, Att_t_client, Seller), with any category under 10 deals collapsed into "Other" first — 19 parameters for 226 wins (EPV ≈ 12, within the recommended range).

- **Test AUC: 0.75–0.84** (varies across train/test splits due to the small, 90-deal test fold; a k-fold cross-validation would give a more stable estimate — noted as a natural next step)
- **Win-probability quintiles (scored on the full dataset, far more stable than the test-set estimate):**

| Quintile (4 = highest) | Deals | Win rate |
|---|---|---|
| 4 | 84 | 78.6% |
| 3 | 76 | 86.8% |
| 2 | 109 | 58.7% |
| 1 | 89 | 24.7% |
| 0 (lowest) | 90 | 10.0% |

The bottom and top quintiles differ by roughly **8x** in win rate — a large, clearly usable spread for prioritizing where sales effort goes.

## Recommendations

1. **Use the win-probability score to triage the pipeline.** The bottom 20% of deals by score win only 10% of the time; the top 40% win 79–87% of the time. Effort should shift toward the top tiers rather than being spread evenly.
2. **Treat incomplete qualification as a red flag, not a data gap.** Deals where budget, purchasing-department involvement, or competitor presence is still "Unknown" lose at 75–86% — flag these for a mandatory qualification call before investing further sales time.
3. **Build a distinct playbook for competitive deals.** Win rate drops from ~67% to ~21% when a competitor is present — this needs a defined competitive-response process, not the standard motion.
4. **Investigate and coach Seller 9 and Seller 2 specifically.** Their lower win rate persists after controlling for client type, source, and competition — pointing to an addressable, rep-level factor (discovery quality, qualification discipline, or deal selection).
5. **Reassess Product D's position.** It's the highest-volume product but underperforms on win rate — worth checking whether this is pricing, product-market fit, or an overlap with the underperforming reps/sources above before assuming it's the product's fault.
6. **Do not use authority level or cross-sell potential as qualification criteria.** Neither showed a meaningful relationship with the outcome in this data.

## Limitations

- 448 deals from one anonymized company; findings describe patterns in this specific historical dataset and may not generalize to other organizations or sales motions.
- All relationships are associations, not proven causation. The model includes only 6 of 18 significant variables (chosen for parsimony given the sample size), so the Seller and Product effects are not fully disentangled from each other or from Deal_type.
- No deal-value or revenue field exists in the source data, so impact is expressed in win-rate and prioritization terms rather than a dollar estimate — unlike the AHRQ-cost-based estimate used in a companion healthcare-readmission project, there is no credible external cost benchmark to apply here.
- The reported AUC (0.75–0.84) reflects real variability from a small, 90-deal test fold; a k-fold cross-validation is the natural next step for a more stable estimate.
- "Unknown" was deliberately kept as its own category rather than treated as missing data, since it's a genuine, informative response in this dataset.

## Repository structure

```
sql/
  02_driver_analysis_b2b_sqlserver.sql   -- table creation, load, driver-summary view, shortlists
python/
  01_load_explore_b2b.py                 -- load, define target, data-quality check
  03_statistical_tests_b2b.py            -- chi-square, Cramer's V, duplicate robustness check
  04_win_model_b2b.py                    -- logistic regression win-probability model
README.md
```

## Tools

SQL Server (T-SQL) · Python (pandas, scipy, scikit-learn)

---

### For a resume / CV

> Analyzed 448 real B2B sales opportunities to identify drivers of deal win/loss, using SQL for exploratory analysis and chi-square/Cramér's V testing — including a duplicate-record robustness check — to confirm findings. Built a logistic regression win-probability model (AUC 0.75–0.84) using an events-per-variable-aware feature selection approach suited to the small sample size, revealing an 8x spread in win rate across priority tiers and a sales-rep performance gap that persists after controlling for deal characteristics.
