# Notes

Working title: **Where to Listen**. The folder and repository use the same name.

## What this is

A static HTML mock of a browse-only podcast shelf: a home grid, one page per show, and an About page. There are 1272 shows. Traffic catalog only. No audio hosting and nothing for sale.

## Data rules for this build

- Podcast Index API keys were not in the environment, so the API was not used.
- Podcast Index API terms (section 5.5) do not allow a permanent database of content returned from the API. This site does not contain one.
- Metadata that is on the pages was read from each show’s public RSS on Oct 3, 2026: title, feed URL, artwork URL, language tag, latest episode title and date.
- Descriptions are catalog copy edited for this shelf. They are not a feed HTML dump and not a Podcast Index dump.
- Outbound links are the official site and the official RSS only. Enclosure URLs were discarded and are not in the HTML.
- Slugs already in the catalog stay frozen. Titles that had collapsed to `show`, `show-N`, `lin`, or `101` use a readable slug derived from the show name.
- For Behind the Bastards, the newest item in the iHeart feed was a sibling show (“It Could Happen Here”). The page uses the newest item that is actually a Behind the Bastards episode.
- Slow Burn was left out. The feed URL associated with that name was serving a different Slate show at the top. Checked again on Oct 4, 2026: that feed was still another Slate show.
- On Oct 4, 2026, 78 narrative series were added from each publisher’s own RSS. New show pages use a multi-paragraph catalog essay. Flagship pages that were still a sentence or two use the same kind of essay. Other pages use sentences already in the publisher summary, packed into as many as five paragraphs when the summary is long enough.
- The build fails when two non-featured descriptions match after the show title is removed. Handwritten flagship notes are the featured set and are left as stored.

## Design

Modern listening room, not a bookshop and not an arcade. Warm paper in light mode, control-room black with an amber needle and a green on-air lamp in dark mode. The header wordmark reads findthispodcast. Page titles still say Where to Listen. The home page is a short hero plus curated shelves: Top Listen and a few popular categories, each with a See all link. Category chips sit under the search box. Full lists live on category pages, which use numbered pages when a category is longer than 48 shows. There is no numbered `page/2` dump on the home. The public host is https://findthispodcast.com. HTTPS redirects sit in front of Pages.

## Theme toggle

Every page has a Light / Dark control in the header.

- Inline script in `head` sets `data-theme` before paint from `localStorage` key `wtl-theme`.
- If nothing is stored, the default follows `prefers-color-scheme`.
- Choosing a mode writes `wtl-theme` so the choice sticks. If the visitor never chooses, a later OS change still applies.
- Colors live in CSS variables on `:root` and `html[data-theme="dark"]`.

## SEO

No HTML page sends a sitewide `noindex`. Every page includes `<link rel="canonical">` and `<meta property="og:url">`. Those URLs are absolute `https://findthispodcast.com` addresses with the trailing slash that page already uses. Home, including `/index.html`, uses `https://findthispodcast.com/`. A show page uses `https://findthispodcast.com/podcasts/{slug}/`. Generators read `SITE_ORIGIN`. Nothing points at github.io or www.
`sitemap.xml` lists indexable URLs only: the home page, the about page (`/about/`), each category hub (`/categories/{slug}/`, not numbered `page/n` lists), and each podcast show page. Every `<loc>` is `https://findthispodcast.com/...`. `robots.txt` names it with `Sitemap: https://findthispodcast.com/sitemap.xml`.
Each page has a `WebSite` node whose `url` is `https://findthispodcast.com/` and a `WebPage` node whose `url` is that page. A show page also has one `PodcastSeries` node whose `url` is the absolute show page and whose `webFeed` is that show’s publisher RSS.
The home title is `Podcast catalog | Where to Listen`. Each show title is `{Show name} | Where to Listen`.
Show URLs are `podcasts/{slug}/` with a trailing slash.

## Rebuild

```bash
python3 tools/fetch_feed_copy.py
python3 tools/build_site.py
```

`data/feed_snapshot.json` is the checked metadata from the RSS reads. `data/feed_copy.json` holds channel language, publisher, and summary text used to write descriptions. `data/editorial.json` holds hosts, categories, official sites, and original blurbs for the first set of shows. The script writes `index.html`, `about.html`, `about/index.html`, `404.html`, `categories/{slug}/index.html`, `categories/{slug}/page/{n}/index.html` when a category needs another page, `podcasts/{slug}/index.html`, `sitemap.xml`, and `robots.txt`.

## GitHub Pages

Pages serves the repository root through Jekyll. `_config.yml` excludes `NOTES.md`, `README.md`, `CREDITS.md`, `data/`, and `tools/`, so those files stay in the repo and are not part of the published site. There is no `.nojekyll` file, because that would turn the exclude list off.
