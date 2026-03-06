import argparse
from pathlib import Path

import pandas as pd

from scripts._http import CoinGeckoHttpClient, add_common_arguments
from scripts._validate import finalize_validation, validate_markets


def parse_args():
    parser = argparse.ArgumentParser(description="List tokenized commodity market data by category.")
    add_common_arguments(parser)
    parser.add_argument("--category", default="tokenized-gold")
    parser.add_argument("--vs-currency", default="usd")
    parser.add_argument("--order", default="market_cap_desc")
    parser.add_argument("--per-page", type=int, default=20)
    parser.add_argument("--page", type=int, default=1)
    return parser.parse_args()


def main():
    args = parse_args()
    client = CoinGeckoHttpClient(
        debug=args.debug,
        save_raw=args.save_raw,
        out_dir=args.out_dir,
        timeout=args.timeout,
        retries=args.retries,
    )

    params = {
        "vs_currency": args.vs_currency,
        "category": args.category,
        "order": args.order,
        "per_page": args.per_page,
        "page": args.page,
    }

    data = client.request_json("/coins/markets", params=params, slug=f"coins_markets_{args.category}")
    errors = validate_markets(data)
    finalize_validation(errors, args.strict_schema, "GET /coins/markets")

    keep_cols = [
        "id",
        "name",
        "symbol",
        "current_price",
        "market_cap",
        "total_volume",
        "price_change_percentage_24h",
    ]
    df = pd.DataFrame(data)
    if df.empty:
        print("No rows returned for this category.")
        return

    df = df[keep_cols]
    print(df.to_string(index=False))

    csv_path = Path(args.out_dir) / "csv" / f"markets_{args.category}.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV: {csv_path}")


if __name__ == "__main__":
    main()
