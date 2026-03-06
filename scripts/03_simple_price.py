import argparse
import json
from pathlib import Path

import pandas as pd

from scripts._http import CoinGeckoHttpClient, add_common_arguments
from scripts._validate import finalize_validation, validate_simple_price


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch real-time simple prices for tokenized commodities.")
    add_common_arguments(parser)
    parser.add_argument("--ids", default="pax-gold,tether-gold")
    parser.add_argument("--vs-currency", default="usd")
    parser.add_argument("--include-market-cap", action="store_true", default=True)
    parser.add_argument("--include-24h-change", action="store_true", default=True)
    return parser.parse_args()


def main():
    args = parse_args()
    ids = [x.strip() for x in args.ids.split(",") if x.strip()]

    client = CoinGeckoHttpClient(
        debug=args.debug,
        save_raw=args.save_raw,
        out_dir=args.out_dir,
        timeout=args.timeout,
        retries=args.retries,
    )

    params = {
        "ids": ",".join(ids),
        "vs_currencies": args.vs_currency,
        "include_market_cap": "true" if args.include_market_cap else "false",
        "include_24hr_change": "true" if args.include_24h_change else "false",
    }

    data = client.request_json("/simple/price", params=params, slug="simple_price")
    errors = validate_simple_price(
        data,
        ids=ids,
        vs_currency=args.vs_currency,
        include_market_cap=args.include_market_cap,
        include_24h_change=args.include_24h_change,
    )
    finalize_validation(errors, args.strict_schema, "GET /simple/price")

    print(json.dumps(data, indent=2))

    rows = []
    for coin_id in ids:
        coin = data.get(coin_id, {})
        rows.append(
            {
                "id": coin_id,
                args.vs_currency: coin.get(args.vs_currency),
                f"{args.vs_currency}_market_cap": coin.get(f"{args.vs_currency}_market_cap"),
                f"{args.vs_currency}_24h_change": coin.get(f"{args.vs_currency}_24h_change"),
            }
        )

    df = pd.DataFrame(rows)
    csv_path = Path(args.out_dir) / "csv" / "simple_price.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV: {csv_path}")


if __name__ == "__main__":
    main()
