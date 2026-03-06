import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from scripts._http import CoinGeckoHttpClient, add_common_arguments
from scripts._validate import finalize_validation, validate_ohlc


def parse_args():
    parser = argparse.ArgumentParser(description="Build OHLC CSV and candlestick chart for tokenized commodities.")
    add_common_arguments(parser)
    parser.add_argument("--coin-id", default="pax-gold")
    parser.add_argument("--vs-currency", default="usd")
    parser.add_argument("--days", default="30")
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
        "days": args.days,
    }

    data = client.request_json(f"/coins/{args.coin_id}/ohlc", params=params, slug=f"ohlc_{args.coin_id}")
    errors = validate_ohlc(data)
    finalize_validation(errors, args.strict_schema, f"GET /coins/{args.coin_id}/ohlc")

    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

    csv_path = Path(args.out_dir) / "csv" / f"{args.coin_id}_ohlc_{args.days}d.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)

    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df["timestamp"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name=args.coin_id,
            )
        ]
    )
    fig.update_layout(
        title=f"{args.coin_id} OHLC ({args.days} days)",
        xaxis_title="Timestamp (UTC)",
        yaxis_title=f"Price ({args.vs_currency.upper()})",
        template="plotly_white",
    )

    chart_path = Path(args.out_dir) / "charts" / f"{args.coin_id}_ohlc_{args.days}d.html"
    chart_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(chart_path)

    print(f"Rows: {len(df)}")
    print(f"Saved CSV: {csv_path}")
    print(f"Saved candlestick chart: {chart_path}")


if __name__ == "__main__":
    main()
