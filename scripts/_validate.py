from typing import Any, Iterable, List


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _get_path(obj: Any, path: str):
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def finalize_validation(errors: List[str], strict: bool, context: str) -> None:
    if not errors:
        return
    msg = f"{context} schema validation issues:\n- " + "\n- ".join(errors)
    if strict:
        raise ValueError(msg)
    print(f"WARNING: {msg}")


def validate_categories_list(data: Any) -> List[str]:
    errors = []
    if not isinstance(data, list):
        return ["Top-level response must be a list."]

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"Item {i} must be an object.")
            continue
        for key in ("category_id", "name"):
            if key not in item:
                errors.append(f"Item {i} missing key: {key}")
            elif not isinstance(item[key], str):
                errors.append(f"Item {i} key {key} must be string.")
    return errors


def validate_markets(data: Any) -> List[str]:
    errors = []
    if not isinstance(data, list):
        return ["Top-level response must be a list."]

    required = [
        "id",
        "name",
        "symbol",
        "current_price",
        "market_cap",
        "total_volume",
        "price_change_percentage_24h",
    ]

    nullable_numeric = {
        "current_price",
        "market_cap",
        "total_volume",
        "price_change_percentage_24h",
    }

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"Item {i} must be an object.")
            continue

        for key in required:
            if key not in item:
                errors.append(f"Item {i} missing key: {key}")
                continue

            value = item[key]
            if key in nullable_numeric:
                if value is not None and not _is_number(value):
                    errors.append(f"Item {i} key {key} must be number or null.")
            else:
                if not isinstance(value, str):
                    errors.append(f"Item {i} key {key} must be string.")

    return errors


def validate_simple_price(
    data: Any,
    *,
    ids: Iterable[str],
    vs_currency: str = "usd",
    include_market_cap: bool = True,
    include_24h_change: bool = True,
) -> List[str]:
    errors = []
    if not isinstance(data, dict):
        return ["Top-level response must be an object."]

    for coin_id in ids:
        if coin_id not in data:
            errors.append(f"Missing top-level key for id: {coin_id}")
            continue

        coin_data = data[coin_id]
        if not isinstance(coin_data, dict):
            errors.append(f"Value for {coin_id} must be object.")
            continue

        if vs_currency not in coin_data or not _is_number(coin_data.get(vs_currency)):
            errors.append(f"{coin_id} missing numeric key: {vs_currency}")

        if include_market_cap:
            k = f"{vs_currency}_market_cap"
            if k not in coin_data or not _is_number(coin_data.get(k)):
                errors.append(f"{coin_id} missing numeric key: {k}")

        if include_24h_change:
            k = f"{vs_currency}_24h_change"
            if k not in coin_data or not _is_number(coin_data.get(k)):
                errors.append(f"{coin_id} missing numeric key: {k}")

    return errors


def validate_coin_detail(data: Any, *, vs_currency: str = "usd") -> List[str]:
    errors = []
    if not isinstance(data, dict):
        return ["Top-level response must be an object."]

    required_paths = [
        f"market_data.current_price.{vs_currency}",
        f"market_data.ath.{vs_currency}",
        f"market_data.total_volume.{vs_currency}",
        "asset_platform_id",
        "platforms",
        "detail_platforms",
    ]

    for p in required_paths:
        value = _get_path(data, p)
        if value is None:
            errors.append(f"Missing path: {p}")
            continue

        if p.endswith(vs_currency) and not _is_number(value):
            errors.append(f"Path {p} must be numeric.")

    if isinstance(_get_path(data, "platforms"), dict) is False:
        errors.append("Path platforms must be object.")

    if isinstance(_get_path(data, "detail_platforms"), dict) is False:
        errors.append("Path detail_platforms must be object.")

    return errors


def validate_market_chart(data: Any) -> List[str]:
    errors = []
    if not isinstance(data, dict):
        return ["Top-level response must be an object."]

    for key in ("prices", "market_caps", "total_volumes"):
        arr = data.get(key)
        if not isinstance(arr, list):
            errors.append(f"Missing/invalid key: {key} (must be list)")
            continue

        for i, row in enumerate(arr):
            if not isinstance(row, list) or len(row) != 2:
                errors.append(f"{key}[{i}] must be a 2-item tuple [timestamp_ms, value].")
                continue
            if not _is_number(row[0]) or not _is_number(row[1]):
                errors.append(f"{key}[{i}] values must be numeric.")
    return errors


def validate_ohlc(data: Any) -> List[str]:
    errors = []
    if not isinstance(data, list):
        return ["Top-level response must be a list."]

    for i, row in enumerate(data):
        if not isinstance(row, list) or len(row) != 5:
            errors.append(f"Row {i} must be [timestamp, open, high, low, close].")
            continue
        if not all(_is_number(v) for v in row):
            errors.append(f"Row {i} OHLC tuple values must be numeric.")
    return errors


def validate_ohlc_range(data: Any) -> List[str]:
    return validate_ohlc(data)
