#!/usr/bin/env python3
"""Generate the static Where to Listen catalog. Does not download audio."""

import html
import json
import re
import shutil
import unicodedata
import urllib.parse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
ET = ZoneInfo("America/New_York")
FETCHED = "Oct 3, 2026"
HOME_TITLE = "Podcast catalog | Where to Listen"
HOME_DESC = "Browse a catalog of podcasts. Links go to each show’s own feed. This site does not host episodes."
SHOW_SUFFIX = "Links go to this show’s own feed. This site does not host episodes."
CATS = [
    "News",
    "Narrative",
    "True crime",
    "Comedy",
    "Culture",
    "History",
    "Science",
    "Business",
    "Technology",
    "Sports",
    "Music",
    "Fiction",
    "Health",
    "Learning",
    "Society",
    "Kids",
]
# Readable slugs for titles whose old slugs were leftovers (show, show-3, lin, 101).
# Every other slug already in the catalog stays frozen.
REPLACED_SLUGS = {
    "硅谷101": "silicon-valley-101",
    "小Lin说": "xiao-lin-shuo",
    "岩中花述": "flower-on-the-rock",
    "天真不天真": "tian-zhen-bu-tian-zhen",
    "安住紳一郎の日曜天国": "azumi-shinichiro-sunday-heaven",
    "自我进化论": "self-evolution-theory",
    "پادکست رخ": "rokh",
}
BAD_SLUG = re.compile(r"^(?:show(?:-\d+)?|lin|\d+)$")
STUB_RE = re.compile(
    r"^A .+ podcast\. New episodes stay on the publisher[’']s own feed\.?$",
    re.I,
)
LANG_NAMES = {
    "en": "English",
    "en-us": "English",
    "en-gb": "English",
    "en-au": "English",
    "en-ca": "English",
    "es": "Spanish",
    "es-es": "Spanish",
    "es-mx": "Spanish",
    "es-419": "Spanish",
    "fr": "French",
    "fr-fr": "French",
    "fr-ca": "French",
    "de": "German",
    "de-de": "German",
    "pt": "Portuguese",
    "pt-br": "Portuguese",
    "pt-pt": "Portuguese",
    "it": "Italian",
    "nl": "Dutch",
    "sv": "Swedish",
    "no": "Norwegian",
    "da": "Danish",
    "fi": "Finnish",
    "pl": "Polish",
    "ru": "Russian",
    "uk": "Ukrainian",
    "ja": "Japanese",
    "ja-jp": "Japanese",
    "zh": "Chinese",
    "zh-cn": "Chinese",
    "zh-hans": "Chinese",
    "zh-tw": "Chinese",
    "zh-hant": "Chinese",
    "ko": "Korean",
    "ko-kr": "Korean",
    "ar": "Arabic",
    "fa": "Persian",
    "fa-ir": "Persian",
    "hi": "Hindi",
    "tr": "Turkish",
    "he": "Hebrew",
    "id": "Indonesian",
    "vi": "Vietnamese",
    "th": "Thai",
    "el": "Greek",
    "cs": "Czech",
    "hu": "Hungarian",
    "ro": "Romanian",
}
# Original catalog copy where the feed text was missing, damaged, or not English.
HAND = {
    "The Dale Jr. Download": [
        "Dale Earnhardt Jr., a fifteen-time Most Popular Driver in NASCAR and a two-time winner of the Daytona 500, hosts this Dirty Mo Media series.",
        "Conversations follow the racing week, the garage, and the stories that sit around the sport. The shelf files the show under Sports.",
    ],
    "Lakepointe Church with Josh Howerton": [
        "Each week Lakepointe Church releases teaching from senior pastor Josh Howerton or another pastor on the church staff.",
        "The episodes are sermons and lessons for the congregation. Lakepointe Church is the publisher, and the shelf files the series under Society.",
    ],
    "硅谷101": [
        "硅谷101 is a Chinese technology interview series started by the journalist 泓君.",
        "Episodes sit with founders, scientists, and the ideas coming out of the tech industry, including the failures and arguments around them. The feed’s language tag is Chinese, and the shelf files the show under Technology.",
    ],
    "小Lin说": [
        "小Lin说 explains business and finance in plain language.",
        "The host studied economics at Peking University and previously worked as an analyst at J.P. Morgan. The feed’s language tag is Chinese, and the shelf files the show under Culture.",
    ],
    "岩中花述": [
        "Flower on the Rock, whose Chinese title is 岩中花述, is an interview series from the Italian house GIADA.",
        "The show gathers women who have walked their own paths and talks through the ideas that shape a life. GIADA calls it a spiritual wardrobe for the intellect and the soul. The feed’s language tag is Chinese.",
    ],
    "天真不天真": [
        "天真不天真 is 杨天真’s Chinese-language series.",
        "Episodes move between personal stories and conversations with guests, some of them playful and some of them more guarded. The feed’s language tag is Chinese.",
    ],
    "安住紳一郎の日曜天国": [
        "安住紳一郎の日曜天国 is TBS Radio’s Sunday morning show with announcer Shinichiro Azumi.",
        "The podcast carries his opening talk and his replies to listener messages from the weekly broadcast. The feed’s language tag is Japanese, and TBS Radio is the publisher.",
    ],
    "自我进化论": [
        "自我进化论 is 颜晓静’s Chinese series about self-exploration and looking after yourself.",
        "Episodes use personal stories to talk about noticing what you actually want. The feed’s language tag is Chinese.",
    ],
    "پادکست رخ": [
        "Rokh Podcast tells life stories of people who shaped parts of Iranian and world history.",
        "The publisher name on the feed is Rokh Podcast. The feed’s language tag is Persian, and the shelf files the show under History.",
    ],
    "DOUBLE COVERAGE PODCAST": [
        "Double Coverage is Mystic Zach’s sports show.",
        "The Buzzsprout page linked from the feed is the public home for the series. The shelf files it under Sports.",
    ],
    "Defected Radio": [
        "Defected Radio is the long-running house-music show from Defected Records.",
        "Guest mixes and label sessions are the heart of the series. Defected is the publisher, and the shelf files the show under Music.",
    ],
    "Shots Fired in Anger": [
        "Shots Fired in Anger is a series from Geissele Automatics.",
        "The publisher’s site and RSS are the way off this page. The shelf files the show under Technology.",
    ],
    "Soder": [
        "Soder is Dan Soder’s comedy show.",
        "The Audioboom channel is the official home listed on the feed. The shelf files the series under Comedy.",
    ],
    "Skill Up": [
        "Skill Up is a culture show from the game critic of the same name.",
        "Episodes talk through games and the industry around them. The shelf files the series under Culture.",
    ],
    "GOONS": [
        "GOONS is a culture series. The publisher name on the feed is The Goons Podcast.",
        "This page collects that feed and the category so the show is easy to find. The shelf files it under Culture.",
    ],
    "The Martyr Made Podcast": [
        "The Martyr Made Podcast is Darryl Cooper’s long-form history series.",
        "Episodes stay with war, ideology, and the people caught inside those stories. martyrmade.com is the official site, and the shelf files the show under History.",
    ],
    "The Art Bell Archive": [
        "The Art Bell Archive collects Art Bell’s overnight radio programs in chronological order, with another episode added each day.",
        "Arthur William Bell III is the host named on the feed. The shelf files the archive under History.",
    ],
    "Danny Jones Podcast": [
        "The Danny Jones Podcast is a long-form interview show from Danny Jones and Daylight Media.",
        "Conversations wander through culture, science, and claims that sit outside the usual news cycle. The shelf files the show under Culture.",
    ],
    "The History of English Podcast": [
        "The History of English Podcast, from Kevin Stroud, follows the English language from its oldest roots into modern speech.",
        "Episodes are narrative lessons rather than a headline roundup. historyofenglishpodcast.com is the official site, and the shelf files the show under History.",
    ],
    "Lighthouse Horror Podcast": [
        "Lighthouse Horror Podcast publishes original scary fiction.",
        "Stories stay on the publisher’s feed, and lighthousehorror.com is the official site. The shelf files the show under Fiction.",
    ],
    "The Archers": [
        "The Archers is BBC Radio 4’s long-running contemporary drama, set in a rural community.",
        "BBC Radio 4 is the publisher. The shelf files the series under Fiction.",
    ],
    "On Being with Krista Tippett": [
        "On Being with Krista Tippett is a run of conversations about meaning, faith, and the inner life.",
        "Krista Tippett is the host, and onbeing.org is the official site. The shelf files the show under Culture.",
    ],
    "Tony Evans' Sermons - Audio": [
        "The Urban Alternative is the national ministry of Dr. Tony Evans. It is dedicated to restoring hope and transforming lives through the proclamation and application of the Word of God.",
        "This audio series collects his sermons. Dr. Tony Evans is the publisher named on the catalog, and the shelf files the show under Society.",
    ],
}

