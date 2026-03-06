# Schema Lock (NotebookLM-Sourced)

Updated: 2026-03-06

Source notebook:
- Title: `CoinGecko OpenAPI Specifications and Full Documentation`
- Notebook ID: `97b110fb-0b7a-4fbe-a3cb-ae96e83019c8`

Purpose:
- Lock expected response shapes and endpoint caveats for script validation.
- Keep expected outputs schema-based, not value-based.

## 1) `GET /coins/categories/list`

Shape:
- Top-level: `array<object>`
- Required item keys:
  - `category_id` (string)
  - `name` (string)

Plan gating:
- Not gated by paid plan.

## 2) `GET /coins/markets`

Typical params used:
- `vs_currency=usd`
- `category=tokenized-gold`
- `order=market_cap_desc`
- `per_page=20` (or up to documented max)
- `page=1`

Shape:
- Top-level: `array<object>`
- Required/common keys used in this repo:
  - `id` (string)
  - `name` (string)
  - `symbol` (string)
  - `current_price` (number or null)
  - `market_cap` (number or null)
  - `total_volume` (number or null)
  - `price_change_percentage_24h` (number or null)

Caveat:
- Market numeric fields may be `null`; treat as missing, not zero.

## 3) `GET /simple/price`

Typical params used:
- `ids=pax-gold,tether-gold`
- `vs_currencies=usd`
- `include_market_cap=true`
- `include_24hr_change=true`

Shape:
- Top-level: object keyed by requested IDs.
- For each ID key:
  - `usd` (number)
  - `usd_market_cap` (number) when include flag enabled
  - `usd_24h_change` (number) when include flag enabled

Key naming convention:
- Currency-driven dynamic keys for market cap and 24h change.

## 4) `GET /coins/{id}`

Paths locked for validation:
- `market_data.current_price.usd` (number)
- `market_data.ath.usd` (number)
- `market_data.total_volume.usd` (number)
- `asset_platform_id` (string or null)
- `platforms` (object)
- `detail_platforms` (object)

## 5) `GET /coins/{id}/market_chart`

Typical params used:
- `vs_currency=usd`
- `days=30`

Shape:
- Top-level object keys:
  - `prices`: `array<[timestamp_ms, value]>`
  - `market_caps`: `array<[timestamp_ms, value]>`
  - `total_volumes`: `array<[timestamp_ms, value]>`

Plan and granularity notes:
- Demo historical range is limited (commonly 365 days max).
- Auto-granularity applies by range; paid plans unlock more control.

## 6) `GET /coins/{id}/ohlc`

Typical params used:
- `vs_currency=usd`
- `days=30`

Shape:
- Top-level: `array<[timestamp, open, high, low, close]>`

Tuple order:
1. `timestamp`
2. `open`
3. `high`
4. `low`
5. `close`

Notes:
- `days` is constrained to documented enum values.
- Candle granularity follows documented auto rules unless paid interval control is available.

## 7) `GET /coins/{id}/ohlc/range` (Paid)

Required params used in repo:
- `vs_currency`
- `from`
- `to`
- `interval` (`daily` or `hourly`)

Shape:
- Top-level: `array<[timestamp, open, high, low, close]>`

Plan gating:
- Paid-plan endpoint (Analyst+). Script hard-blocks in Demo mode.

Timestamp expectations:
- Request accepts unix or ISO-like time formats.
- Response tuples use unix epoch milliseconds.

## Canonical Query Examples Used in Scripts

- Categories list: no params
- Markets by category: `vs_currency=usd&category=tokenized-gold`
- Simple price: `ids=pax-gold,tether-gold&vs_currencies=usd`
- Market chart 30d: `vs_currency=usd&days=30`
- OHLC 30d: `vs_currency=usd&days=30`
