import argparse
from pathlib import Path
import sys

import pandas as pd

from config import USE_PRO_API
from scripts._http import CoinGeckoHttpClient, add_common_arguments
from scripts._validate import finalize_validation, validate_ohlc_range


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch OHLC range data (paid plans only).")
    add_common_arguments(parser)
    parser.add_argument("--coin-id", default="pax-gold")
    parser.add_argument("--vs-currency", default="usd")
    parser.add_argument("--from", dest="from_ts", required=True, help="From timestamp/date (unix or ISO date).")
    parser.add_argument("--to", dest="to_ts", required=True, help="To timestamp/date (unix or ISO date).")
    parser.add_argument("--interval", choices=["daily", "hourly"], default="daily")
    return parser.parse_args()


def main():
    args = parse_args()

    if not USE_PRO_API:
        print("This script requires a paid CoinGecko API plan (Analyst+).")
        print("Set USE_PRO_API=true in .env and use a paid-plan API key to continue.")
        sys.exit(1)

    client = CoinGeckoHttpClient(
        debug=args.debug,
        save_raw=args.save_raw,
        out_dir=args.out_dir,
        timeout=args.timeout,
        retries=args.retries,
    )

    params = {
        "vs_currency": args.vs_currency,
        "from": args.from_ts,
        "to": args.to_ts,
        "interval": args.interval,
    }

    data = client.request_json(f"/coins/{args.coin_id}/ohlc/range", params=params, slug=f"ohlc_range_{args.coin_id}")
    errors = validate_ohlc_range(data)
    finalize_validation(errors, args.strict_schema, f"GET /coins/{args.coin_id}/ohlc/range")

    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

    csv_path = Path(args.out_dir) / "csv" / f"{args.coin_id}_ohlc_range_{args.interval}.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)

    print(f"Rows: {len(df)}")
    print(f"Saved CSV: {csv_path}")


if __name__ == "__main__":
    main()
