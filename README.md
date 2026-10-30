# Market Basket Analysis for Online Retail Product Recommendations

**Teresa Ferrill | DSC 680 — Applied Data Science | Project 2**

## Project Overview

This project uses transaction data from the UCI Online Retail dataset to identify products frequently purchased together and evaluate product recommendations. The intended audience is retail merchandising and marketing teams considering cross-selling opportunities and potential product bundles.

The analysis uses FP-growth and association rules. It evaluates whether recommendations recover a hidden product within a later shopping basket more often than a popular-product baseline.

Unlike my customer segmentation project, which uses RFM analysis and K-means to group customers, this project examines product relationships within invoices.

## Research Questions

1. Which product combinations occur frequently in valid shopping baskets?
2. Which product relationships exceed what would be expected from individual product popularity?
3. Do association-rule recommendations recover hidden products more often than a popular-product baseline, and how often can the system provide recommendations?

## Key Results

Results below are from the final chronological test period, October 1–December 9, 2011.

| Measure | Result |
|---|---:|
| Eligible test baskets | 5,183 |
| Association-rule hit rate at 5 | 9.84% |
| Popular-product baseline hit rate at 5 | 2.01% |
| Absolute improvement | 7.83 percentage points |
| Rule recommendation coverage | 90.16% |
| Final directional association rules | 10,842 |
| Test targets unseen during development | 340 |

**Hit rate at 5** is the percentage of eligible baskets whose hidden product appears among up to five recommendations. **Coverage** is the percentage receiving at least one rule-based recommendation. Coverage is not accuracy. Baskets without recommendations count as misses in the overall hit rate.

The paired basket bootstrap gives an approximate 95% interval of 7.00–8.64 percentage points for the improvement. Repeated customers and time dependence limit interpretation of this interval.

These results measure offline basket completion. They do not establish purchase order, next-purchase behavior, or an increase in sales.

## Dataset

- **Source:** [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail)
- **DOI:** https://doi.org/10.24432/C5BW33
- **Coverage:** December 1, 2010–December 9, 2011
- **Original size:** 541,909 transaction lines
- **Retained:** 522,504 lines, 19,773 baskets, and 3,900 product codes
- **License:** Creative Commons Attribution 4.0

