import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go

from scripts._http import CoinGeckoHttpClient, add_common_arguments
from scripts._validate import (
    finalize_validation,
    validate_categories_list,
    validate_coin_detail,
    validate_market_chart,
    validate_markets,
    validate_ohlc,
    validate_simple_price,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Run end-to-end smoke checks for scripts 01-07.")
    add_common_arguments(parser)
    parser.add_argument("--coin-id", default="pax-gold")
    parser.add_argument("--days", default="30")
    parser.add_argument("--fail-fast", action="store_true")
    return parser.parse_args()


def run_test(name, fn, report, fail_fast):
    started = datetime.utcnow().isoformat() + "Z"
    try:
        details = fn()
        report["tests"].append({"name": name, "status": "passed", "started_at": started, "details": details})
        print(f"PASS: {name}")
        return True
    except Exception as exc:
        report["tests"].append({"name": name, "status": "failed", "started_at": started, "error": str(exc)})
        print(f"FAIL: {name} -> {exc}")
        if fail_fast:
            raise
        return False


def main():
    args = parse_args()
    client = CoinGeckoHttpClient(
        debug=args.debug,
        save_raw=args.save_raw,
        out_dir=args.out_dir,
        timeout=args.timeout,
        retries=args.retries,
    )

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "coin_id": args.coin_id,
        "days": args.days,
        "strict_schema": args.strict_schema,
        "tests": [],
    }

    cached_market_df = None

    def t1_categories():
        data = client.request_json("/coins/categories/list", slug="smoke_categories")
        finalize_validation(validate_categories_list(data), args.strict_schema, "smoke categories")
        return {"rows": len(data)}

    def t2_markets():
        params = {
            "vs_currency": "usd",
            "category": "tokenized-gold",
            "order": "market_cap_desc",
            "per_page": 20,
            "page": 1,
        }
        data = client.request_json("/coins/markets", params=params, slug="smoke_markets")
        finalize_validation(validate_markets(data), args.strict_schema, "smoke markets")
        return {"rows": len(data)}

    def t3_simple_price():
        params = {
            "ids": "pax-gold,tether-gold",
            "vs_currencies": "usd",
            "include_market_cap": "true",
            "include_24hr_change": "true",
        }
        data = client.request_json("/simple/price", params=params, slug="smoke_simple_price")
        finalize_validation(
            validate_simple_price(data, ids=["pax-gold", "tether-gold"], vs_currency="usd"),
            args.strict_schema,
            "smoke simple price",
        )
        return {"ids": list(data.keys())}

    def t4_coin_detail():
        data = client.request_json(f"/coins/{args.coin_id}", slug="smoke_coin_detail")
        finalize_validation(validate_coin_detail(data, vs_currency="usd"), args.strict_schema, "smoke coin detail")
        return {
            "id": data.get("id"),
            "price_usd": data.get("market_data", {}).get("current_price", {}).get("usd"),
        }

    def t5_market_chart():
        nonlocal cached_market_df
        params = {"vs_currency": "usd", "days": args.days}
        data = client.request_json(f"/coins/{args.coin_id}/market_chart", params=params, slug="smoke_market_chart")
        finalize_validation(validate_market_chart(data), args.strict_schema, "smoke market chart")

        prices_df = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
        market_caps_df = pd.DataFrame(data["market_caps"], columns=["timestamp", "market_cap"])
        volumes_df = pd.DataFrame(data["total_volumes"], columns=["timestamp", "total_volume"])
        df = prices_df.merge(market_caps_df, on="timestamp", how="outer").merge(volumes_df, on="timestamp", how="outer")
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df = df.sort_values("timestamp").reset_index(drop=True)
        cached_market_df = df

        csv_path = Path(args.out_dir) / "csv" / f"{args.coin_id}_market_chart_{args.days}d.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)

        chart_path = Path(args.out_dir) / "charts" / f"{args.coin_id}_market_chart_{args.days}d.png"
        chart_path.parent.mkdir(parents=True, exist_ok=True)
        plt.figure(figsize=(12, 5))
        plt.plot(df["timestamp"], df["price"], label=f"{args.coin_id} price")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(chart_path)

        return {"rows": len(df), "csv": str(csv_path), "chart": str(chart_path)}

    def t6_ohlc():
        params = {"vs_currency": "usd", "days": args.days}
        data = client.request_json(f"/coins/{args.coin_id}/ohlc", params=params, slug="smoke_ohlc")
        finalize_validation(validate_ohlc(data), args.strict_schema, "smoke ohlc")

        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

        csv_path = Path(args.out_dir) / "csv" / f"{args.coin_id}_ohlc_{args.days}d.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)

        html_path = Path(args.out_dir) / "charts" / f"{args.coin_id}_ohlc_{args.days}d.html"
        html_path.parent.mkdir(parents=True, exist_ok=True)
        fig = go.Figure(
            data=[go.Candlestick(x=df["timestamp"], open=df["open"], high=df["high"], low=df["low"], close=df["close"])]
        )
        fig.write_html(html_path)

        return {"rows": len(df), "csv": str(csv_path), "chart": str(html_path)}

    def t7_weekend_gap():
        nonlocal cached_market_df
        if cached_market_df is None:
            raise RuntimeError("Market chart test must run before weekend gap test.")

        df = cached_market_df.copy().set_index("timestamp")
        weekend = df[df.index.dayofweek >= 5]
        if weekend.empty:
            raise RuntimeError("No weekend data points were found.")

        weekend_csv = Path(args.out_dir) / "csv" / f"{args.coin_id}_weekend_only_{args.days}d.csv"
        weekend_csv.parent.mkdir(parents=True, exist_ok=True)
        weekend.reset_index().to_csv(weekend_csv, index=False)

        weekend_chart = Path(args.out_dir) / "charts" / f"{args.coin_id}_weekend_gap_{args.days}d.png"
        weekend_chart.parent.mkdir(parents=True, exist_ok=True)
        plt.figure(figsize=(12, 5))
        plt.plot(df.index, df["price"], alpha=0.7)
        plt.scatter(weekend.index, weekend["price"], color="red", s=10)
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(weekend_chart)

        return {
            "weekend_points": int(len(weekend)),
            "weekend_min": float(weekend["price"].min()),
            "weekend_max": float(weekend["price"].max()),
            "csv": str(weekend_csv),
            "chart": str(weekend_chart),
        }

    all_ok = True
    tests = [
        ("01_discover_categories", t1_categories),
        ("02_list_markets", t2_markets),
        ("03_simple_price", t3_simple_price),
        ("04_coin_detail", t4_coin_detail),
        ("05_market_chart", t5_market_chart),
        ("06_ohlc_chart", t6_ohlc),
        ("07_weekend_gap_view", t7_weekend_gap),
    ]

    try:
        for name, fn in tests:
            ok = run_test(name, fn, report, args.fail_fast)
            all_ok = all_ok and ok
    except Exception:
        all_ok = False

    out_path = Path(args.out_dir) / "json" / "smoke_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved smoke report: {out_path}")

    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
