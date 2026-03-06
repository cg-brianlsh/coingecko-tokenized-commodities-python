import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import requests

from config import BASE_URL, MAX_RETRIES, REQUEST_TIMEOUT, get_headers


class CoinGeckoHttpClient:
    def __init__(
        self,
        *,
        debug: bool = False,
        save_raw: bool = False,
        out_dir: str = "output",
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
    ) -> None:
        self.debug = debug
        self.save_raw = save_raw
        self.timeout = REQUEST_TIMEOUT if timeout is None else timeout
        self.retries = MAX_RETRIES if retries is None else retries
        self.base_url = BASE_URL.rstrip("/")
        self.session = requests.Session()
        self.headers = get_headers()

        self.out_dir = Path(out_dir)
        self.json_dir = self.out_dir / "json"
        self.csv_dir = self.out_dir / "csv"
        self.charts_dir = self.out_dir / "charts"
        for d in (self.json_dir, self.csv_dir, self.charts_dir):
            d.mkdir(parents=True, exist_ok=True)

    def _log(self, msg: str) -> None:
        if self.debug:
            ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts} UTC] {msg}")

    def _snapshot(self, slug: str, payload: dict) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = self.json_dir / f"raw_{slug}_{timestamp}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def request_json(
        self,
        path: str,
        *,
        params: Optional[dict] = None,
        expected_status: int = 200,
        slug: Optional[str] = None,
    ) -> Any:
        endpoint = f"{self.base_url}/{path.lstrip('/')}"
        slug = slug or path.strip("/").replace("/", "_").replace("{", "").replace("}", "")

        last_error = None
        for attempt in range(self.retries + 1):
            try:
                start = time.perf_counter()
                response = self.session.get(endpoint, headers=self.headers, params=params, timeout=self.timeout)
                elapsed_ms = (time.perf_counter() - start) * 1000

                self._log(
                    f"GET {response.url} -> status={response.status_code}, elapsed_ms={elapsed_ms:.2f}, bytes={len(response.content)}"
                )

                preview = response.text[:600]
                self._log(f"Response preview (first 600 chars): {preview}")

                if self.save_raw:
                    snapshot_payload = {
                        "request": {
                            "url": endpoint,
                            "params": params or {},
                            "timeout": self.timeout,
                            "attempt": attempt + 1,
                        },
                        "response": {
                            "status_code": response.status_code,
                            "headers": dict(response.headers),
                            "text_preview": preview,
                        },
                    }
                    path_written = self._snapshot(slug, snapshot_payload)
                    self._log(f"Saved raw snapshot: {path_written}")

                if response.status_code == expected_status:
                    try:
                        return response.json()
                    except ValueError as exc:
                        raise RuntimeError(f"Expected JSON response but parsing failed: {exc}") from exc

                retriable = response.status_code in {429, 500, 502, 503, 504}
                message = (
                    f"Unexpected HTTP status for {path}: {response.status_code}. "
                    f"Expected {expected_status}. Body preview: {preview}"
                )
                if retriable and attempt < self.retries:
                    sleep_s = 2 ** attempt
                    self._log(f"Retryable status encountered. sleeping {sleep_s}s before retry...")
                    time.sleep(sleep_s)
                    continue

                raise RuntimeError(message)

            except requests.RequestException as exc:
                last_error = exc
                self._log(f"Network/request error on attempt {attempt + 1}: {exc}")
                if attempt < self.retries:
                    sleep_s = 2 ** attempt
                    self._log(f"Retrying after {sleep_s}s...")
                    time.sleep(sleep_s)
                    continue
                break

        raise RuntimeError(f"Request failed after {self.retries + 1} attempts for {path}: {last_error}")


def add_common_arguments(parser):
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logs.")
    parser.add_argument("--strict-schema", action="store_true", help="Fail on schema validation errors.")
    parser.add_argument("--save-raw", action="store_true", help="Persist raw request/response snapshots to output/json.")
    parser.add_argument("--timeout", type=float, default=None, help="Request timeout in seconds.")
    parser.add_argument("--retries", type=int, default=None, help="Retry attempts for request failures/retryable statuses.")
    parser.add_argument("--out-dir", default="output", help="Base output directory for artifacts.")
    return parser
