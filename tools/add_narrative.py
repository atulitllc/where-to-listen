#!/usr/bin/env python3
"""Add curated narrative shows from their publisher RSS feeds.

Discovers nothing from Podcast Index. Saves channel fields and one episode
title only. Audio enclosures are discarded.
"""

import html
import json
import re
import ssl
import urllib.parse
import urllib.request
from email.utils import parsedate_to_datetime
from pathlib import Path

from essay_copy import EXISTING, NEW

ROOT = Path(__file__).resolve().parents[1]
UA = "WhereToListenCatalog/1.0 (metadata only; no media)"
CTX = ssl.create_default_context()
FEEDS = json.loads((Path(__file__).resolve().parent / "narrative_feeds.json").read_text())

SKIP_ITEM = re.compile(
    r"\b(trailer|teaser|preview|introducing|introduces|audiobook)\b|"
    r"\bpresents\b|\bfrom npr\b|^from\b|coming soon|special preview|new from\b|"
    r"^listen now\b|^featuring\b|^listen to\b|^new npr series\b|"
    r"alternate realities from|^tested\b|watch the queen\b",
    re.I,
)


def get(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, */*"},
    )
    with urllib.request.urlopen(req, timeout=22, context=CTX) as response:
        return response.read(220000)


def clean(value):
    text = re.sub(r"<!\[CDATA\[|\]\]>", "", value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def tag(block, name):
    match = re.search(rf"<{name}(?:\s[^>]*)?>(.*?)</{name}>", block, re.I | re.S)
    return clean(match.group(1)) if match else ""


def slugify(title):
    text = title.lower().replace("&", " and ").replace("’", "'")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return (text or "show")[:70]


def norm_feed(url):
    try:
        parts = urllib.parse.urlsplit(url.strip())
    except Exception:
        return ""
    return parts.netloc.lower().removeprefix("www.") + parts.path.rstrip("/")


def usable_site(url, feed):
    if not url or not url.startswith("http"):
        return ""
    low = url.lower()
    if any(bit in low for bit in ("apple.com", "itunes.apple", "podcasts.apple")):
        return ""
    if "spotify.com" in low and "/show/" not in low:
        return ""
    if low.split("?")[0].endswith((".mp3", ".m4a", ".mp4")):
        return ""
    if norm_feed(url) and norm_feed(url) == norm_feed(feed):
        return ""
    return url.split("?")[0] if "utm_" in url else url


def good_item(title, show_title):
    if not title or SKIP_ITEM.search(title):
        return False
    low = title.lower()
    show = show_title.lower()
    if show not in low and low.startswith("decoder ring"):
        return False
    if "my mom" in low and "murder" in low and "mom" not in show:
        return False
    if low.startswith("listen now"):
        return False
    return True


def parse(raw, feed, show_title):
    text = raw.decode("utf-8", "replace")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    parts = re.split(r"<item\b", text, flags=re.I)
    head = parts[0]
    image_m = re.search(r"<itunes:image[^>]*href=[\"']([^\"']+)[\"']", head, re.I)
    image = html.unescape(image_m.group(1).strip()) if image_m else ""
    links = re.findall(r"<link>([^<]+)</link>", head, re.I)
    explicit = tag(head, "itunes:explicit").lower() in ("yes", "true", "explicit")
    language = (tag(head, "language") or tag(head, "dc:language")).lower().replace("_", "-")[:16]
    chosen = None
    fallback = None
    for item in parts[1:40]:
        block = item.split("</item>")[0]
        title = tag(block, "title")
        pub = tag(block, "pubDate")
        dt = ""
        if pub:
            try:
                dt = parsedate_to_datetime(pub).isoformat()
            except Exception:
                dt = ""
        row = (title, dt)
        if fallback is None and title:
            fallback = row
        if good_item(title, show_title):
            chosen = row
            break
    latest, latest_dt = chosen or fallback or ("", "")
    return {
        "title": tag(head, "title")[:160],
        "author": (tag(head, "itunes:author") or tag(head, "author"))[:140],
        "link": clean(links[0])[:240] if links else "",
        "image": image[:500],
        "explicit": explicit,
        "latestTitle": latest[:180],
        "latestDate": latest_dt,
        "language": language,
        "feed": feed,
    }


def refresh_latest():
    """Replace promo episode titles on shows this script already added."""
    catalog = json.loads((ROOT / "data/catalog.json").read_text())
    essays = json.loads((ROOT / "data/essays.json").read_text())
    changed = 0
    for row in catalog:
        if row.get("category") != "Narrative" or not row.get("handwritten"):
            continue
        current = row.get("latestTitle") or ""
        if good_item(current, row.get("title") or ""):
            continue
        feed = row.get("feed") or ""
        if not feed:
            continue
        try:
            info = parse(get(feed), feed, row.get("title") or "")
        except Exception as exc:
            print("refresh fail", row.get("slug"), type(exc).__name__)
            continue
        nxt = info["latestTitle"]
        if not nxt or nxt == current or not good_item(nxt, row.get("title") or ""):
            print("still promo", row.get("slug"), "|", nxt[:70])
            continue
        print("fix", row["slug"], "->", nxt[:70])
        row["latestTitle"] = nxt
        row["latestDate"] = info["latestDate"]
        changed += 1
    dissect = next((row for row in catalog if row.get("slug") == "dissect"), None)
    if dissect and "dissect" not in essays and "Dissect" in NEW:
        essays["dissect"] = NEW["Dissect"]["paragraphs"]
        print("essay dissect")
    (ROOT / "data/catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")
    (ROOT / "data/essays.json").write_text(json.dumps(essays, indent=2, ensure_ascii=False) + "\n")
    print("refreshed", changed)


def main():
    catalog = json.loads((ROOT / "data/catalog.json").read_text())
    feeds = {norm_feed(row["feed"]) for row in catalog}
    titles = {row["title"].lower().strip() for row in catalog}
    slugs = {row["slug"] for row in catalog}
    essays = dict(EXISTING)
    added = []
    for key, meta in NEW.items():
        feed = FEEDS.get(key)
        if not feed:
            print("no feed", key)
            continue
        if norm_feed(feed) in feeds:
            print("dup feed", key)
            continue
        try:
            info = parse(get(feed), feed, meta.get("host") or key)
        except Exception as exc:
            print("fetch fail", key, type(exc).__name__)
            continue
        title = info["title"] or key
        if title.lower().strip() in titles:
            print("dup title", title)
            continue
        if len(title) < 2:
            print("bad title", key)
            continue
        base = slugify(title)
        slug = base
        n = 2
        while slug in slugs:
            slug = f"{base}-{n}"
            n += 1
        slugs.add(slug)
        titles.add(title.lower().strip())
        feeds.add(norm_feed(feed))
        first = meta["paragraphs"][0]
        row = {
            "slug": slug,
            "title": title,
            "host": meta["host"],
            "category": "Narrative",
            "site": usable_site(info["link"], feed),
            "feed": feed,
            "artwork": info["image"] if info["image"].startswith("http") else "",
            "blurb": first,
            "explicit": bool(info["explicit"]),
            "latestTitle": info["latestTitle"],
            "latestDate": info["latestDate"],
            "handwritten": True,
            "publisher": info["author"] or meta["host"],
            "language": info["language"],
            "languageLabel": "",
            "description": "\n\n".join(meta["paragraphs"]),
        }
        catalog.append(row)
        essays[slug] = meta["paragraphs"]
        added.append((slug, title, info["latestTitle"][:60]))
        print("add", title, "|", info["latestDate"][:10], "|", info["latestTitle"][:70])
    catalog.sort(key=lambda row: row["title"].lower())
    (ROOT / "data/catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")
    (ROOT / "data/essays.json").write_text(json.dumps(essays, indent=2, ensure_ascii=False) + "\n")
    print("added", len(added), "catalog", len(catalog), "essays", len(essays))


if __name__ == "__main__":
    main()
