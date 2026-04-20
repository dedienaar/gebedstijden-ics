import os
import time

import httpx
import pytest

from fetcher import PageFetcher


class FakeResponse:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        return None


class FakeClient:
    def __init__(self, content: bytes = b'data', raise_error: Exception | None = None):
        self._content = content
        self._raise_error = raise_error
        self.calls = 0

    def get(self, url: str):
        self.calls += 1

        if self._raise_error:
            raise self._raise_error

        return FakeResponse(self._content)


def test_fetch_returns_cached_file_when_valid(tmp_path):
    cache_file = tmp_path / 'page.html'
    cache_file.write_text('cached')

    client = FakeClient(content=b'new')

    fetcher = PageFetcher(client, 'https://example.com', cache_file, ttl_seconds=3600)

    result = fetcher.fetch()

    assert result == cache_file
    assert cache_file.read_text() == 'cached'
    assert client.calls == 0


def test_fetch_downloads_when_cache_missing(tmp_path):
    cache_file = tmp_path / 'page.html'

    client = FakeClient(content=b'fresh')

    fetcher = PageFetcher(client, 'https://example.com', cache_file)

    fetcher.fetch()

    assert cache_file.read_bytes() == b'fresh'
    assert client.calls == 1


def test_fetch_downloads_when_cache_expired(tmp_path):
    cache_file = tmp_path / 'page.html'
    cache_file.write_text('old')

    old_time = time.time() - 10_000
    os.utime(cache_file, (old_time, old_time))

    client = FakeClient(content=b'new')

    fetcher = PageFetcher(client, 'https://example.com', cache_file, ttl_seconds=1)

    fetcher.fetch()

    assert cache_file.read_bytes() == b'new'


def test_fetch_creates_parent_dirs(tmp_path):
    cache_file = tmp_path / 'nested' / 'dir' / 'page.html'

    client = FakeClient(content=b'data')

    fetcher = PageFetcher(client, 'https://example.com', cache_file)

    fetcher.fetch()

    assert cache_file.exists()


def test_fetch_raises_http_error(tmp_path):
    cache_file = tmp_path / 'page.html'

    client = FakeClient(
        raise_error=httpx.HTTPStatusError(
            'error',
            request=httpx.Request('GET', 'https://example.com'),
            response=httpx.Response(500),
        )
    )

    fetcher = PageFetcher(client, 'https://example.com', cache_file)

    with pytest.raises(httpx.HTTPStatusError):
        fetcher.fetch()

    assert not cache_file.exists()
