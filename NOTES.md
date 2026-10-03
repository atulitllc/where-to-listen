# Notes

Working title: **Where to Listen**. The folder and repository use the same name.

## What this is

A static HTML mock of a browse-only podcast shelf: a home grid, one page per show, and an About page. There are 77 shows. Traffic catalog only. No audio hosting and nothing for sale.

## Data rules for this build

- Podcast Index API keys were not in the environment, so the API was not used.
- Podcast Index API terms (section 5.5) do not allow a permanent database of content returned from the API. This site does not contain one.
- Metadata that is on the pages was read from each show’s public RSS on Oct 3, 2026: title, feed URL, artwork URL, latest episode title and date.
- Blurbs are original one-sentence paraphrases.
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
