from __future__ import annotations

import time
from pathlib import Path

import httpx


class PageFetcher:
    def __init__(
        self,
        client: httpx.Client,
        url: str,
        cache_file: Path,
        ttl_seconds: int = 6 * 3600,
    ) -> None:
        self._client = client
        self._url = url
        self._cache_file = cache_file
        self._ttl = ttl_seconds

    def fetch(self) -> Path:
        if self._is_cache_valid():
            print(f'Cache hit: {self._cache_file}')
            return self._cache_file

        content = self._download_bytes()
        self._write_cache(content)
        return self._cache_file

    def _is_cache_valid(self) -> bool:
        if not self._cache_file.exists():
            return False

        mtime = self._cache_file.stat().st_mtime
        age = time.time() - mtime
        return age < self._ttl

    def _download_bytes(self) -> bytes:
        response = self._client.get(self._url)
        response.raise_for_status()
        return response.content

    def _write_cache(self, content: bytes) -> None:
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)

        file = self._cache_file.with_suffix('.tmp')
        file.write_bytes(content)
        file.replace(self._cache_file)

        print(f'Created cache file: {file}')