The original workbook is included at [`data/Online Retail.xlsx`](data/Online%20Retail.xlsx). If downloading the data separately, obtain the [UCI ZIP archive](https://archive.ics.uci.edu/static/public/352/online+retail.zip), extract `Online Retail.xlsx`, and place it in `data/` with that exact filename.

Key fields include InvoiceNo, StockCode, Description, Quantity, InvoiceDate, and UnitPrice. Customer identifiers are not required for basket construction. Transactions with missing CustomerID values are retained when other validity criteria are satisfied.

## Data Preparation

The script preserves the original workbook and applies these sequential exclusions:

| Step | Removed lines |
|---|---:|
| Missing invoice number, product code, or date | 0 |
| Cancellation invoice | 9,288 |
| Nonpositive or missing quantity or price | 2,517 |
| Nonmerchandise or atypical product code | 2,379 |
| Exact duplicate row | 5,221 |

The product-code filter accepts five digits followed by optional letters. It can exclude unusual legitimate items, so the exclusions are documented rather than treated as definitive merchandise classifications. Each invoice becomes a basket of distinct product codes; repeated lines or quantities do not increase product presence.

The retained data include 131,354 lines without CustomerID values. The analysis represents positive purchasing activity, not net revenue after returns.

## Methods and Evaluation

- **Training:** invoices before August 1, 2011; 11,044 baskets.
- **Validation:** August 1–September 30, 2011; 3,157 baskets.
- **Final testing:** October 1–December 9, 2011; 5,572 baskets, including 5,183 with at least two distinct products.

FP-growth uses the 300 most frequent products in the fitting period and itemsets containing at most two products. Six settings compare minimum support of 0.5% or 1% and minimum lift of 1, 1.5, or 2. Validation selects **0.5% support and 1.5 lift**. Rules are then refitted on all pre-October invoices. Final test outcomes are not used to choose settings.

A stable invoice hash determines one hidden product in each eligible test basket. The remaining products form the visible basket. Recommendations exclude visible products and rank candidates by confidence, then lift, support, and product code. The popularity baseline uses development-period basket frequencies and excludes the same visible products.

Test baskets are not restricted to the 300 candidate products. Unseen targets remain in the overall evaluation. See [`analysis.py`](analysis.py) for the full preparation, fitting, and evaluation code.

## Repository Contents

| Path | Contents |
|---|---|
| [`analysis.py`](analysis.py) | Complete analysis and figure generation |
| [`notebook/market_basket_analysis.ipynb`](notebook/market_basket_analysis.ipynb) | Notebook that runs the script and displays results |
| [`data/`](data/) | Original Online Retail workbook |
| [`results/`](results/) | Figures, cleaning audit, validation grid, rules, predictions, and summary |
| [`requirements.txt`](requirements.txt) | Required Python packages |
| [`environment_versions.json`](environment_versions.json) | Recorded package versions; verify against the environment used for a new run |

## How to Run

Download or clone the entire repository and retain its folder structure. The notebook depends on `analysis.py`; downloading the notebook alone is insufficient.

### From a Terminal

Open a terminal in the repository root:

```bash
python -m pip install -r requirements.txt
python analysis.py
```

To open the notebook instead:

```bash
jupyter notebook notebook/market_basket_analysis.ipynb
```

Select the Python environment where the requirements were installed, restart the kernel after installation if needed, and run all cells.

### From Jupyter

To identify the active Python environment:

```python
import sys
print(sys.executable)
print(sys.version)
```

If the notebook's working directory is `notebook/`, install requirements in a temporary code cell:

```python
%pip install -r ../requirements.txt
```

If its working directory is the repository root, use:

```python
%pip install -r requirements.txt
```

Restart the kernel after installation, then run all cells. The notebook locates the repository root from either location.

### Runtime and Outputs

A complete run took approximately **2.53 minutes** in the recorded local run; runtime varies by hardware and environment. The execution cell runs the entire pipeline, including Excel loading, six validation settings, final evaluation, 2,000 bootstrap resamples, and figure generation. Existing results are overwritten when the pipeline runs.

After the analysis finishes, the later display cells can be rerun without rerunning the analysis cell. Save the notebook with its completed outputs for review.

## Results Files

| File | Purpose |
|---|---|
| [`cleaning_audit.csv`](results/cleaning_audit.csv) | Sequential excluded-row counts |
| [`validation.csv`](results/validation.csv) | Six candidate settings and validation metrics |
| [`rules.csv`](results/rules.csv) | Final product rules with support, confidence, lift, codes, and names |
| [`test_predictions.csv`](results/test_predictions.csv) | Hidden targets, recommendations, hits, and coverage by eligible invoice |
| [`summary.json`](results/summary.json) | Dataset counts, selected settings, and final metrics |
| [`baskets.pkl`](results/baskets.pkl) | Generated intermediate basket data; not required as an input |

Five PNG figures summarize monthly invoices, basket sizes, popular products, recommendation performance, and coverage.

## Business Interpretation and Limitations

The rules outperform the popularity baseline for hidden-item recovery, supporting further merchandising review of product pairings. Most hidden items are still not recovered. Potential implementation should include product suitability and inventory checks, a fallback for baskets without rules, and prospective testing before claiming business benefits.

The data describe one historical retailer, including wholesale customers. Seasonality, large baskets, product filtering, and popular-product concentration may affect recommendations. Inventory availability, promotions, margins, and shopping sequence are not observed. The December period is incomplete.

Customer identifiers are not used in recommendations or published result tables. Cleaning decisions and evaluation limitations are documented. Association does not establish causation, and offline performance does not demonstrate increased conversion, retention, or revenue.

## References

Chen, D. (2015). *Online retail* [Data set]. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33

Han, J., Pei, J., & Yin, Y. (2000). Mining frequent patterns without candidate generation. *ACM SIGMOD Record, 29*(2), 1–12. https://doi.org/10.1145/335191.335372
