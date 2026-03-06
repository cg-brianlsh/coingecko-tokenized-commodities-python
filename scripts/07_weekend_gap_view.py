import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from scripts._http import CoinGeckoHttpClient, add_common_arguments
from scripts._validate import finalize_validation, validate_market_chart


def parse_args():
    parser = argparse.ArgumentParser(description="Generate weekend price movement view from market chart data.")
    add_common_arguments(parser)
    parser.add_argument("--coin-id", default="pax-gold")
    parser.add_argument("--vs-currency", default="usd")
    parser.add_argument("--days", default="30")
    parser.add_argument(
        "--input-csv",
        default=None,
        help="Optional path to existing market chart CSV. If not provided, data is fetched live.",
    )
    return parser.parse_args()


def _load_or_fetch(args, client: CoinGeckoHttpClient) -> pd.DataFrame:
    if args.input_csv:
        df = pd.read_csv(args.input_csv)
        if "timestamp" not in df.columns or "price" not in df.columns:
            raise ValueError("Input CSV must contain timestamp and price columns.")
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df.sort_values("timestamp").reset_index(drop=True)

    params = {
        "vs_currency": args.vs_currency,
        "days": args.days,
    }
    data = client.request_json(f"/coins/{args.coin_id}/market_chart", params=params, slug=f"weekend_market_chart_{args.coin_id}")
    errors = validate_market_chart(data)
    finalize_validation(errors, args.strict_schema, f"GET /coins/{args.coin_id}/market_chart")

    prices_df = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
    prices_df["timestamp"] = pd.to_datetime(prices_df["timestamp"], unit="ms", utc=True)
    return prices_df.sort_values("timestamp").reset_index(drop=True)


def main():
    args = parse_args()
    client = CoinGeckoHttpClient(
        debug=args.debug,
        save_raw=args.save_raw,
        out_dir=args.out_dir,
        timeout=args.timeout,
        retries=args.retries,
    )

    df = _load_or_fetch(args, client)
    df = df.set_index("timestamp")

    weekend_mask = df.index.dayofweek >= 5
    weekend_df = df[weekend_mask].copy()

    if weekend_df.empty:
        raise RuntimeError("No weekend rows found in selected range. Increase --days and try again.")

    weekend_csv = Path(args.out_dir) / "csv" / f"{args.coin_id}_weekend_only_{args.days}d.csv"
    weekend_csv.parent.mkdir(parents=True, exist_ok=True)
    weekend_df.reset_index().to_csv(weekend_csv, index=False)

    chart_path = Path(args.out_dir) / "charts" / f"{args.coin_id}_weekend_gap_{args.days}d.png"
    chart_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 5))
    plt.plot(df.index, df["price"], label="All days", alpha=0.7)
    plt.scatter(weekend_df.index, weekend_df["price"], color="red", s=12, label="Weekend points")
    plt.title(f"{args.coin_id} weekend movement ({args.days} days)")
    plt.xlabel("Timestamp (UTC)")
    plt.ylabel(f"Price ({args.vs_currency.upper()})")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(chart_path)

    print(f"Total points: {len(df)}")
    print(f"Weekend points: {len(weekend_df)}")
    print(f"Weekend min/max: {weekend_df['price'].min()} / {weekend_df['price'].max()}")
    print(f"Saved weekend CSV: {weekend_csv}")
    print(f"Saved weekend chart: {chart_path}")


if __name__ == "__main__":
    main()