BOOT = """<script>
try {
  var t = localStorage.getItem("wtl-theme");
  if (t !== "light" && t !== "dark") {
    t = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  document.documentElement.setAttribute("data-theme", t);
} catch (e) {
  document.documentElement.setAttribute("data-theme", "light");
}
</script>"""

WAVE = """<svg class="wave" viewBox="0 0 88 28" aria-hidden="true">
  <rect x="2" y="10" width="4" height="12" rx="1" fill="currentColor"/>
  <rect x="10" y="4" width="4" height="20" rx="1" fill="currentColor"/>
  <rect x="18" y="8" width="4" height="16" rx="1" fill="currentColor"/>
  <rect x="26" y="2" width="4" height="24" rx="1" fill="currentColor"/>
  <rect x="34" y="9" width="4" height="14" rx="1" fill="currentColor"/>
  <rect x="42" y="5" width="4" height="18" rx="1" fill="currentColor"/>
  <rect x="50" y="11" width="4" height="10" rx="1" fill="currentColor"/>
  <rect x="58" y="6" width="4" height="16" rx="1" fill="currentColor"/>
  <rect x="66" y="3" width="4" height="22" rx="1" fill="currentColor"/>
  <rect x="74" y="9" width="4" height="12" rx="1" fill="currentColor"/>
  <rect x="82" y="12" width="4" height="8" rx="1" fill="currentColor"/>
</svg>"""

CLOSERS = [
    "The publisher is {publisher}. This shelf files the show under {category}.",
    "{publisher} is the publisher named on the feed. The catalog groups it with {category}.",
    "On this shelf, {title} sits in {category}. {publisher} puts the series out.",
    "{title} is grouped with {category}. {publisher} is the publisher on the feed.",
    "This catalog files {title} under {category}, with {publisher} as the publisher.",
    "{publisher} publishes {title}. You will find it in the {category} section of the shelf.",
]


def esc(value):
    return html.escape(value or "", quote=True)


def deliquid(value):
    return (value or "").replace("{{", "{ {").replace("{%", "{ %")


