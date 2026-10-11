# Personal Spending Explorer

A local dashboard for exploring personal expenses in **Canadian dollars (CAD)**. It opens with 192 fictional transactions from April–September 2026, so no personal CSV or API key is needed.

## Run the app

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```sh
git clone https://github.com/jlx339/personal-spending-explorer.git
cd personal-spending-explorer
uv sync --locked
uv run streamlit run app.py
```

Python 3.11 is selected by `.python-version`; uv can download it if needed. Open the local URL printed by Streamlit, normally `http://localhost:8501`. Press Control+C in the terminal to stop the app.

## Features

- Total spending, monthly average, transaction count, and largest expense.
- Interactive charts for monthly trends, categories, and top merchants.
- Filters for dates, categories, and payment methods.
- Merchant search and download of displayed transactions.
- CSV upload with validation, plus sample data and reset controls.

Sidebar filters update the whole dashboard. Merchant search affects only the table and its download. Monthly average includes every calendar month touched by the selected date range, including months with no expenses. Calculations use integer cents.

## Run tests

```sh
uv run pytest
```

Tests cover CSV validation, spending calculations, filters, dataset replacement, and the Streamlit interface. To recreate the same fictional sample CSV:

```sh
uv run python -m scripts.generate_sample_data
```

## CSV format

```csv
date,merchant,category,amount,payment_method
2026-04-02,Corner Market,Groceries,64.25,Debit
2026-04-03,City Transit,Transport,12.00,Credit
```

Upload a UTF-8 CSV up to 5 MB containing all five columns. Use `YYYY-MM-DD` dates and positive CAD amounts with at most two decimal places and 15 whole digits. Merchant, category, and payment method cannot be blank. Extra columns are ignored with a notice; duplicate transactions are preserved.

Invalid uploads show an error and keep the previous valid dataset. Income, refunds, currency conversion, and bank-specific CSV formats are not supported. Uploaded records stay in session memory and are not saved to disk or sent to an external service. Reloading the browser starts a new demo session.

## Files

- `app.py`: entry point and sidebar controls.
- `components/`: dashboard metrics, charts, table, and downloads.
- `utils/`: CSV validation, spending calculations, and session handling.
- `sample_data/sample_spending.csv`: fictional demo transactions.
- `.streamlit/config.toml`: theme and upload limit.
- `pyproject.toml`, `uv.lock`, and `.python-version`: dependency and Python setup.

- `tests/`: automated checks for data and dashboard behavior.
- `scripts/`: reproducible sample-data generator used by the tests.
