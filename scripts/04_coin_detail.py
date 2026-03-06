import argparse
import json
from pathlib import Path

from scripts._http import CoinGeckoHttpClient, add_common_arguments
from scripts._validate import finalize_validation, validate_coin_detail


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch detailed coin metadata for tokenized commodities.")
    add_common_arguments(parser)
    parser.add_argument("--coin-id", default="pax-gold")
    parser.add_argument("--vs-currency", default="usd")
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

    data = client.request_json(f"/coins/{args.coin_id}", slug=f"coin_detail_{args.coin_id}")
    errors = validate_coin_detail(data, vs_currency=args.vs_currency)
    finalize_validation(errors, args.strict_schema, f"GET /coins/{args.coin_id}")

    summary = {
        "id": data.get("id"),
        "symbol": data.get("symbol"),
        "name": data.get("name"),
        "asset_platform_id": data.get("asset_platform_id"),
        "price_usd": data.get("market_data", {}).get("current_price", {}).get(args.vs_currency),
        "ath_usd": data.get("market_data", {}).get("ath", {}).get(args.vs_currency),
        "total_volume_usd": data.get("market_data", {}).get("total_volume", {}).get(args.vs_currency),
        "platforms": data.get("platforms", {}),
        "detail_platforms": data.get("detail_platforms", {}),
    }

    print(json.dumps(summary, indent=2))

    out_path = Path(args.out_dir) / "json" / f"{args.coin_id}_detail_summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Saved summary: {out_path}")


if __name__ == "__main__":
    main()
