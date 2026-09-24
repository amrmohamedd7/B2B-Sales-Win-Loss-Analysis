# %% [markdown]
# # Step: Statistical testing (B2B sales)
# Confirms which SQL findings are real vs. noise, and ranks them by effect
# size (Cramer's V), not just p-value. With only 447 deals total, some
# categories are too small for chi-square to be reliable -- this script
# flags that explicitly instead of hiding it.

# %% Load
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

df = pd.read_csv("b2b_sales_clean.csv")
print("Rows:", len(df), "| Overall win rate:", round(df["won"].mean() * 100, 2), "%")

# %% Chi-square + Cramer's V, with a validity flag
def chi_square_test(data, col, target="won", min_expected=5):
    table = pd.crosstab(data[col], data[target])
    chi2, p, dof, expected = chi2_contingency(table)
    n = table.values.sum()
    min_dim = min(table.shape) - 1
    cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else np.nan
    pct_low_expected = round(100 * (expected < min_expected).mean(), 1)
    return {
        "variable": col, "chi2": round(chi2, 1), "dof": dof, "p_value": p,
        "cramers_v": round(cramers_v, 4), "n": n,
        "pct_cells_low_expected": pct_low_expected,   # >0 means take the result with caution
    }

dimensions = [
    "Authority", "Comp_size", "Competitors", "Purch_dept", "Partnership",
    "Budgt_alloc", "Forml_tend", "Growth", "Posit_statm", "Source", "Client",
    "Scope", "Strat_deal", "Cross_sale", "Up_sale", "Deal_type", "Needs_def",
    "Att_t_client",
]

results = pd.DataFrame([chi_square_test(df, col) for col in dimensions])
results["p_value_fmt"] = results["p_value"].apply(lambda p: "<0.001" if p < 0.001 else round(p, 4))
results = results.sort_values("cramers_v", ascending=False)
print("\n=== Ranked by effect size (Cramer's V) ===")
print(results[["variable", "cramers_v", "chi2", "dof", "p_value_fmt", "pct_cells_low_expected", "n"]].to_string(index=False))
print("\npct_cells_low_expected > 0 means some categories are too small for a fully")
print("reliable chi-square result on that variable -- note this if you cite it.")

# %% Seller and Product: filter to groups with enough deals first (matches the
# SQL >=10-deal threshold), since most sellers/products are too small to test
for col in ["Seller", "Product"]:
    counts = df[col].value_counts()
    keep = counts[counts >= 10].index
    sub = df[df[col].isin(keep)]
    res = chi_square_test(sub, col)
    p_fmt = "<0.001" if res["p_value"] < 0.001 else round(res["p_value"], 4)
    print(f"\n{col} (groups with >=10 deals only, n={res['n']}): "
          f"Cramer's V={res['cramers_v']}, chi2={res['chi2']}, p={p_fmt}")

# %% Duplicate-row robustness check (promised in step 1)
# Does the headline picture change if we treat exact duplicate rows as one deal?
dupe_free = df.drop_duplicates(subset=df.columns.drop("won"))
print(f"\n=== Robustness check: with duplicates removed ===")
print(f"Rows: {len(df)} -> {len(dupe_free)} "
      f"({len(df) - len(dupe_free)} duplicate rows dropped)")
print(f"Overall win rate: {round(100*df['won'].mean(),2)}% -> {round(100*dupe_free['won'].mean(),2)}%")

check_results = pd.DataFrame([chi_square_test(dupe_free, col) for col in dimensions])
check_results = check_results.sort_values("cramers_v", ascending=False)
print("\nTop 5 drivers, duplicates removed:")
print(check_results[["variable", "cramers_v"]].head(5).to_string(index=False))
print("\nCompare this ranking with the main one above -- if the top few variables")
print("are the same, the duplicate rows aren't driving the conclusions.")

# %% Save
results.drop(columns="p_value_fmt").to_csv("b2b_statistical_test_results.csv", index=False)
print("\nSaved b2b_statistical_test_results.csv")
# %%
