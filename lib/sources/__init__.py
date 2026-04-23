"""검색 소스 레지스트리. 새 소스 추가 시 여기에만 등록."""
from __future__ import annotations
from typing import Callable

from . import rakuten, naver, ebay

SearchFn = Callable[[str, int], list[dict]]

REGISTRY: dict[str, SearchFn] = {
    "rakuten": rakuten.search,
    "naver": naver.search,
    "ebay": ebay.search,
}


def available() -> list[str]:
    return list(REGISTRY.keys())


def get(source: str) -> SearchFn | None:
    return REGISTRY.get(source)
