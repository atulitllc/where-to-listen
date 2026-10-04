#!/usr/bin/env python3
"""Read publisher RSS for language, publisher, and a channel summary.

Does not download audio or keep enclosure URLs. Channel fields only.
"""

import html
import json
import re
import ssl
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = "WhereToListenCatalog/1.0 (metadata only; no media)"
CTX = ssl.create_default_context()

ACAST = re.compile(
    r"hosted on acast\.?\s*(see\s*)?acast\.com/privacy for more information\.?",
    re.I,
)
SUPPORT = re.compile(r"become a supporter of this podcast\s*:?", re.I)


def strip_markup(value):
    text = value or ""
    text = re.sub(r"<!\[CDATA\[", " ", text, flags=re.I)
    text = text.replace("]]>", " ")
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"https?://\S+", " ", text)
    text = ACAST.sub(" ", text)
    text = re.sub(r"acast\.com/privacy for more information\.?", " ", text, flags=re.I)
    text = SUPPORT.sub(" ", text)
    text = re.sub(r"\bfree\s+downloads?\b", " ", text, flags=re.I)
    text = re.sub(r"\bdownloads?\b", " ", text, flags=re.I)
    text = re.sub(r"\btorrents?\b", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip(" \t\r\n-–—|,;:.")
    return text.strip()


def tag_body(block, name):
    matches = re.findall(rf"<{name}(?:\s[^>]*)?>(.*?)</{name}>", block, re.I | re.S)
    return matches[0] if matches else ""


def best_summary(head):
    chunks = []
    for name in ("itunes:summary", "description", "itunes:subtitle"):
        raw = tag_body(head, name)
        cleaned = strip_markup(raw)
        if len(cleaned) >= 40:
            chunks.append(cleaned)
    if not chunks:
        return ""
    chunks.sort(key=len, reverse=True)
    text = chunks[0]
    if len(text) > 700:
        cut = text[:700]
        for sep in (". ", "? ", "! "):
            i = cut.rfind(sep)
            if i > 180:
                return cut[: i + 1].strip()
        text = cut.rsplit(" ", 1)[0].strip()
    return text


def parse_channel(raw):
    text = raw.decode("utf-8", "replace")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    head = re.split(r"<item\b", text, maxsplit=1, flags=re.I)[0]
    author = strip_markup(tag_body(head, "itunes:author")) or strip_markup(tag_body(head, "author"))
    language = strip_markup(tag_body(head, "language")) or strip_markup(tag_body(head, "dc:language"))
    language = language.lower().replace("_", "-")[:16]
    links = re.findall(r"<link>([^<]+)</link>", head, re.I)
    link = html.unescape(links[0]).strip() if links else ""
    return {
        "publisher": author[:140],
        "language": language,
        "summary": best_summary(head),
        "link": link[:240],
    }


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, */*"})
    with urllib.request.urlopen(req, timeout=18, context=CTX) as response:
        return response.read(120000)


def one(row):
    try:
        info = parse_channel(get(row["feed"]))
        info["ok"] = True
    except Exception as exc:
        info = {"publisher": "", "language": "", "summary": "", "link": "", "ok": False, "error": type(exc).__name__}
    info["feed"] = row["feed"]
    info["slug"] = row["slug"]
    return info


def main():
    rows = json.loads((ROOT / "data/catalog.json").read_text())
    out = []
    with ThreadPoolExecutor(max_workers=24) as pool:
        futures = [pool.submit(one, row) for row in rows]
        for i, future in enumerate(as_completed(futures), 1):
            out.append(future.result())
            if i % 100 == 0:
                print("fetched", i, flush=True)
    (ROOT / "data/feed_copy.json").write_text(json.dumps(out, indent=2) + "\n")
    ok = sum(1 for row in out if row.get("ok"))
    summaries = sum(1 for row in out if len(row.get("summary") or "") >= 40)
    langs = sum(1 for row in out if row.get("language"))
    print(f"wrote {len(out)} ok={ok} summaries={summaries} langs={langs}")


if __name__ == "__main__":
    main()