def scrub_banned(text):
    text = text or ""
    text = re.sub(r"\bdownloadables?\b", "printables", text, flags=re.I)
    text = re.sub(r"\bfree\s+downloads?\b", "", text, flags=re.I)
    text = re.sub(r"\bdaily downloaded\b", "daily", text, flags=re.I)
    text = re.sub(r"\bmost downloaded\b", "widely heard", text, flags=re.I)
    text = re.sub(r"\bdownloaded\b", "heard", text, flags=re.I)
    text = re.sub(r"\bdownloading\b", "opening", text, flags=re.I)
    text = re.sub(r"\bdownloads\b", "listens", text, flags=re.I)
    text = re.sub(r"\bdownload\b", "listen", text, flags=re.I)
    text = re.sub(r"\btorrents?\b", "", text, flags=re.I)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"\(\s*\)", "", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def strip_feed_text(value):
    text = value or ""
    text = re.sub(r"<!\[CDATA\[", " ", text, flags=re.I)
    text = text.replace("]]>", " ")
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\b[\w.+-]+@[\w.-]+\.\w+\b", " ", text)
    text = re.sub(
        r"hosted on acast\.?\s*(see\s*)?acast\.com/privacy for more information\.?",
        " ",
        text,
        flags=re.I,
    )
    text = re.sub(r"acast\.com/privacy.*", " ", text, flags=re.I)
    text = re.sub(r"become a supporter of this podcast\s*:?", " ", text, flags=re.I)
    text = scrub_banned(text)
    text = re.sub(r"\s+", " ", text).strip(" \t\r\n-–—|,;:")
    return text.strip()


def mostly_latin(text):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return True
    latin = sum(1 for c in letters if "LATIN" in unicodedata.name(c, ""))
    return latin / len(letters) >= 0.6


def good_blurb(text):
    cleaned = strip_feed_text(text)
    if len(cleaned) < 40:
        return ""
    if STUB_RE.match(cleaned):
        return ""
    if "acast.com/privacy" in cleaned.lower() or "]]>" in cleaned or "cdata" in cleaned.lower():
        return ""
    return cleaned


def sentences(text):
    parts = re.split(r"(?<=[.!?。！？])\s+", text or "")
    return [part.strip() for part in parts if part.strip()]


def clip_sentence(text, limit=170):
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:")
    return cut


def language_info(code):
    raw = (code or "").strip().lower().replace("_", "-")
    if raw in {"english", "eng"}:
        raw = "en"
    if raw in LANG_NAMES:
        return raw, LANG_NAMES[raw]
    primary = raw.split("-")[0] if raw else ""
    if primary in LANG_NAMES:
        return raw, LANG_NAMES[primary]
    return "", ""


def usable_site(url, feed):
    if not url or not str(url).startswith("http"):
        return ""
    low = url.lower()
    if any(bit in low for bit in ("apple.com", "itunes.apple", "podcasts.apple")):
        return ""
    if "spotify.com" in low and "/show/" not in low and "podcasters.spotify.com" not in low:
        return ""
    if low.split("?")[0].endswith((".mp3", ".m4a", ".mp4")):
        return ""

    def norm(value):
        try:
            parts = urllib.parse.urlsplit(value.strip())
        except Exception:
            return ""
        return parts.netloc.lower().removeprefix("www.") + parts.path.rstrip("/")

    if norm(url) and norm(url) == norm(feed):
        return ""
    return url.split("?")[0] if "utm_" in url else url


def closer_for(show):
    template = CLOSERS[sum(ord(c) for c in show["slug"]) % len(CLOSERS)]
    line = template.format(publisher=show["publisher"], category=show["category"], title=show["title"])
    label = show.get("languageLabel") or ""
    if label and label != "English":
        line = f"{line} The feed’s language tag is {label}."
    return line


def split_paragraphs(summary):
    parts = sentences(summary)
    if not parts:
        return []
    if len(summary) < 300 or len(parts) == 1:
        return [summary]
    mid = max(1, len(parts) // 2)
    if mid >= len(parts):
        mid = len(parts) - 1
    first = " ".join(parts[:mid]).strip()
    second = " ".join(parts[mid:]).strip()
    return [part for part in (first, second) if part]


def ensure_length(paragraphs, show):
    text = " ".join(paragraphs)
    if len(text) >= 280:
        return paragraphs
    extra = []
    latest = strip_feed_text(show.get("latestTitle") or "")
    if latest:
        extra.append(f"A recent episode title on the publisher’s feed is “{latest}”.")
    extra.append(
        f"The official site and the feed on this page are where {show['publisher']} carries {show['title']}."
    )
    return paragraphs + [" ".join(extra)]


def compose(show):
    title = show["title"]
    if title in HAND:
        paragraphs = [scrub_banned(part) for part in HAND[title]]
    else:
        raw_summary = good_blurb(show.get("sourceSummary") or "")
        summary = raw_summary if raw_summary and mostly_latin(raw_summary) else ""
        native = raw_summary if raw_summary and not mostly_latin(raw_summary) else ""
        handwritten = good_blurb(show.get("blurb") or "") if show.get("handwritten") else ""
        catalog_blurb = "" if show.get("handwritten") else good_blurb(show.get("blurb") or "")
        closer = closer_for(show)
        if handwritten:
            paragraphs = [handwritten]
            if summary and summary[:80].lower() != handwritten[:80].lower():
                paragraphs.extend(split_paragraphs(summary))
            elif native:
                paragraphs.append(native)
            paragraphs.append(closer)
        elif summary:
            paragraphs = split_paragraphs(summary) + [closer]
        elif native:
            paragraphs = [
                f"{title} is published by {show['publisher']}.",
                native,
                closer,
            ]
        elif catalog_blurb:
            paragraphs = split_paragraphs(catalog_blurb) + [closer]
        else:
            paragraphs = [
                f"{title} is published by {show['publisher']}.",
                f"The series is grouped with {show['category']} on this shelf.",
            ]
    paragraphs = [re.sub(r"\s+", " ", part).strip() for part in paragraphs if part and part.strip()]
    paragraphs = ensure_length(paragraphs, show)
    show["paragraphs"] = paragraphs
    show["description"] = "\n\n".join(paragraphs)
    first = sentences(paragraphs[0])
    sentence = first[0] if first else paragraphs[0]
    if not sentence.endswith((".", "!", "?")):
        sentence += "."
    show["sentence"] = scrub_banned(sentence)
    if not show.get("handwritten"):
        show["blurb"] = show["sentence"]
    return show


def fmt_date(iso):
    if not iso:
        return ""
    dt = datetime.fromisoformat(iso)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ET)
    return dt.astimezone(ET).strftime("%b %-d, %Y") + " ET"


