# %% [markdown]
# # Win-probability model (B2B sales)
# With only 448 deals (vs. 70,000 in the healthcare project), we can't throw
# every significant variable into the model -- the Events Per Variable (EPV)
# rule says we need roughly 10-20 wins per predictor to keep the model
# stable. With ~227 wins, that caps us at about 15-22 parameters. So this
# script:
#   1. Uses only the 6 STRONGEST drivers (Cramer's V > 0.35), not all 18
#   2. Collapses any category with fewer than 10 deals into "Other" first,
#      so no dummy variable is estimated from a near-empty group
#   3. Uses an 80/20 train/test split (not 70/30) to keep more training data

# %% Load
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

df = pd.read_csv("b2b_sales_clean.csv")

# %% Collapse rare categories (< 10 deals) into "Other" before modeling
def collapse_rare(series, min_n=10):
    counts = series.value_counts()
    keep = counts[counts >= min_n].index
    return series.where(series.isin(keep), "Other")

feature_cols = ["Up_sale", "Client", "Competitors", "Source", "Att_t_client", "Seller"]
data = df[feature_cols + ["won"]].copy()
for col in feature_cols:
    data[col] = collapse_rare(data[col])
    print(col, "->", data[col].value_counts().to_dict())

# %% One-hot encode
X = pd.get_dummies(data[feature_cols], drop_first=True)
y = data["won"]
print(f"\n{X.shape[1]} parameters for {y.sum()} wins -> EPV = {y.sum() / X.shape[1]:.1f}")

# %% Train/test split (80/20 -- more training data for a smaller dataset)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print("Train:", len(X_train), "| Test:", len(X_test))

# %% Fit on train, evaluate on test
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

test_probs = model.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, test_probs)
print(f"\nTest AUC: {auc:.3f}")

# %% Odds ratios
odds_ratios = pd.DataFrame({
    "feature": X.columns,
    "odds_ratio": np.exp(model.coef_[0]),
}).sort_values("odds_ratio", ascending=False)
print("\n=== Odds ratios (vs. each variable's reference category) ===")
print(odds_ratios.to_string(index=False))

# %% [markdown]
# NOTE: with only 6 categorical predictors, deals share a limited number of
# distinct feature combinations (96 unique profiles out of 447 deals here),
# so many deals get the exact same predicted probability. On the small test
# fold (~90 rows) this creates ties that break a clean 5-way quantile split
# -- so we build the quintile table on the FULL dataset below instead, which
# is also the more useful version: it's the actual prioritization tool.

# %% Final: refit on all data, score every deal (for reporting / prioritization)
final_model = LogisticRegression(max_iter=1000)
final_model.fit(X, y)
data["win_score"] = final_model.predict_proba(X)[:, 1]
data["win_quintile"] = pd.qcut(data["win_score"], 5, labels=False, duplicates="drop")

full_summary = (
    data.groupby("win_quintile")
    .agg(deals=("won", "size"), wins=("won", "sum"))
    .sort_index(ascending=False)
)
full_summary["win_rate_pct"] = (100 * full_summary["wins"] / full_summary["deals"]).round(1)
print("\n=== Win-probability quintiles (4 = highest), full dataset ===")
print(full_summary)

data.to_csv("b2b_scored.csv", index=False)
print("\nSaved b2b_scored.csv")