#!/usr/bin/env python3
"""Free-licensed images from Wikimedia Commons for on-screen visuals.

  python3 scripts/images.py "Government Palace Ulaanbaatar" --name gov_palace
Saves remotion/public/images/<name>.jpg and appends credit to images/CREDITS.txt.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import REMOTION  # noqa: E402

UA = {"User-Agent": "hashka-vlog-edit/1.0 (video editing script)"}
API = "https://commons.wikimedia.org/w/api.php"
OK_LICENSES = ("cc0", "cc-by", "cc by", "public domain", "pd")


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read()


def search(query: str, n: int = 10) -> list[dict]:
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": f"{query} filetype:bitmap", "gsrlimit": n, "prop": "imageinfo",
        "iiprop": "url|extmetadata|size", "iiurlwidth": 1200})
    pages = json.loads(get(f"{API}?{q}")).get("query", {}).get("pages", {})
    out = []
    for p in sorted(pages.values(), key=lambda p: p.get("index", 0)):
        ii = p["imageinfo"][0]
        meta = ii.get("extmetadata", {})
        lic = meta.get("LicenseShortName", {}).get("value", "")
        artist = re.sub("<[^>]+>", "", meta.get("Artist", {}).get("value", "")).strip()
        out.append({"title": p["title"], "thumb": ii.get("thumburl"), "license": lic,
                    "artist": artist, "page": ii.get("descriptionurl"),
                    "w": ii.get("width"), "h": ii.get("height")})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--name", default="image")
    ap.add_argument("--pick", type=int, default=0, help="Which search result (0 = first usable)")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    res = [r for r in search(a.query) if r["thumb"] and any(k in r["license"].lower() for k in OK_LICENSES)]
    if a.list or not res:
        for i, r in enumerate(res):
            print(i, r["title"], "|", r["license"], "|", f"{r['w']}x{r['h']}")
        if not res:
            print("Чөлөөт лицензтэй зураг олдсонгүй.")
        return
    r = res[min(a.pick, len(res) - 1)]
    d = REMOTION / "public" / "images"
    d.mkdir(parents=True, exist_ok=True)
    ext = Path(urllib.parse.urlparse(r["thumb"]).path).suffix.lower() or ".jpg"
    out = d / f"{a.name}{ext}"
    out.write_bytes(get(r["thumb"]))
    with open(d / "CREDITS.txt", "a", encoding="utf-8") as f:
        f.write(f"{out.name}: {r['title']} — {r['artist']} — {r['license']} — {r['page']}\n")
    print(f"✔ images/{out.name}  ({r['license']}, {r['artist'][:40]})")


if __name__ == "__main__":
    main()