def initials(title):
    parts = [p for p in title.replace("&", " ").replace("’", "'").split() if p]
    letters = []
    for part in parts:
        if part[0].isalnum():
            letters.append(part[0].upper())
        if len(letters) == 2:
            break
    return "".join(letters) or "W"


def hue(slug):
    return sum(ord(c) for c in slug) % 360


def assign_slugs(shows):
    used = set()
    for show in shows:
        slug = show["slug"]
        title = show["title"]
        if title in REPLACED_SLUGS or BAD_SLUG.match(slug or ""):
            slug = REPLACED_SLUGS.get(title) or slug
        base = slug
        n = 2
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        show["slug"] = slug
        used.add(slug)


def related_shows(show, shows):
    peers = [other for other in shows if other["category"] == show["category"] and other["slug"] != show["slug"]]
    peers.sort(key=lambda other: other["title"].lower())
    chosen = []
    if peers:
        mine = show["title"].lower()
        idx = 0
        while idx < len(peers) and peers[idx]["title"].lower() < mine:
            idx += 1
        for step in range(len(peers)):
            chosen.append(peers[(idx + step) % len(peers)])
            if len(chosen) == 6:
                break
    if len(chosen) < 4:
        seen = {item["slug"] for item in chosen} | {show["slug"]}
        for other in shows:
            if other["slug"] in seen:
                continue
            chosen.append(other)
            if len(chosen) == 6:
                break
    return chosen


def head(title, description, depth, current):
    prefix = "../" * depth
    nav_home = ' aria-current="page"' if current == "home" else ""
    nav_about = ' aria-current="page"' if current == "about" else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(description)}">
<meta name="robots" content="noindex">
<link rel="canonical" href="./">
<title>{esc(title)}</title>
<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=IBM+Plex+Mono:wght@400;500&family=Outfit:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefix}css/site.css">
{BOOT}
</head>
<body>
<a class="skip" href="#content">Skip to content</a>
<header class="site-head">
  <div class="wrap head-inner">
    <a class="brand" href="{prefix}index.html">
      <span class="led" aria-hidden="true"></span>
      <span class="brand-copy"><small>88.0 · Shelf</small><strong>Where to Listen</strong></span>
      {WAVE}
    </a>
    <nav class="nav" aria-label="Primary">
      <a href="{prefix}index.html"{nav_home}>Shelf</a>
      <a href="{prefix}about.html"{nav_about}>About</a>
    </nav>
    <button type="button" class="theme-toggle" id="themeToggle" aria-pressed="false" aria-label="Switch color theme">
      <span class="knob" aria-hidden="true"></span>
      <span class="toggle-label">Theme</span>
    </button>
  </div>
</header>
"""


FOOT = """<footer class="site-foot">
  <div class="wrap">
    <p>Where to Listen is a browse-only catalog. It does not host, sell, or mirror episode audio.</p>
    <p>Show titles, feeds, and artwork addresses come from each publisher’s public RSS. Descriptions on this shelf are catalog copy edited for these pages. See the About page.</p>
  </div>
