import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from scripts._http import CoinGeckoHttpClient, add_common_arguments
from scripts._validate import finalize_validation, validate_market_chart


def parse_args():
    parser = argparse.ArgumentParser(description="Build market chart CSV and line chart for tokenized commodities.")
    add_common_arguments(parser)
    parser.add_argument("--coin-id", default="pax-gold")
    parser.add_argument("--vs-currency", default="usd")
    parser.add_argument("--days", default="30")
    return parser.parse_args()


def _build_dataframe(data: dict) -> pd.DataFrame:
    prices_df = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
    market_caps_df = pd.DataFrame(data["market_caps"], columns=["timestamp", "market_cap"])
    volumes_df = pd.DataFrame(data["total_volumes"], columns=["timestamp", "total_volume"])

    df = prices_df.merge(market_caps_df, on="timestamp", how="outer").merge(volumes_df, on="timestamp", how="outer")
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df.sort_values("timestamp").reset_index(drop=True)


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
        "days": args.days,
    }

    data = client.request_json(f"/coins/{args.coin_id}/market_chart", params=params, slug=f"market_chart_{args.coin_id}")
    errors = validate_market_chart(data)
    finalize_validation(errors, args.strict_schema, f"GET /coins/{args.coin_id}/market_chart")

    df = _build_dataframe(data)

    csv_path = Path(args.out_dir) / "csv" / f"{args.coin_id}_market_chart_{args.days}d.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)

    chart_path = Path(args.out_dir) / "charts" / f"{args.coin_id}_market_chart_{args.days}d.png"
    chart_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(12, 5))
    plt.plot(df["timestamp"], df["price"], label=f"{args.coin_id} price")
    plt.title(f"{args.coin_id} market chart ({args.days} days)")
    plt.xlabel("Timestamp (UTC)")
    plt.ylabel(f"Price ({args.vs_currency.upper()})")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(chart_path)

    print(f"Rows: {len(df)}")
    print(f"Saved CSV: {csv_path}")
    print(f"Saved chart: {chart_path}")


if __name__ == "__main__":
    main()
