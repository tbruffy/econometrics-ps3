#!/usr/bin/env python3
"""Reproduce all empirical results for Econometrics I Problem Set 3.

Run from the repository root: python src/analysis.py
Only the supplied workbooks are used. White covariances are HC0.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import numpy as np
import pandas as pd
import scipy
from scipy import stats
import statsmodels
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant
from types import SimpleNamespace
sm = SimpleNamespace(OLS=OLS, add_constant=add_constant)

for directory in ("results", "tables", "figures"):
    (ROOT / directory).mkdir(parents=True, exist_ok=True)

def robust_ols(y, X):
    """Check statsmodels against a direct NumPy OLS/HC0 calculation."""
    fit = sm.OLS(y, X).fit()
    hc0 = fit.get_robustcov_results(cov_type="HC0", use_t=False)
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    np.testing.assert_allclose(fit.params, b, rtol=1e-7, atol=1e-11)
    u = y - X @ b
    bread = np.linalg.inv(X.T @ X)
    V = bread @ (X.T @ (u[:, None]**2 * X)) @ bread
    np.testing.assert_allclose(hc0.cov_params(), V, rtol=5e-6, atol=1e-12)
    return fit, hc0

def wald(b, V):
    return float(b @ np.linalg.solve(V, b))

def iv_hc0(y, X, Z):
    """2SLS, structural residuals, and the explicit White sandwich."""
    Xhat = Z @ np.linalg.lstsq(Z, X, rcond=None)[0]
    bread = np.linalg.inv(Xhat.T @ X)
    b = bread @ (Xhat.T @ y)
    u = y - X @ b
    V = bread @ (Xhat.T @ (u[:, None]**2 * Xhat)) @ bread.T
    V = (V + V.T) / 2
    zz_inv = np.linalg.inv(Z.T @ Z)
    cross = X.T @ Z
    meat = Z.T @ (u[:, None]**2 * Z)
    alternative = bread @ cross @ zz_inv @ meat @ zz_inv @ cross.T @ bread.T
    np.testing.assert_allclose(V, alternative, rtol=1e-8, atol=1e-12)
    np.testing.assert_allclose(Xhat.T @ u, 0, atol=1e-10)
    assert np.linalg.matrix_rank(Z) == Z.shape[1]
    assert np.linalg.matrix_rank(Xhat) == X.shape[1]
    return b, u, V

def summary(fit, hc0, terms):
    return {
        "terms": terms, "coefficients": fit.params.tolist(),
        "standard_errors": fit.bse.tolist(),
        "standard_errors_hc0": hc0.bse.tolist(),
        "n": int(fit.nobs), "residual_df": int(fit.df_resid),
        "r_squared": float(fit.rsquared),
    }

def tabular(filename, layout, rows):
    text = ("\\begin{tabular}{" + layout + "}\n\\toprule\n"
            + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
    (ROOT / "tables" / filename).write_text(text, encoding="utf-8")

# P2: the expenditure and income series are already real.
source = ROOT / "data" / "PS4data.xls"
raw = pd.read_excel(source, engine="xlrd")
required = ["year", "quarter", "real consumption of nondurables",
            "real consumption of services", "real disposable income", "population"]
assert len(raw) == 220 and raw[required].notna().all().all()
assert (raw["population"] > 0).all()
periods = pd.PeriodIndex(
    [f"{int(y)}Q{int(q)}" for y, q in zip(raw["year"], raw["quarter"])],
    freq="Q")
assert periods.is_unique and periods.is_monotonic_increasing
assert (np.diff(periods.asi8) == 1).all()
data = pd.DataFrame({
    "quarter": periods.astype(str),
    "consumption_per_capita": (
        raw["real consumption of nondurables"] +
        raw["real consumption of services"]) / raw["population"],
    "income_per_capita": raw["real disposable income"] / raw["population"],
})
assert (data[["consumption_per_capita", "income_per_capita"]] > 0).all().all()
data["log_consumption"] = np.log(data["consumption_per_capita"])
data["log_income"] = np.log(data["income_per_capita"])
data["dlog_consumption"] = data["log_consumption"].diff()
data["dlog_income"] = data["log_income"].diff()
for lag in range(1, 5):
    data[f"consumption_lag{lag}"] = data["consumption_per_capita"].shift(lag)
for lag in range(2, 6):
    data[f"instrument_dlog_consumption_lag{lag}"] = (
        data["dlog_consumption"].shift(lag))

# AR(4), with four initial observations lost.
ar_columns = [f"consumption_lag{j}" for j in range(1, 5)]
ar_sample = data.dropna(subset=["consumption_per_capita"] + ar_columns)
assert len(ar_sample) == 216 and ar_sample["quarter"].iloc[0] == "1949Q1"
ar_y = ar_sample["consumption_per_capita"].to_numpy()
ar_X = sm.add_constant(ar_sample[ar_columns].to_numpy(), has_constant="add")
ar, ar_hc0 = robust_ols(ar_y, ar_X)
R = np.zeros((3, 5))
R[:, 2:] = np.eye(3)
ar_ftest = ar.f_test(R)
ar_F, ar_fp = float(ar_ftest.fvalue), float(ar_ftest.pvalue)
ar_W = wald(ar.params[2:], ar_hc0.cov_params()[2:, 2:])
ar_wp = float(stats.chi2.sf(ar_W, 3))
# Independently reproduce the conventional nested-model F.
restricted = sm.OLS(ar_y, ar_X[:, :2]).fit()
np.testing.assert_allclose(
    ar_F, ((restricted.ssr-ar.ssr)/3)/(ar.ssr/ar.df_resid), rtol=1e-10)

# Same 214 observations for all OLS, IV, first-stage, DWH and J comparisons.
instrument_columns = [
    f"instrument_dlog_consumption_lag{j}" for j in range(2, 6)]
iv_sample = data.dropna(
    subset=["dlog_consumption", "dlog_income"] + instrument_columns)
assert len(iv_sample) == 214
assert iv_sample["quarter"].iloc[0] == "1949Q3"
assert iv_sample["quarter"].iloc[-1] == "2002Q4"
y = iv_sample["dlog_consumption"].to_numpy()
X = sm.add_constant(iv_sample["dlog_income"].to_numpy(), has_constant="add")
Z = sm.add_constant(iv_sample[instrument_columns].to_numpy(), has_constant="add")
n = len(y)
ols, ols_hc0 = robust_ols(y, X)
b_iv, u_iv, V_iv = iv_hc0(y, X, Z)
se_iv = np.sqrt(np.diag(V_iv))

first, first_hc0 = robust_ols(X[:, 1], Z)
first_R = np.column_stack([np.zeros(4), np.eye(4)])
first_ftest = first.f_test(first_R)
first_F, first_fp = float(first_ftest.fvalue), float(first_ftest.pvalue)
first_W = wald(first.params[1:], first_hc0.cov_params()[1:, 1:])
first_wp = float(stats.chi2.sf(first_W, 4))

# HC0 regression-form DWH. Under H0 rho=0, estimating the first-stage
# residual contributes no first-order generated-regressor correction.
aug_X = np.column_stack([X, first.resid])
aug, aug_hc0 = robust_ols(y, aug_X)
dwh_W = float(aug.params[-1]**2 / aug_hc0.cov_params()[-1, -1])
dwh_p = float(stats.chi2.sf(dwh_W, 1))

# Robust overidentification: re-estimate by efficient two-step GMM.
# The weight uses uncentered moment second moments from 2SLS residuals.
S = Z.T @ (u_iv[:, None]**2 * Z) / n
D = Z.T @ X / n
zy = Z.T @ y / n
W = np.linalg.inv(S)
b_gmm = np.linalg.solve(D.T @ W @ D, D.T @ W @ zy)
gbar = Z.T @ (y - X @ b_gmm) / n
J = float(n * gbar @ W @ gbar)
J_df = Z.shape[1] - X.shape[1]
J_p = float(stats.chi2.sf(J, J_df))
np.testing.assert_allclose(D.T @ W @ gbar, 0, atol=1e-9)
assert J >= 0 and J_df == 3
zcrit = float(stats.norm.ppf(.975))
iv_z = b_iv / se_iv
iv_p = 2 * stats.norm.sf(np.abs(iv_z))
iv_ci = np.column_stack([b_iv-zcrit*se_iv, b_iv+zcrit*se_iv])
gamma_one_W = float(((b_iv[1]-1)/se_iv[1])**2)
gamma_one_p = float(stats.chi2.sf(gamma_one_W, 1))

# P3(d): the first level is the initial condition t=0, not an increment.
sp_source = ROOT / "data" / "SP500Index.xlsx"
sp_raw = pd.read_excel(sp_source, sheet_name="WRDS", engine="openpyxl")
assert sp_raw.shape == (702, 2)
sp = pd.DataFrame({
    "date": pd.to_datetime(sp_raw.iloc[:, 0].astype(str), format="%Y%m%d"),
    "index": sp_raw.iloc[:, 1].astype(float),
})
assert sp["date"].is_unique and sp["date"].is_monotonic_increasing
assert (sp["index"] > 0).all()
month_numbers = sp["date"].dt.to_period("M").astype("int64")
assert (month_numbers.diff().dropna() == 1).all()
sp["normalized_log_level"] = np.log(sp["index"] / sp["index"].iloc[0])
sp["monthly_log_return"] = np.log(sp["index"]).diff()
returns = sp["monthly_log_return"].dropna().to_numpy()
T = len(returns)
assert T == 701 and len(sp) == T+1
drift = float(returns.mean())
variance = float(np.mean((returns-drift)**2))
volatility = float(np.sqrt(variance))
np.testing.assert_allclose(
    drift, sp["normalized_log_level"].iloc[-1]/T, rtol=1e-12, atol=1e-15)

results = {
    "conventions": {
        "consumption": "(real nondurables + real services) / population",
        "income": "real disposable income / population",
        "levels_units": "Unscaled ratios of workbook source units",
        "white_covariance": "HC0; no degrees-of-freedom adjustment",
        "iv_instruments": ["constant"] + instrument_columns,
        "time_series_inference": "White HC0, without HAC correction",
        "hansen": "Two-step GMM; uncentered S from 2SLS residuals",
    },
    "data": {
        "consumption_observations": len(data),
        "consumption_start": data["quarter"].iloc[0],
        "consumption_end": data["quarter"].iloc[-1],
        "source_sha256": {
            "PS4data.xls": hashlib.sha256(source.read_bytes()).hexdigest(),
            "SP500Index.xlsx": hashlib.sha256(sp_source.read_bytes()).hexdigest(),
        },
    },
    "ar4": {
        **summary(ar, ar_hc0, ["Intercept"]+ar_columns),
        "start": ar_sample["quarter"].iloc[0],
        "end": ar_sample["quarter"].iloc[-1],
        "extra_lags_F": ar_F, "extra_lags_F_df": [3, int(ar.df_resid)],
        "extra_lags_F_p": ar_fp, "extra_lags_hc0_Wald": ar_W,
        "extra_lags_hc0_Wald_df": 3, "extra_lags_hc0_Wald_p": ar_wp,
    },
    "ols_same_sample": summary(ols, ols_hc0, ["Intercept", "dlog_income"]),
    "iv_2sls": {
        "terms": ["Intercept", "dlog_income"], "coefficients": b_iv.tolist(),
        "standard_errors_hc0": se_iv.tolist(), "covariance_hc0": V_iv.tolist(),
        "normal_z": iv_z.tolist(), "normal_p": iv_p.tolist(),
        "confidence_interval_95": iv_ci.tolist(), "n": n,
        "start": iv_sample["quarter"].iloc[0],
        "end": iv_sample["quarter"].iloc[-1],
        "slope_equals_one_Wald": gamma_one_W,
        "slope_equals_one_p": gamma_one_p,
    },
    "first_stage": {
        **summary(first, first_hc0, ["Intercept"]+instrument_columns),
        "excluded_F": first_F, "excluded_F_df": [4, int(first.df_resid)],
        "excluded_F_p": first_fp, "excluded_hc0_Wald": first_W,
        "excluded_hc0_Wald_df": 4, "excluded_hc0_Wald_p": first_wp,
        "excluded_hc0_Wald_divided_by_four": first_W/4,
    },
    "endogeneity_test": {
        "method": "HC0 residual-inclusion Durbin-Wu-Hausman",
        "residual_coefficient": float(aug.params[-1]),
        "residual_standard_error_hc0": float(aug_hc0.bse[-1]),
        "statistic": dwh_W, "reference": "chi-square", "df": 1, "p": dwh_p,
    },
    "overidentification_test": {
        "method": "Two-step efficient GMM Hansen J",
        "gmm_coefficients": b_gmm.tolist(), "statistic": J,
        "reference": "chi-square", "df": J_df, "p": J_p,
    },
    "sp500": {
        "level_observations": len(sp), "increments_T": T,
        "first_date": sp["date"].iloc[0].strftime("%Y-%m-%d"),
        "last_date": sp["date"].iloc[-1].strftime("%Y-%m-%d"),
        "first_index": float(sp["index"].iloc[0]),
        "last_index": float(sp["index"].iloc[-1]),
        "drift_ml": drift, "variance_ml": variance, "volatility_ml": volatility,
        "monthly_geometric_price_growth": float(np.expm1(drift)),
        "annual_geometric_price_growth": float(np.expm1(12*drift)),
        "annualized_volatility": float(volatility*np.sqrt(12)),
        "dividends": "Excluded by the course source",
    },
    "software": {
        "numpy": np.__version__, "pandas": pd.__version__,
        "scipy": scipy.__version__, "statsmodels": statsmodels.__version__,
    },
}
(ROOT / "results/results.json").write_text(
    json.dumps(results, indent=2, allow_nan=False)+"\n", encoding="utf-8")
data["sample_ar4"] = data.index.isin(ar_sample.index)
data["sample_iv"] = data.index.isin(iv_sample.index)
data.to_csv(ROOT / "results/prepared_consumption.csv", index=False)
sp.to_csv(ROOT / "results/sp500_returns.csv", index=False, date_format="%Y-%m-%d")
regression_rows = []
models = [
    ("AR4", ["Intercept"]+ar_columns, ar.params, ar.bse,
     "Conventional", len(ar_sample)),
    ("AR4", ["Intercept"]+ar_columns, ar.params, ar_hc0.bse,
     "White HC0", len(ar_sample)),
    ("OLS_same_sample", ["Intercept", "dlog_income"],
     ols.params, ols_hc0.bse, "White HC0", n),
    ("2SLS", ["Intercept", "dlog_income"], b_iv, se_iv, "White HC0", n),
    ("First_stage", ["Intercept"]+instrument_columns,
     first.params, first_hc0.bse, "White HC0", n),
]
for model, terms, b, se, covariance, nn in models:
    for term, coefficient, standard_error in zip(terms, b, se):
        regression_rows.append({
            "model": model, "term": term, "coefficient": coefficient,
            "standard_error": standard_error, "covariance": covariance, "n": nn})
pd.DataFrame(regression_rows).to_csv(ROOT / "results/regressions.csv", index=False)
test_rows = [
    ("AR4 extra lags", ar_F, "F", 3, int(ar.df_resid), ar_fp),
    ("AR4 extra lags HC0", ar_W, "chi-square", 3, None, ar_wp),
    ("First-stage excluded instruments", first_F, "F", 4,
     int(first.df_resid), first_fp),
    ("First-stage excluded instruments HC0", first_W, "chi-square", 4,
     None, first_wp),
    ("Exogeneity DWH HC0", dwh_W, "chi-square", 1, None, dwh_p),
    ("Overidentification Hansen J", J, "chi-square", 3, None, J_p),
    ("2SLS slope equals one", gamma_one_W, "chi-square", 1, None, gamma_one_p),
]
pd.DataFrame(test_rows, columns=[
    "test", "statistic", "reference", "numerator_df", "denominator_df",
    "p_value"]).to_csv(ROOT / "results/tests.csv", index=False)

ar_rows = [r"Regressor & Estimate & Conventional SE & White HC0 SE \\",
           r"\midrule"]
labels = [r"Constant", r"$C_{t-1}$", r"$C_{t-2}$", r"$C_{t-3}$", r"$C_{t-4}$"]
for label, b, se, hcse in zip(labels, ar.params, ar.bse, ar_hc0.bse):
    digits = 8 if label == "Constant" else 6
    ar_rows.append(f"{label} & {b:.{digits}f} & {se:.{digits}f} & "
                   f"{hcse:.{digits}f}" + r" \\")
ar_rows += [r"\midrule", f"Observations & {len(ar_sample)} & &" + r" \\"]
tabular("consumption_ar.tex", "lrrr", ar_rows)

iv_rows = [
    r" & \multicolumn{2}{c}{OLS} & \multicolumn{2}{c}{2SLS} \\",
    r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}",
    r"Regressor & Estimate & White HC0 SE & Estimate & White HC0 SE \\",
    r"\midrule",
]
for i, label in enumerate([r"Constant", r"$\Delta\log Y_t$"]):
    iv_rows.append(f"{label} & {ols.params[i]:.6f} & {ols_hc0.bse[i]:.6f} & "
                   f"{b_iv[i]:.6f} & {se_iv[i]:.6f}" + r" \\")
iv_rows += [r"\midrule", f"Observations & {n} & & {n} &" + r" \\"]
tabular("consumption_iv.tex", "lrrrr", iv_rows)
tabular("consumption_tests.tex", "lrrr", [
    r"Test & Statistic & df & $p$-value \\", r"\midrule",
    f"Hall lag restrictions ($F$) & {ar_F:.6f} & $(3,211)$ & {ar_fp:.8f}" + r" \\",
    f"Exogeneity (HC0 $\\chi^2$) & {dwh_W:.6f} & $1$ & {dwh_p:.6f}" + r" \\",
    f"Overidentification (Hansen $J$) & {J:.6f} & $3$ & {J_p:.6f}" + r" \\",
])
macros = {
    "SPDrift": f"{drift:.10f}", "SPVariance": f"{variance:.10f}",
    "SPVolatility": f"{volatility:.10f}", "SPIncrements": str(T),
    "ARFStat": f"{ar_F:.6f}", "ARFPValue": f"{ar_fp:.8f}",
    "IVSlope": f"{b_iv[1]:.6f}", "IVSlopeSE": f"{se_iv[1]:.6f}",
    "DWHStat": f"{dwh_W:.6f}", "DWHPValue": f"{dwh_p:.6f}",
    "HansenStat": f"{J:.6f}", "HansenPValue": f"{J_p:.6f}",
}
(ROOT / "results/macros.tex").write_text(
    "% Generated by src/analysis.py.\n" +
    "".join("\\newcommand{\\"+key+"}{"+value+"}\n" for key, value in macros.items()),
    encoding="utf-8")
print(json.dumps({
    "AR4_F": ar_F, "AR4_p": ar_fp,
    "IV_coefficients": b_iv.tolist(), "IV_HC0_SE": se_iv.tolist(),
    "first_stage_F": first_F, "DWH": [dwh_W, dwh_p], "Hansen_J": [J, J_p],
    "SP500": {"T": T, "drift": drift, "variance": variance,
               "volatility": volatility},
}, indent=2))