</footer>
<script src="{prefix}js/theme.js"></script>
{extra}
</body>
</html>
"""


def sleeve(show):
    art = show.get("artwork") or ""
    img = ""
    if art:
        img = f'<img src="{esc(art)}" alt="" referrerpolicy="no-referrer" onerror="this.remove()">'
    return f'''<div class="sleeve" style="--hue:{hue(show["slug"])}">
      {img}
      <span class="initials" aria-hidden="true">{esc(initials(show["title"]))}</span>
    </div>'''


def json_ld(show):
    data = {
        "@context": "https://schema.org",
        "@type": "PodcastSeries",
        "name": show["title"],
        "description": show["sentence"],
        "webFeed": show["feed"],
    }
    if show.get("artwork"):
        data["image"] = show["artwork"]
    if show.get("publisher"):
        data["author"] = {"@type": "Organization", "name": show["publisher"]}
    if show.get("language"):
        data["inLanguage"] = show["language"]
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    return f'<script type="application/ld+json">{payload}</script>'


def load():
    rows = json.loads((ROOT / "data/catalog.json").read_text())
    copies = {}
    copy_path = ROOT / "data/feed_copy.json"
    if copy_path.exists():
        for row in json.loads(copy_path.read_text()):
            copies[row.get("feed") or ""] = row
    shows = []
    for row in rows:
        show = dict(row)
        copy = copies.get(show.get("feed") or "", {})
        code, label = language_info(copy.get("language") or show.get("language") or "")
        show["language"] = code
        show["languageLabel"] = label
        publisher = strip_feed_text(copy.get("publisher") or show.get("publisher") or "")
        if not publisher or "acast.com" in publisher.lower() or publisher.lower() == show["title"].lower():
            publisher = show.get("host") or publisher
        show["publisher"] = publisher or show.get("host") or "The publisher"
        summary = copy.get("summary") or ""
        show["sourceSummary"] = summary
        site = show.get("site") or ""
        if not usable_site(site, show.get("feed") or ""):
            site = usable_site(copy.get("link") or "", show.get("feed") or "")
        show["site"] = site or ""
        show["dateLabel"] = fmt_date(show.get("latestDate") or "")
        shows.append(show)
    assign_slugs(shows)
    for show in shows:
        for key in ("title", "host", "publisher", "blurb", "sourceSummary", "latestTitle", "category"):
            if show.get(key):
                show[key] = deliquid(show[key])
        compose(show)
    shows.sort(key=lambda show: show["title"].lower())
    return shows


def write_pages(shows):
    cards = []
    for show in shows:
        hay = " ".join([
            show["title"],
            show.get("host") or "",
            show["publisher"],
            show["category"],
            show["description"],
        ]).lower()
        flag = '<span class="flag">Explicit</span>' if show.get("explicit") else ""
        cards.append(f'''<a class="card" href="podcasts/{esc(show["slug"])}/" data-cat="{esc(show["category"])}" data-hay="{esc(hay)}">
          {sleeve(show)}
          <div class="card-body">
            <span class="cat">{esc(show["category"])}</span>
            <h2>{esc(show["title"])}{flag}</h2>
            <p class="host">{esc(show["publisher"])}</p>
          </div>
        </a>''')
    present = {show["category"] for show in shows}
    chips = ['<button type="button" class="chip" data-filter="all" aria-pressed="true">All</button>']
    for cat in CATS:
        if cat in present:
            chips.append(f'<button type="button" class="chip" data-filter="{esc(cat)}" aria-pressed="false">{esc(cat)}</button>')
    for cat in sorted(present - set(CATS)):
        chips.append(f'<button type="button" class="chip" data-filter="{esc(cat)}" aria-pressed="false">{esc(cat)}</button>')
    home = head(HOME_TITLE, HOME_DESC, 0, "home") + f'''
<main id="content">
  <section class="hero wrap">
    <p class="kicker">On air · Browse only · No player</p>
    <h1>Find the show.<br>Follow their feed.</h1>
    <p class="lede">Hundreds of shows, one shelf. Artwork and titles point at the real podcasts. The audio stays on each publisher’s feed. Nothing here is for sale.</p>
    <div class="tools">
      <label class="search">
        <input id="q" type="search" placeholder="Search shows, hosts, topics" autocomplete="off">
        <span id="count">{len(shows)}</span>
      </label>
      <div class="filters" role="group" aria-label="Categories">{''.join(chips)}</div>
    </div>
  </section>
  <section class="wrap">
    <p class="meta-row"><span>Catalog checked {FETCHED} ET</span><span>Official links only</span></p>
    <div class="grid" id="grid">{''.join(cards)}</div>
    <p class="empty" id="empty">No shows match that search. Try another name or clear the filter.</p>
  </section>
</main>
''' + FOOT.format(prefix="", extra='<script src="js/catalog.js"></script>')
    (ROOT / "index.html").write_text(home)

    about_desc = "Notes on this browse-only podcast catalog. Show pages were built from publisher feeds. This site does not host episodes."
    about = head("About | Where to Listen", about_desc, 0, "about") + f'''
<main id="content" class="page">
  <article class="wrap prose">
    <p class="kicker">Program notes</p>
    <h1>We point. We don’t host.</h1>
    <p>Where to Listen is a static shelf of popular podcasts. It is a catalog for browsing, in the same spirit as a guide that tells you where a film is playing or where a game can be found. It is not a listening app.</p>
    <h2>What you will not find here</h2>
    <p>No episode audio, no embedded players, no copied MP3s, and no pirate mirrors. There is nothing for sale. Each show page links out to the publisher’s own website and to that show’s public RSS feed, labeled as external.</p>
    <p>The line called “last episode listed in the official feed” is a title and a date read from the publisher’s RSS. It is not a file, and it is not a promise that the feed still looks the same tomorrow.</p>
    <h2>Where the facts come from</h2>
    <p>On {FETCHED} the shelf was filled from publisher RSS feeds. Public podcast charts were used only to find those feed addresses, then discarded. Each page keeps the show title, the feed URL, the artwork address already published in that feed, a description written for this catalog, and the title of the latest episode. The Podcast Index API was not called. No Podcast Index response is stored here, and show pages do not carry a Podcast Index credit.</p>
    <p>Artwork is hotlinked from that feed address. The image bytes are not copied into this site. If a publisher would rather not be hotlinked, the picture should be removed and the monogram left in its place. Feeds are linked so you can subscribe in your own app.</p>
    <h2>A note on Podcast Index</h2>
    <p>Podcast Index (<a href="https://podcastindex.org/">podcastindex.org</a>) is an open podcast directory with a developer API. Their terms (section 5.5) say not to keep a permanent copy of content the API returns. No API key was available for this build, so the API was not called. This catalog is not a Podcast Index product, is not endorsed by them, and does not display their logo as a partner mark.</p>
    <h2>Indexing</h2>
    <p>Every page on this demo sends a <code>noindex</code> robots meta tag and a relative canonical URL of <code>./</code>. Show pages live at <code>podcasts/&#123;slug&#125;/</code>.</p>
  </article>
</main>
''' + FOOT.format(prefix="", extra="")
    (ROOT / "about.html").write_text(about)

    missing = head("Page not found | Where to Listen", "That page is not on this shelf. This site does not host episodes.", 0, "") + '''
<main id="content" class="page">
  <article class="wrap prose">
    <p class="kicker">Off the dial</p>
    <h1>That page is not on this shelf.</h1>
    <p>The show link may have moved. Go back to the catalog and pick a show from there.</p>
    <p><a href="index.html">Back to the shelf</a></p>
  </article>
</main>
''' + FOOT.format(prefix="", extra="")
    (ROOT / "404.html").write_text(missing)

    old_shows = ROOT / "shows"
    if old_shows.exists():
        shutil.rmtree(old_shows)
    nojekyll = ROOT / ".nojekyll"
    if nojekyll.exists():
        nojekyll.unlink()

    pod = ROOT / "podcasts"
    pod.mkdir(exist_ok=True)
    keep = {show["slug"] for show in shows}
    for child in list(pod.iterdir()):
        if child.is_dir() and child.name not in keep:
            shutil.rmtree(child)
        elif child.is_file():
            child.unlink()

    for show in shows:
        flag = ' <span class="flag">Explicit</span>' if show.get("explicit") else ""
        facts = [
            f'<div><dt>Category</dt><dd>{esc(show["category"])}</dd></div>',
            f'<div><dt>Publisher</dt><dd>{esc(show["publisher"])}</dd></div>',
        ]
        host = show.get("host") or ""
        if host and host.lower() != show["publisher"].lower():
            facts.append(f'<div><dt>Host</dt><dd>{esc(host)}</dd></div>')
        if show.get("languageLabel"):
            facts.append(f'<div><dt>Language</dt><dd>{esc(show["languageLabel"])}</dd></div>')
        body = "\n".join(f"<p>{esc(part)}</p>" for part in show["paragraphs"])
        episode = ""
        latest = strip_feed_text(show.get("latestTitle") or "")
        if latest:
            when = f" · {esc(show['dateLabel'])}" if show.get("dateLabel") else ""
            episode = f'''<div class="episode">
            <p class="label">Last episode listed in the official feed</p>
            <p><strong>{esc(latest)}</strong></p>
            <p>Read from the publisher’s RSS on {FETCHED}{when}. Audio is not hosted here.</p>
          </div>'''
        related = []
        for other in related_shows(show, shows):
            related.append(
                f'<li><a href="../{esc(other["slug"])}/"><strong>{esc(other["title"])}</strong><span>{esc(other["publisher"])}</span></a></li>'
            )
        page = head(f"{show['title']} | Where to Listen", f"{show['sentence']} {SHOW_SUFFIX}", 2, "")
        page = page.replace("</head>", json_ld(show) + "\n</head>", 1)
        page += f'''
<main id="content" class="page">
  <article class="wrap">
    <a class="back" href="../../index.html">← Back to the shelf</a>
    <div class="detail">
      {sleeve(show)}
      <div>
        <p class="kicker">{esc(show["category"])}</p>
        <h1 class="show-title">{esc(show["title"])}</h1>
        <dl class="facts">
          {''.join(facts)}
        </dl>
        <div class="description">
          {body}
        </div>
        {episode}
        <div class="actions">
          {('<a class="btn primary" href="' + esc(show["site"]) + '" rel="noopener noreferrer">Official site <span class="ext">External</span></a>') if show.get("site") else ""}
          <a class="btn" href="{esc(show["feed"])}" rel="noopener noreferrer">Official RSS feed <span class="ext">External</span></a>
        </div>
        <p class="fine">Where to Listen does not host this show. Subscribe in your own podcast app with the feed, or listen where the publisher says to listen. Artwork is loaded from the image address in that same feed.</p>
      </div>
    </div>
    <section class="related" aria-labelledby="related-heading">
      <h2 id="related-heading">Related shows</h2>
      <ul>
        {''.join(related)}
      </ul>
    </section>
  </article>
</main>
''' + FOOT.format(prefix="../../", extra="")
        folder = pod / show["slug"]
        folder.mkdir(exist_ok=True)
        (folder / "index.html").write_text(page)

    public = []
    for show in shows:
        public.append({
            "slug": show["slug"],
            "title": show["title"],
            "host": show.get("host") or "",
            "publisher": show["publisher"],
            "category": show["category"],
            "language": show.get("language") or "",
            "blurb": show["sentence"],
            "description": show["description"],
            "site": show.get("site") or "",
            "feed": show["feed"],
            "artwork": show.get("artwork") or "",
            "latestEpisode": show.get("latestTitle") or "",
            "latestEpisodeDateET": show.get("dateLabel") or "",
            "explicit": bool(show.get("explicit")),
        })
    (ROOT / "data/shows.json").write_text(json.dumps(public, indent=2) + "\n")
    persist(shows)
    return public


def persist(shows):
    path = ROOT / "data/catalog.json"
    rows = json.loads(path.read_text())
    by_feed = {show["feed"]: show for show in shows}
    for row in rows:
        show = by_feed.get(row.get("feed") or "")
        if not show:
            continue
        row["slug"] = show["slug"]
        row["site"] = show.get("site") or ""
        row["publisher"] = show["publisher"]
        row["language"] = show.get("language") or ""
        row["languageLabel"] = show.get("languageLabel") or ""
        row["description"] = show["description"]
        if not row.get("handwritten"):
            row["blurb"] = show["sentence"]
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")


def write_credits(shows):
    lines = [
        "# Credits",
        "",
        "Where to Listen is a browse-only mock catalog. It does not host podcast audio.",
        "",
        "## What was not used",
        "",
        "- The Podcast Index API was not called. `PODCASTINDEX_API_KEY` and `PODCASTINDEX_API_SECRET` were not set in the build environment.",
        "- Podcast Index API Terms of Service v1.1, section 5.5, prohibit scraping, building a database from, or keeping permanent copies of content returned by the APIs, and prohibit publicly displaying that API content unless the content owner or the law allows it. See https://github.com/Podcastindex-org/legal/blob/main/TermsOfService.md",
        "- Podcast Index’s public homepage says the core index is available for free, for any use (https://podcastindex.org/). That mission statement is not treated here as permission to store API responses. This site does not copy the Podcast Index database and does not present itself as a Podcast Index product or partner (API terms, section 7.3).",
        "- No episode enclosures, MP3s, or M4A files were downloaded or linked.",
        "- Descriptions are catalog copy edited for this shelf from publisher feed summaries. Full feed HTML is not stored. Show pages do not credit Podcast Index, because those pages were not filled from that API.",
        "",
        "## What was used",
        "",
        f"On {FETCHED}, public top-podcast charts were read only to discover feed URLs. Those chart payloads were not committed. Each publisher RSS was then read for channel title, feed URL, artwork URL (`itunes:image` or channel image), a description, the channel language tag, and one recent episode title and date. Podcast Index was not queried, because no free-plan API credentials were present, and a Podcast Index catalog dump is not in this repo.",
        "",
        "Artwork is hotlinked from the image URL the show’s feed already publishes for podcast apps and directories. Image files are not in this repository. If the image fails to load, the page shows a monogram.",
        "",
        "Attribute the show and its art to the publisher and the feed listed below. This catalog is not affiliated with those shows.",
        "",
        "## Shows",
        "",
        "| Show | Official site | Official feed | Artwork address (hotlinked, not copied) |",
        "| --- | --- | --- | --- |",
    ]
    for show in shows:
        art = show.get("artwork") or "(none — monogram only)"
        lines.append(f"| {show['title']} | {show['site']} | {show['feed']} | {art} |")
    lines += [
        "",
        "## Design",
        "",
        "Type is loaded from Google Fonts: Barlow Condensed, Outfit, and IBM Plex Mono. Those files are not vendored here.",
        "",
        "## Podcast Index, for a later refresh",
        "",
        "If credentials are present, a future refresh can query the Podcast Index API under its current terms and display whatever attribution their docs require. Do not commit API secrets. Do not store a permanent dump of API content if the terms still forbid it. Do not add that credit on a show page unless that page’s data actually came from Podcast Index.",
        "",
    ]
    (ROOT / "CREDITS.md").write_text("\n".join(lines))


def write_notes(count):
    text = f"""# Notes

