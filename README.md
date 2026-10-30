# Online Retail Market Basket Analysis

Run `python -m pip install -r requirements.txt`, then `python analysis.py`, or open `market_basket_analysis.ipynb` and run all cells.

Place the original `Online Retail.xlsx` in `data/`. Download: https://archive.ics.uci.edu/static/public/352/online+retail.zip . Source: Chen (2015), https://doi.org/10.24432/C5BW33, CC BY 4.0.

Results include the cleaning audit, validation grid, rules, final test predictions, summary and five figures. The test set is used only after validation selects settings. Hit rate counts no-recommendation cases as misses.

The notebook calls the included analysis.py; retain both files. No customer IDs are published in results. Predictions identify invoices and products for reproducibility.
