import argparse

from scripts._http import CoinGeckoHttpClient, add_common_arguments
from scripts._validate import finalize_validation, validate_categories_list


def parse_args():
    parser = argparse.ArgumentParser(description="Discover CoinGecko category IDs (tokenized commodities focused).")
    add_common_arguments(parser)
    parser.add_argument("--contains", default="tokenized", help="Substring filter for category_id or name.")
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

    data = client.request_json("/coins/categories/list", slug="coins_categories_list")
    errors = validate_categories_list(data)
    finalize_validation(errors, args.strict_schema, "GET /coins/categories/list")

    needle = args.contains.lower()
    filtered = [
        x for x in data
        if needle in x.get("category_id", "").lower() or needle in x.get("name", "").lower()
    ]

    print(f"Total categories returned: {len(data)}")
    print(f"Filtered categories containing '{args.contains}': {len(filtered)}")
    for item in filtered:
        print(f"- {item['category_id']}: {item['name']}")


if __name__ == "__main__":
    main()
