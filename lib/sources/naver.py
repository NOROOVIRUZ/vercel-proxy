"""네이버 쇼핑 검색 API 래퍼. 스펙 추출 포함."""
from __future__ import annotations
import os
import re
import requests

ENDPOINT = "https://openapi.naver.com/v1/search/shop.json"
_TAG_RE = re.compile(r"<[^>]+>")

# 스펙 추출용 패턴
_YEAR_RE = re.compile(r"(20\d{2})\s*년")
_SCREEN_RE = re.compile(r"(\d{1,2}(?:\.\d+)?)\s*인치")
_CPU_PATTERNS = [
    re.compile(r"\b(M[1-9][0-9]?(?:\s*(?:Pro|Max|Ultra))?)\b"),  # Apple M1~M9+
    re.compile(r"\b(i[3579](?:-\d{4,5}[A-Z]?)?)\b"),  # Intel Core
    re.compile(r"\b(Ryzen\s*[3579](?:\s*\d{3,4}[A-Z]{0,2})?)\b", re.IGNORECASE),  # AMD Ryzen
    re.compile(r"\b(A[1-9][0-9]?(?:\s*(?:Pro|Bionic|Max))?)\b"),  # Apple A-series
    re.compile(r"\b(Snapdragon\s*\d+(?:\+|Plus)?)\b", re.IGNORECASE),  # Qualcomm
    re.compile(r"\b(Exynos\s*\d+)\b", re.IGNORECASE),  # Samsung
]
_GB_TB_RE = re.compile(r"(\d+)\s*(GB|TB)", re.IGNORECASE)
_CPU_CORE_RE = re.compile(r"CPU\s*(\d+)\s*코어|(\d+)\s*코어\s*CPU", re.IGNORECASE)
_GPU_CORE_RE = re.compile(r"GPU\s*(\d+)\s*코어|(\d+)\s*코어\s*GPU", re.IGNORECASE)


def _clean(text: str) -> str:
    if not text:
        return ""
    return (_TAG_RE.sub("", text)
            .replace("&amp;", "&")
            .replace("&quot;", '"')
            .replace("&lt;", "<")
            .replace("&gt;", ">"))


def _extract_specs(title: str) -> dict:
    """제목 문자열에서 자주 나오는 스펙 패턴을 regex로 추출.
    안 나오는 항목은 결과에서 제외 (빈 값 안 넣음).
    """
    specs: dict = {}

    m = _YEAR_RE.search(title)
    if m:
        specs["year"] = m.group(1)

    m = _SCREEN_RE.search(title)
    if m:
        specs["screen"] = m.group(1) + "인치"

    for pat in _CPU_PATTERNS:
        m = pat.search(title)
        if m:
            specs["cpu"] = re.sub(r"\s+", " ", m.group(1)).strip()
            break

    m = _CPU_CORE_RE.search(title)
    if m:
        specs["cpu_cores"] = int(m.group(1) or m.group(2))

    m = _GPU_CORE_RE.search(title)
    if m:
        specs["gpu_cores"] = int(m.group(1) or m.group(2))

    # RAM / Storage 분리:
    #   4~64 GB → RAM
    #   128 GB 이상 or TB 단위 → Storage
    ram = None
    storage = None
    for num_s, unit in _GB_TB_RE.findall(title):
        num = int(num_s)
        is_tb = unit.upper() == "TB"
        total_gb = num * 1024 if is_tb else num
        if ram is None and not is_tb and 4 <= total_gb <= 64:
            ram = f"{num}GB"
        elif storage is None and total_gb >= 128:
            storage = f"{num}{unit.upper()}"
    if ram:
        specs["ram"] = ram
    if storage:
        specs["storage"] = storage

    return specs


def search(keyword: str, limit: int = 10) -> list[dict]:
    cid = os.environ.get("NAVER_CLIENT_ID", "").strip()
    csecret = os.environ.get("NAVER_CLIENT_SECRET", "").strip()
    if not cid or not csecret:
        raise RuntimeError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET not configured")

    r = requests.get(
        ENDPOINT,
        params={
            "query": keyword,
            "display": max(1, min(limit, 100)),
            "sort": "sim",
        },
        headers={
            "X-Naver-Client-Id": cid,
            "X-Naver-Client-Secret": csecret,
        },
        timeout=8,
    )
    r.raise_for_status()
    data = r.json()

    items: list[dict] = []
    for i, it in enumerate(data.get("items", []) or []):
        title = _clean(str(it.get("title", "")))[:300]

        # 카테고리 1~4 병합 (네이버가 분류 계층으로 제공)
        category_parts = [
            str(it.get(f"category{n}", "")).strip() for n in range(1, 5)
        ]
        category = " > ".join(p for p in category_parts if p)

        items.append({
            "rank": i + 1,
            "title": title,
            "price": str(it.get("lprice", "")),
            "price_high": str(it.get("hprice", "")),
            "currency": "원",
            "shop": str(it.get("mallName", ""))[:100],
            "url": str(it.get("link", "")),
            "image_url": str(it.get("image", "")),
            "brand": str(it.get("brand", "")),
            "maker": str(it.get("maker", "")),
            "category": category,
            "specs": _extract_specs(title),
            "source": "naver",
        })
    return items
