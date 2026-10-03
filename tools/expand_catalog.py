#!/usr/bin/env python3
"""Discover show feeds from public charts, then keep only publisher RSS fields.

Does not call Podcast Index and does not save chart payloads or audio.
"""

import html
import json
import re
import ssl
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = "WhereToListenCatalog/1.0 (metadata only; no media)"
CTX = ssl.create_default_context()
GENRES = {
    "26": "Culture",
    "1301": "Culture",
    "1303": "Comedy",
    "1304": "Learning",
    "1305": "Kids",
    "1309": "Culture",
    "1310": "Music",
    "1314": "Society",
    "1318": "Technology",
    "1321": "Business",
    "1324": "Culture",
    "1483": "Fiction",
    "1487": "History",
    "1488": "True crime",
    "1489": "News",
    "1502": "Culture",
    "1511": "News",
    "1512": "Health",
    "1533": "Science",
    "1545": "Sports",
}
TARGET = 1000

def get(url, limit=900000, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, application/rss+xml, */*"})
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read(limit)

def slugify(title):
    s = title.lower()
    s = s.replace("&", " and ").replace("’", "'")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return (s or "show")[:70]

def shorten(desc):
    text = re.sub(r"<[^>]+>", " ", desc or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"https?://\S+", "", text).strip()
    if len(text) < 40:
        return ""
    if len(text) <= 240:
        return text
    cut = text[:240]
    for sep in (". ", "? ", "! "):
        i = cut.rfind(sep)
        if i > 80:
            return cut[: i + 1].strip()
    return cut.rsplit(" ", 1)[0].rstrip(" ,;:") + "…"

def norm_feed(url):
    try:
        p = urllib.parse.urlsplit(url.strip())
    except Exception:
        return ""
    host = p.netloc.lower().removeprefix("www.")
    path = p.path.rstrip("/")
    return f"{host}{path}"

def chart_ids():
    found = {}
    def one(gid, cat):
        url = f"https://itunes.apple.com/us/rss/toppodcasts/limit=100/genre={gid}/json"
        try:
            data = json.loads(get(url, 2_000_000, 30))
        except Exception as e:
            print("chart fail", gid, type(e).__name__)
            return []
        rows = []
        for entry in data.get("feed", {}).get("entry", []):
            iid = (entry.get("id") or {}).get("attributes", {}).get("im:id")
            if iid:
                rows.append((iid, cat))
        print("chart", gid, cat, len(rows))
        return rows
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(one, gid, cat) for gid, cat in GENRES.items()]
        for f in as_completed(futs):
            for iid, cat in f.result():
                found.setdefault(iid, cat)
    return found

def lookup_feeds(ids):
    feeds = {}
    id_list = list(ids)
    def batch(chunk):
        url = "https://itunes.apple.com/lookup?entity=podcast&id=" + ",".join(chunk)
        try:
            data = json.loads(get(url, 3_000_000, 40))
        except Exception as e:
            print("lookup fail", type(e).__name__, e)
            return []
        out = []
        for row in data.get("results", []):
            if row.get("kind") not in (None, "podcast") and row.get("wrapperType") != "track":
                continue
            feed = row.get("feedUrl") or ""
            if not feed.startswith("http"):
                continue
            out.append({
                "id": str(row.get("collectionId") or ""),
                "feed": feed,
                "artist": row.get("artistName") or "",
                "explicit": (row.get("collectionExplicitness") or "") == "explicit",
            })
        return out
    chunks = [id_list[i:i+150] for i in range(0, len(id_list), 150)]
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(batch, c) for c in chunks]
        for f in as_completed(futs):
            for row in f.result():
                feeds[row["id"]] = row
    print("feeds", len(feeds), "of", len(id_list))
    return feeds

def parse_rss(raw):
    text = raw.decode("utf-8", "replace")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    parts = re.split(r"<item\b", text, maxsplit=1, flags=re.I)
    head = parts[0]
    item = "<item" + parts[1].split("</item>")[0] if len(parts) > 1 else ""

    def clean(s):
        s = re.sub(r"<!\[CDATA\[|\]\]>", "", s or "")
        s = re.sub(r"<[^>]+>", " ", s)
        return re.sub(r"\s+", " ", html.unescape(s)).strip()

    def tag(block, name):
        m = re.search(rf"<{name}(?:\s[^>]*)?>(.*?)</{name}>", block, re.I | re.S)
        return clean(m.group(1)) if m else ""

    title = tag(head, "title")
    links = re.findall(r"<link>([^<]+)</link>", head, re.I)
    link = clean(links[0]) if links else ""
    author = tag(head, "itunes:author") or tag(head, "author")
    image_m = re.search(r"<itunes:image[^>]*href=[\"']([^\"']+)[\"']", head, re.I)
    image = html.unescape(image_m.group(1).strip()) if image_m else ""
    if not image:
        im = re.search(r"<image>.*?<url>(.*?)</url>", head, re.I | re.S)
        image = clean(im.group(1)) if im else ""
    desc = ""
    dm = re.search(r"<description(?:\s[^>]*)?>(.*?)</description>", head, re.I | re.S)
    if dm:
        desc = dm.group(1)
    explicit = tag(head, "itunes:explicit").lower() in ("yes", "true", "explicit")
    ep = tag(item, "title") if item else ""
    pub = tag(item, "pubDate") if item else ""
    dt = ""
    if pub:
        try:
            dt = parsedate_to_datetime(pub).isoformat()
        except Exception:
            dt = ""
    return {
        "title": title[:160],
        "link": link[:240],
        "author": author[:140],
        "image": image[:500],
        "blurb": shorten(desc),
        "explicit": explicit,
        "latestTitle": ep[:180],
        "latestDate": dt,
    }

def good_site(url, feed):
    if not url or not url.startswith("http"):
        return ""
    low = url.lower()
    if any(b in low for b in ("apple.com", "itunes.apple", "podcasts.apple", "spotify.com/show")):
        # spotify show pages are official homes for some studios; allow them
        if "spotify.com/show" not in low:
            return ""
    if low.split("?")[0].endswith((".mp3", ".m4a", ".mp4")):
        return ""
    if norm_feed(url) and norm_feed(url) == norm_feed(feed):
        return ""
    return url.split("?")[0] if "utm_" in url else url

def fetch_one(job):
    feed = job["feed"]
    try:
        raw = get(feed, 160000, 18)
        info = parse_rss(raw)
    except Exception:
        return None
    if not info["title"] or len(info["title"]) < 2:
        return None
    # reject if the "feed" was an html page
    if info["title"].lower() in ("html", "just a moment...", "attention required"):
        return None
    site = good_site(info["link"], feed)
    blurb = info["blurb"] or f"A {job['category'].lower()} podcast. New episodes stay on the publisher’s own feed."
    return {
        "feed": feed,
        "title": info["title"],
        "host": info["author"] or job.get("artist") or "The publisher",
        "category": job["category"],
        "site": site,
        "artwork": info["image"] if info["image"].startswith("http") else "",
        "blurb": blurb,
        "explicit": bool(info["explicit"] or job.get("explicit")),
        "latestTitle": info["latestTitle"],
        "latestDate": info["latestDate"],
        "handwritten": False,
    }

def main():
    ids = chart_ids()
    print("unique chart ids", len(ids))
    looked = lookup_feeds(ids)
    jobs = []
    seen_feeds = set()
    for iid, cat in ids.items():
        row = looked.get(iid)
        if not row:
            continue
        key = norm_feed(row["feed"])
        if not key or key in seen_feeds:
            continue
        seen_feeds.add(key)
        jobs.append({**row, "category": cat})
    print("unique feeds", len(jobs))

    editorial = json.loads((ROOT / "data/editorial.json").read_text())
    snap = {norm_feed(r["feed"]): r for r in json.loads((ROOT / "data/feed_snapshot.json").read_text())}
    by_feed_ed = {}
    for row in editorial:
        src = snap.get(norm_feed(json.loads((ROOT / "data/feed_snapshot.json").read_text())[0]["feed"]))
    # map editorial slug -> snapshot feed
    snap_by_slug = {r["slug"]: r for r in json.loads((ROOT / "data/feed_snapshot.json").read_text())}
    ed_by_norm = {}
    for row in editorial:
        src = snap_by_slug.get(row["slug"])
        if not src:
            continue
        ed_by_norm[norm_feed(src["feed"])] = {**row, **{
            "feed": src["feed"],
            "artwork": src.get("artwork") or "",
            "latestTitle": src.get("latestTitle") or "",
            "latestDate": src.get("latestDate") or "",
            "explicit": bool(src.get("explicit")),
            "handwritten": True,
        }}

    # Prefer editorial copies; still fetch RSS only for the rest.
    records = []
    used = set()
    for key, row in ed_by_norm.items():
        used.add(key)
        records.append(row)
    todo = [j for j in jobs if norm_feed(j["feed"]) not in used]
    print("to fetch", len(todo), "keeping editorial", len(records))

    ok = 0
    with ThreadPoolExecutor(max_workers=18) as ex:
        futs = [ex.submit(fetch_one, job) for job in todo]
        for i, f in enumerate(as_completed(futs), 1):
            row = f.result()
            if row:
                key = norm_feed(row["feed"])
                if key not in used:
                    used.add(key)
                    records.append(row)
                    ok += 1
            if i % 100 == 0:
                print("progress", i, "kept", ok)
            if len(records) >= TARGET:
                break
    print("records", len(records))

    slugs = set()
    for row in records:
        if row.get("slug") and row.get("handwritten"):
            slugs.add(row["slug"])
            continue
        base = slugify(row["title"])
        slug = base
        n = 2
        while slug in slugs:
            slug = f"{base}-{n}"
            n += 1
        row["slug"] = slug
        slugs.add(slug)
        row.pop("id", None)
        row.pop("artist", None)

    # handwritten rows already have slug from editorial
    out = []
    for row in records:
        out.append({
            "slug": row["slug"],
            "title": row["title"] if not row.get("handwritten") else snap_by_slug[row["slug"]]["title"],
            "host": row["host"],
            "category": row["category"],
            "site": row.get("site") or "",
            "feed": row["feed"],
            "artwork": html.unescape(row.get("artwork") or ""),
            "blurb": row["blurb"],
            "explicit": bool(row.get("explicit")),
            "latestTitle": row.get("latestTitle") or "",
            "latestDate": row.get("latestDate") or "",
            "handwritten": bool(row.get("handwritten")),
        })
    # fix handwritten titles from snapshot (feed title)
    (ROOT / "data/catalog.json").write_text(json.dumps(out, indent=2) + "\n")
    print("wrote", len(out))

if __name__ == "__main__":
    main()
