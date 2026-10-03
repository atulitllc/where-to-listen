#!/usr/bin/env python3
"""Generate the static Where to Listen catalog. Does not download audio."""

import html
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
ET = ZoneInfo("America/New_York")
FETCHED = "Oct 3, 2026"
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


def esc(value):
    return html.escape(value or "", quote=True)


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


def head(title, depth, current):
    prefix = "../" if depth else ""
    nav_home = ' aria-current="page"' if current == "home" else ""
    nav_about = ' aria-current="page"' if current == "about" else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
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
    <p>Show titles, feeds, and artwork addresses come from each publisher’s public RSS. Short descriptions on this site are original paraphrases. See the About page.</p>
  </div>
</footer>
<script src="{prefix}js/theme.js"></script>
{extra}
</body>
</html>
"""


def sleeve(show, large=False):
    art = show.get("artwork") or ""
    img = ""
    if art:
        img = f'<img src="{esc(art)}" alt="" referrerpolicy="no-referrer" onerror="this.remove()">'
    return f'''<div class="sleeve" style="--hue:{hue(show["slug"])}">
      {img}
      <span class="initials" aria-hidden="true">{esc(initials(show["title"]))}</span>
    </div>'''


def load():
    catalog_path = ROOT / "data/catalog.json"
    if catalog_path.exists():
        rows = json.loads(catalog_path.read_text())
    else:
        editorial = {row["slug"]: row for row in json.loads((ROOT / "data/editorial.json").read_text())}
        snapshot = json.loads((ROOT / "data/feed_snapshot.json").read_text())
        rows = []
        for row in snapshot:
            rows.append({**row, **editorial[row["slug"]]})
    shows = []
    for row in rows:
        show = dict(row)
        show["dateLabel"] = fmt_date(show.get("latestDate") or "")
        show["site"] = show.get("site") or ""
        shows.append(show)
    shows.sort(key=lambda s: s["title"].lower())
    return shows


def write_pages(shows):
    cards = []
    for show in shows:
        hay = " ".join([show["title"], show["host"], show["category"], show["blurb"]]).lower()
        flag = '<span class="flag">Explicit</span>' if show.get("explicit") else ""
        cards.append(f'''<a class="card" href="shows/{esc(show["slug"])}.html" data-cat="{esc(show["category"])}" data-hay="{esc(hay)}">
          {sleeve(show)}
          <div class="card-body">
            <span class="cat">{esc(show["category"])}</span>
            <h2>{esc(show["title"])}{flag}</h2>
            <p class="host">{esc(show["host"])}</p>
          </div>
        </a>''')
    present = {s["category"] for s in shows}
    chips = ['<button type="button" class="chip" data-filter="all" aria-pressed="true">All</button>']
    for cat in CATS:
        if cat in present:
            chips.append(f'<button type="button" class="chip" data-filter="{esc(cat)}" aria-pressed="false">{esc(cat)}</button>')
    for cat in sorted(present - set(CATS)):
        chips.append(f'<button type="button" class="chip" data-filter="{esc(cat)}" aria-pressed="false">{esc(cat)}</button>')
    home = head("Where to Listen", 0, "home") + f'''
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

    about = head("About · Where to Listen", 0, "about") + f'''
<main id="content" class="page">
  <article class="wrap prose">
    <p class="kicker">Program notes</p>
    <h1>We point. We don’t host.</h1>
    <p>Where to Listen is a static shelf of popular podcasts. It is a catalog for browsing, in the same spirit as a guide that tells you where a film is playing or where a game can be found. It is not a listening app.</p>
    <h2>What you will not find here</h2>
    <p>No episode audio, no embedded players, no copied MP3s, and no pirate mirrors. There is nothing for sale. Each show page links out to the publisher’s own website and to that show’s public RSS feed, labeled as external.</p>
    <p>The line called “last episode listed in the official feed” is a title and a date read from the publisher’s RSS. It is not a file, and it is not a promise that the feed still looks the same tomorrow.</p>
    <h2>Where the facts come from</h2>
    <p>Podcast Index (<a href="https://podcastindex.org/">podcastindex.org</a>) is the open directory this shelf is built around. Their API is free, and their terms (section 5.5) say not to keep a permanent copy of content the API returns. No API key was available for this build, so the API was not called and no Podcast Index response is stored here. This is not a Podcast Index product and not a partner site.</p>
    <p>On {FETCHED} the shelf was filled from publisher RSS feeds. Public podcast charts were used only to find those feed addresses, then discarded. Each page keeps the show title, the feed URL, the artwork address already published in that feed, a short description, and the title of the latest episode. Hand-written notes are used where we had them. Otherwise the description is the opening of the show’s own feed summary, trimmed so the page does not dump feed HTML.</p>
    <p>Artwork is hotlinked from that feed address. The image bytes are not copied into this site. If a publisher would rather not be hotlinked, the picture should be removed and the monogram left in its place. Feeds are linked so you can subscribe in your own app.</p>
    <h2>A note on Podcast Index</h2>
    <p>Podcast Index (<a href="https://podcastindex.org/">podcastindex.org</a>) is an open podcast directory with a developer API. This catalog is not a Podcast Index product, is not endorsed by them, and does not display their logo as a partner mark. If API credentials are added later, a refresh should follow their current terms, including any required attribution, and should not keep a permanent copy of API content beyond what those terms allow.</p>
    <h2>Indexing</h2>
    <p>Every page on this demo sends a <code>noindex</code> robots meta tag and a relative canonical URL of <code>./</code>.</p>
  </article>
</main>
''' + FOOT.format(prefix="", extra="")
    (ROOT / "about.html").write_text(about)

    show_dir = ROOT / "shows"
    show_dir.mkdir(exist_ok=True)
    keep = {f"{show['slug']}.html" for show in shows}
    for stale in show_dir.glob("*.html"):
        if stale.name not in keep:
            stale.unlink()
    for show in shows:
        flag = ' <span class="flag">Explicit</span>' if show.get("explicit") else ""
        episode = ""
        if show.get("latestTitle"):
            when = f" · {esc(show['dateLabel'])}" if show.get("dateLabel") else ""
            episode = f'''<div class="episode">
            <p class="label">Last episode listed in the official feed</p>
            <p><strong>{esc(show["latestTitle"])}</strong></p>
            <p>Read from the publisher’s RSS on {FETCHED}{when}. Audio is not hosted here.</p>
          </div>'''
        page = head(f"{show['title']} · Where to Listen", 1, "") + f'''
<main id="content" class="page">
  <article class="wrap">
    <a class="back" href="../index.html">← Back to the shelf</a>
    <div class="detail">
      {sleeve(show)}
      <div>
        <p class="kicker">{esc(show["category"])}</p>
        <h1 class="show-title">{esc(show["title"])}</h1>
        <p class="host-line">{esc(show["host"])}{flag}</p>
        <p class="blurb">{esc(show["blurb"])}</p>
        {episode}
        <div class="actions">
          {('<a class="btn primary" href="' + esc(show["site"]) + '" rel="noopener noreferrer">Official site <span class="ext">External</span></a>') if show.get("site") else ""}
          <a class="btn" href="{esc(show["feed"])}" rel="noopener noreferrer">Official RSS feed <span class="ext">External</span></a>
        </div>
        <p class="fine">Where to Listen does not host this show. Subscribe in your own podcast app with the feed, or listen where the publisher says to listen. Artwork is loaded from the image address in that same feed.</p>
      </div>
    </div>
  </article>
</main>
''' + FOOT.format(prefix="../", extra="")
        (show_dir / f"{show['slug']}.html").write_text(page)

    public = []
    for show in shows:
        public.append({
            "slug": show["slug"],
            "title": show["title"],
            "host": show["host"],
            "category": show["category"],
            "blurb": show["blurb"],
            "site": show["site"],
            "feed": show["feed"],
            "artwork": show.get("artwork") or "",
            "latestEpisode": show.get("latestTitle") or "",
            "latestEpisodeDateET": show.get("dateLabel") or "",
            "explicit": bool(show.get("explicit")),
        })
    (ROOT / "data/shows.json").write_text(json.dumps(public, indent=2) + "\n")
    return public


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
        "- A core set of blurbs was written for this catalog. Additional descriptions are the opening of each show’s own feed summary, trimmed. Full feed HTML is not stored.",
        "",
        "## What was used",
        "",
        f"On {FETCHED}, public top-podcast charts were read only to discover feed URLs. Those chart payloads were not committed. Each publisher RSS was then read for channel title, feed URL, artwork URL (`itunes:image` or channel image), a shortened description, and one recent episode title and date. Podcast Index was not queried, because no free-plan API credentials were present, and a Podcast Index catalog dump is not in this repo.",
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
        "If credentials are present, a future refresh can query the Podcast Index API under its current terms and display whatever attribution their docs require. Do not commit API secrets. Do not store a permanent dump of API content if the terms still forbid it.",
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
- Metadata that is on the pages was read from each show’s public RSS on {FETCHED}: title, feed URL, artwork URL, latest episode title and date.
- A core set of blurbs was written for the shelf. The rest are trimmed openings of each show’s own feed summary, not a feed HTML dump and not a Podcast Index dump.
- Outbound links are the official site and the official RSS only. Enclosure URLs were discarded and are not in `data/shows.json` or the HTML.
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

## Rebuild

```bash
python3 tools/build_site.py
```

`data/feed_snapshot.json` is the checked metadata from the RSS reads. `data/editorial.json` holds hosts, categories, official sites, and original blurbs. The script writes `index.html`, `about.html`, `shows/*.html`, and `data/shows.json`.

## GitHub Pages

The site is plain static files at the repository root, with `.nojekyll` so Pages will not run Jekyll.
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


def main():
    shows = load()
    missing_cats = sorted({s["category"] for s in shows} - set(CATS))
    if missing_cats:
        print("extra categories", missing_cats)
    public = write_pages(shows)
    write_credits(public)
    write_notes(len(public))
    write_readme(len(public))
    (ROOT / ".nojekyll").write_text("")
    print(f"built {len(public)} shows")


if __name__ == "__main__":
    main()