Working title: **Where to Listen**. The folder and repository use the same name.

## What this is

A static HTML mock of a browse-only podcast shelf: a home grid, one page per show, and an About page. There are {count} shows. Traffic catalog only. No audio hosting and nothing for sale.

## Data rules for this build

- Podcast Index API keys were not in the environment, so the API was not used.
- Podcast Index API terms (section 5.5) do not allow a permanent database of content returned from the API. This site does not contain one.
- Metadata that is on the pages was read from each show’s public RSS on {FETCHED}: title, feed URL, artwork URL, language tag, latest episode title and date.
- Descriptions are catalog copy edited for this shelf. They are not a feed HTML dump and not a Podcast Index dump.
- Outbound links are the official site and the official RSS only. Enclosure URLs were discarded and are not in the HTML.
- Slugs already in the catalog stay frozen. Titles that had collapsed to `show`, `show-N`, `lin`, or `101` use a readable slug derived from the show name.
- For Behind the Bastards, the newest item in the iHeart feed was a sibling show (“It Could Happen Here”). The page uses the newest item that is actually a Behind the Bastards episode.
- Slow Burn was left out. The feed URL associated with that name was serving a different Slate show at the top.

## Design

Modern listening room, not a bookshop and not an arcade. Warm paper in light mode, control-room black with an amber needle and a green on-air lamp in dark mode. A waveform sits in the wordmark. Category chips behave like receiver presets.

