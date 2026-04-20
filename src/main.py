from __future__ import annotations

from pathlib import Path

import httpx

from fetcher import PageFetcher

HISSA_URL = 'https://www.hissa.nl/his/maand'


def build_http_client() -> httpx.Client:
    return httpx.Client(timeout=10.0)


def build_cache_path() -> Path:
    return Path('.tmp') / 'hissa_month.html'


def main() -> None:
    cache_path = build_cache_path()

    fetcher = PageFetcher(
        client=build_http_client(),
        url=HISSA_URL,
        cache_path=cache_path,
        ttl_seconds=6 * 3600,  # 6 hours
    )

    html_file = fetcher.fetch()

    print(f'[OK] HTML available at: {html_file}')


if __name__ == '__main__':
    main()
