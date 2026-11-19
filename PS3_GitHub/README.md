# Econometrics I — Problem Set 3

Typed LaTeX solutions to all five problems, with reproducible Python analysis for consumption and the S&P 500.

Start with [UPLOAD_INSTRUCTIONS.md](UPLOAD_INSTRUCTIONS.md). All empirical outputs are included; rerunning Python is optional.

## Files

- `main.tex`: compile this document.
- `config.tex`: author name and GitHub repository URL.
- `sections/`: solutions, organized by question.
- `data/`: the two original workbooks and original question PDF.
- `src/analysis.py`: reads the original workbooks and regenerates empirical tables and numerical results.
- `results/`: machine-readable results and prepared data.
- Generated LaTeX tables are in the tables folder.
- `submission/PS3_Travis_Bruffy.pdf`: compiled PDF.
- `requirements.txt`: versions used for the checked run.

The PDF's repository link is deliberately unset until the submission repository has been created. Update `config.tex` and recompile before submitting.

## Reproduce the empirical analysis

Use Python 3.12 in a fresh virtual environment:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/analysis.py
```

Run these commands from this directory. The script requires only the supplied workbooks; it does not download data. White standard errors use HC0 with no finite-sample correction. The IV sandwich uses structural 2SLS residuals. The robust Hansen test uses the minimized two-step efficient GMM criterion.

The consumption sample is 1948Q1–2002Q4. Consumption equals real nondurables plus real services, divided by population; income equals real disposable income divided by population. AR(4) uses 216 observations. The IV regression uses 214 observations, with a constant and consumption-growth lags 2 through 5 as instruments. The real series are not deflated again.

The S&P workbook has 702 monthly levels, January 1960–June 2018, so the random-walk MLE uses 701 increments and divisor 701.

## Compile the submission

In Overleaf, use `main.tex` as the main document and pdfLaTeX as the compiler. No Python execution is needed in Overleaf.

With a local TeX Live installation:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Alternatively, Tectonic can compile the same source:

```sh
tectonic main.tex
```

The checked local build used Tectonic 0.17.0. The portable repository excludes the downloaded compiler, virtual environment, caches, and LaTeX auxiliary files.

## Key empirical checks

| Quantity | Checked result |
| --- | ---: |
| Hall extra-lag F(3,211) | 8.409997 |
| Hall test p-value | 0.0000263641 |
| IV income-growth slope | 0.43692450 |
| White HC0 slope SE | 0.20255470 |
| First-stage F(4,209) | 2.509115 |
| Robust exogeneity test p-value | 0.28567257 |
| Robust Hansen J p-value | 0.16553510 |
| S&P monthly drift | 0.005548394684 |
| S&P monthly innovation SD | 0.042180346074 |

The first stage is weak; the solution discusses the resulting limitations of conventional IV inference.

## Provenance

Inputs are the course files supplied for this assignment, preserved under their original base filenames in `data/`. The question sheet is `PS3_2025_LBS.pdf`, by Alexei Onatski. The two workbooks are `PS4data.xls` (the filename used by Problem 2) and `SP500Index.xlsx`. No additional financial or macroeconomic series were substituted.