## Theme toggle

Every page has a Light / Dark control in the header.

- Inline script in `head` sets `data-theme` before paint from `localStorage` key `wtl-theme`.
- If nothing is stored, the default follows `prefers-color-scheme`.
- Choosing a mode writes `wtl-theme` so the choice sticks. If the visitor never chooses, a later OS change still applies.
- Colors live in CSS variables on `:root` and `html[data-theme="dark"]`.

## SEO

Every HTML page includes `<meta name="robots" content="noindex">` and `<link rel="canonical" href="./">`.
The home title is `{HOME_TITLE}`. Each show title is `{{Show name}} | Where to Listen`.
Show URLs are `podcasts/{{slug}}/` with a trailing slash. Each show page has one `PodcastSeries` JSON-LD block whose `webFeed` is that show’s publisher RSS.

## Rebuild

```bash
python3 tools/fetch_feed_copy.py
python3 tools/build_site.py
```

`data/feed_snapshot.json` is the checked metadata from the RSS reads. `data/feed_copy.json` holds channel language, publisher, and summary text used to write descriptions. `data/editorial.json` holds hosts, categories, official sites, and original blurbs for the first set of shows. The script writes `index.html`, `about.html`, `404.html`, and `podcasts/{{slug}}/index.html`.

## GitHub Pages

