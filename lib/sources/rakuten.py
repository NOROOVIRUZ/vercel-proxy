"""라쿠텐 Ichiba Item Search API 래퍼."""
from __future__ import annotations
import os
import requests

ENDPOINT = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"


def search(keyword: str, limit: int = 10) -> list[dict]:
    app_id = os.environ.get("RAKUTEN_APP_ID", "").strip()
    if not app_id:
        raise RuntimeError("RAKUTEN_APP_ID not configured")

    r = requests.get(
        ENDPOINT,
        params={
            "format": "json",
            "applicationId": app_id,
            "keyword": keyword,
            "hits": max(1, min(limit, 30)),
            "formatVersion": 2,
        },
        timeout=8,
    )
    r.raise_for_status()
    data = r.json()

    items: list[dict] = []
    for i, it in enumerate(data.get("Items", []) or []):
        imgs = it.get("mediumImageUrls") or []
        image = imgs[0] if imgs and isinstance(imgs[0], str) else (imgs[0].get("imageUrl", "") if imgs else "")
        items.append({
            "rank": i + 1,
            "title": str(it.get("itemName", ""))[:300],
            "price": str(it.get("itemPrice", "")),
            "currency": "엔",
            "shop": str(it.get("shopName", ""))[:100],
            "url": str(it.get("itemUrl", "")),
            "image_url": image,
            "source": "rakuten",
        })
    return items
