from __future__ import annotations

import time
from pathlib import Path

import httpx


class PageFetcher:
    def __init__(
        self,
        client: httpx.Client,
        url: str,
        cache_path: Path,
        ttl_seconds: int = 6 * 3600,
    ) -> None:
        self._client = client
        self._url = url
        self._cache_path = cache_path
        self._ttl = ttl_seconds

    def fetch(self) -> Path:
        if self._is_cache_valid():
            return self._cache_path

        content = self._download()
        self._write_cache(content)
        return self._cache_path

    def _is_cache_valid(self) -> bool:
        if not self._cache_path.exists():
            return False

        mtime = self._cache_path.stat().st_mtime
        age = time.time() - mtime
        return age < self._ttl

    def _download(self) -> bytes:
        response = self._client.get(self._url)
        response.raise_for_status()
        return response.content

    def _write_cache(self, content: bytes) -> None:
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = self._cache_path.with_suffix('.tmp')
        tmp_path.write_bytes(content)
        tmp_path.replace(self._cache_path)