Pages serves the repository root through Jekyll. `_config.yml` excludes `NOTES.md`, `README.md`, `CREDITS.md`, `data/`, and `tools/`, so those files stay in the repo and are not part of the published site. There is no `.nojekyll` file, because that would turn the exclude list off.
"""
    (ROOT / "NOTES.md").write_text(text)


def write_readme(count):
    (ROOT / "README.md").write_text(f"""# Where to Listen

A browse-only shelf of {count} well-known podcasts. Find a show, then leave for the publisher’s site or RSS feed.

This site does not host episode audio, does not sell anything, and is not a podcast app.

- [About this catalog](about.html)
- [Credits and sources](CREDITS.md)
- [Build notes](NOTES.md)
""")


def write_config():
    (ROOT / "_config.yml").write_text("""title: Where to Listen
exclude:
  - NOTES.md
  - README.md
  - CREDITS.md
  - data
  - tools
  - .github
  - Gemfile
  - Gemfile.lock
  - vendor
  - node_modules
""")


def visible_text(page):
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", page, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"https?://\S+", " ", text)
    return text


def audit(shows):
    problems = []
    pages = [ROOT / "index.html", ROOT / "about.html", ROOT / "404.html"]
    pages.extend(sorted((ROOT / "podcasts").glob("*/index.html")))
    if (ROOT / "shows").exists():
        problems.append("shows/ directory still exists")
    if (ROOT / ".nojekyll").exists():
        problems.append(".nojekyll still exists")
    slugs = {show["slug"] for show in shows}
    if len(pages) != len(shows) + 3:
        problems.append(f"page count {len(pages)} expected {len(shows) + 3}")
    home = (ROOT / "index.html").read_text()
    if f"<title>{HOME_TITLE}</title>" not in home:
        problems.append("home title mismatch")
    if 'content="noindex"' not in home or 'rel="canonical" href="./"' not in home:
        problems.append("home robots/canonical")
    if HOME_DESC not in home:
        problems.append("home meta description")
    if 'href="shows/' in home or "shows/" in re.sub(r"<[^>]+>", " ", home):
        # Artwork URLs may contain /shows/. Only flag catalog links.
        pass
    if 'href="shows/' in home:
        problems.append("home still links to shows/")
    if home.count('href="podcasts/') < len(shows):
        problems.append("home missing podcast links")
    banned_schema = ("PodcastEpisode", "Product", "Offer", "Review", "aggregateRating")
    stub_hits = 0
    for show in shows:
        path = ROOT / "podcasts" / show["slug"] / "index.html"
        if not path.exists():
            problems.append(f"missing {show['slug']}")
            continue
        page = path.read_text()
        title = f"{show['title']} | Where to Listen"
        if f"<title>{html.escape(title)}</title>" not in page and f"<title>{title}</title>" not in page:
            problems.append(f"title {show['slug']}")
        if page.count('content="noindex"') != 1 or 'rel="canonical" href="./"' not in page:
            problems.append(f"robots {show['slug']}")
        if SHOW_SUFFIX not in page:
            problems.append(f"meta suffix {show['slug']}")
        if page.count('"@type": "PodcastSeries"') != 1 and page.count('"@type":"PodcastSeries"') != 1:
            problems.append(f"jsonld {show['slug']}")
        if '"webFeed"' not in page:
            problems.append(f"webFeed {show['slug']}")
        for kind in banned_schema:
            if f'"@type": "{kind}"' in page or f'"@type":"{kind}"' in page:
                problems.append(f"schema {kind} {show['slug']}")
        if "]]>" in page or "acast.com/privacy" in page.lower():
            problems.append(f"garbage {show['slug']}")
        if STUB_RE.search(visible_text(page)):
            stub_hits += 1
        if 'class="related"' not in page or page.count('href="../') < 4:
            problems.append(f"related {show['slug']}")
        episode = page.split('class="episode"', 1)[-1].split("</div>", 1)[0] if 'class="episode"' in page else ""
        if "<a " in episode:
            problems.append(f"episode link {show['slug']}")
        visible = visible_text(page)
        visible = re.sub(r"the dale jr\.?\s+download", "", visible, flags=re.I)
        if re.search(r"download|torrent", visible, flags=re.I):
            problems.append(f"banned word {show['slug']}")
        if "atulit" in page.lower():
            problems.append(f"atulit {show['slug']}")
        if "·" in re.search(r"<title>.*?</title>", page).group(0):
            problems.append(f"title dot {show['slug']}")
        if show["slug"] not in slugs:
            problems.append(f"slug {show['slug']}")
    for name in ("index.html", "about.html", "404.html"):
        page = (ROOT / name).read_text()
        if 'content="noindex"' not in page or 'rel="canonical" href="./"' not in page:
            problems.append(f"public head {name}")
        if "atulit" in page.lower():
            problems.append(f"atulit {name}")
        visible = visible_text(page)
        visible = re.sub(r"the dale jr\.?\s+download", "", visible, flags=re.I)
        if re.search(r"download|torrent", visible, flags=re.I):
            problems.append(f"banned word {name}")
    if stub_hits:
        problems.append(f"stubs {stub_hits}")
    if problems:
        print("AUDIT FAIL", len(problems))
        for item in problems[:40]:
            print(" -", item)
        raise SystemExit(1)
    print(f"audit ok {len(shows)} shows")


def main():
    shows = load()
    write_config()
    public = write_pages(shows)
    write_credits(public)
    write_notes(len(public))
    write_readme(len(public))
    audit(shows)
    print(f"built {len(public)} shows")


if __name__ == "__main__":
    main()
