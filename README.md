# CoinGecko Tokenized Commodities Python Toolkit (Debug-First v1)

Debug-first Python reference repository for tracking tokenized commodity data (PAXG, XAUT, and category peers) using CoinGecko API endpoints.

This repository is designed for article-author validation first:
- verbose diagnostics
- schema-shape checks
- reproducible CSV/JSON/chart artifacts

## Scope

Python-only implementation.

## Endpoints Covered

- `GET /coins/categories/list`
- `GET /coins/markets`
- `GET /simple/price`
- `GET /coins/{id}`
- `GET /coins/{id}/market_chart`
- `GET /coins/{id}/ohlc`
- `GET /coins/{id}/ohlc/range` (paid plan only)

## Repository Structure

```text
coingecko-tokenized-commodities-python/
├── config.py
├── requirements.txt
├── .env.example
├── docs/
│   └── schema_lock.md
├── scripts/
│   ├── _http.py
│   ├── _validate.py
│   ├── 01_discover_categories.py
│   ├── 02_list_markets.py
│   ├── 03_simple_price.py
│   ├── 04_coin_detail.py
│   ├── 05_market_chart.py
│   ├── 06_ohlc_chart.py
│   ├── 07_weekend_gap_view.py
│   ├── 08_ohlc_range_pro.py
│   └── smoke_test.py
└── output/
    ├── json/
    ├── csv/
    └── charts/
```

## Quick Start

1. Clone and install dependencies:

```bash
git clone https://github.com/cg-brianlsh/coingecko-tokenized-commodities-python.git
cd coingecko-tokenized-commodities-python
pip install -r requirements.txt
```

2. Configure environment:

```bash
cp .env.example .env
```

Set your key in `.env`:

```ini
COINGECKO_API_KEY=CG-your_api_key_here
USE_PRO_API=false
```

3. Run smoke test:

```bash
python scripts/smoke_test.py --debug --strict-schema --save-raw
```

## Script Commands

### 01 Discover Category IDs

```bash
python scripts/01_discover_categories.py --contains tokenized --debug --strict-schema
```

### 02 List Market Data by Category

```bash
python scripts/02_list_markets.py --category tokenized-gold --vs-currency usd --debug --strict-schema
```

### 03 Fetch Real-Time Simple Price

```bash
python scripts/03_simple_price.py --ids pax-gold,tether-gold --vs-currency usd --debug --strict-schema
```

### 04 Fetch Coin Detail

```bash
python scripts/04_coin_detail.py --coin-id pax-gold --vs-currency usd --debug --strict-schema
```

### 05 Build Market Chart Artifacts

```bash
python scripts/05_market_chart.py --coin-id pax-gold --days 30 --debug --strict-schema
```

### 06 Build OHLC Artifacts

```bash
python scripts/06_ohlc_chart.py --coin-id pax-gold --days 30 --debug --strict-schema
```

### 07 Build Weekend Gap View

```bash
python scripts/07_weekend_gap_view.py --coin-id pax-gold --days 30 --debug --strict-schema
```

Optional input from pre-generated CSV:

```bash
python scripts/07_weekend_gap_view.py --input-csv output/csv/pax-gold_market_chart_30d.csv --days 30 --debug
```

### 08 Fetch OHLC Range (Paid Plan)

```bash
python scripts/08_ohlc_range_pro.py --coin-id pax-gold --from 2025-01-01 --to 2025-02-01 --interval daily --debug --strict-schema
```

If `USE_PRO_API=false`, this script exits with a clear paid-plan gate message.

## Debug Flags

All scripts share:

- `--debug`: verbose logs (URL, status, latency, response preview)
- `--strict-schema`: fail immediately on schema-shape mismatches
- `--save-raw`: save raw request/response snapshots to `output/json/`
- `--timeout`: override request timeout
- `--retries`: override retry attempts
- `--out-dir`: change artifact base directory (default `output`)

## Expected Output (Schema/Artifact Based)

No fixed numeric values are assumed.

### Schema Expectations

- Categories: list of objects with `category_id` and `name`
- Markets: list of objects with `id,name,symbol,current_price,market_cap,total_volume,price_change_percentage_24h` (numeric market fields may be `null`)
- Simple price: top-level object keyed by requested IDs, nested keys include `usd`, `usd_market_cap`, `usd_24h_change`
- Coin detail: nested paths include
  - `market_data.current_price.usd`
  - `market_data.ath.usd`
  - `market_data.total_volume.usd`
  - `asset_platform_id`, `platforms`, `detail_platforms`
- Market chart: top-level keys `prices`, `market_caps`, `total_volumes`; each row `[timestamp_ms, value]`
- OHLC / OHLC range: list of `[timestamp, open, high, low, close]`

### Artifact Expectations

After smoke test, expect files such as:

- `output/json/smoke_report.json`
- `output/csv/pax-gold_market_chart_30d.csv`
- `output/csv/pax-gold_ohlc_30d.csv`
- `output/csv/pax-gold_weekend_only_30d.csv`
- `output/charts/pax-gold_market_chart_30d.png`
- `output/charts/pax-gold_ohlc_30d.html`
- `output/charts/pax-gold_weekend_gap_30d.png`

## Troubleshooting

### `COINGECKO_API_KEY is not set`

- Ensure `.env` exists
- Ensure key value is non-empty and starts with your `CG-...` token

### HTTP 401 / 403

- Verify Demo vs Pro mode:
  - Demo: `USE_PRO_API=false`
  - Pro: `USE_PRO_API=true`
- Ensure key type matches configured mode

### HTTP 429 / intermittent 5xx

- Increase retries, for example `--retries 4`
- Increase timeout, for example `--timeout 60`

### `null` market fields

`current_price`, `market_cap`, `total_volume`, `price_change_percentage_24h` can be `null` when data is unavailable. Treat `null` as missing data, not zero.

### Pro-only endpoint block

`08_ohlc_range_pro.py` requires paid API plans (Analyst+). Demo mode is intentionally blocked.

## Schema Source of Truth

See [docs/schema_lock.md](docs/schema_lock.md). This document is locked from NotebookLM queries over:

- Notebook title: `CoinGecko OpenAPI Specifications and Full Documentation`
- Notebook ID: `97b110fb-0b7a-4fbe-a3cb-ae96e83019c8`

## License

MIT
