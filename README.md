# Streams Sphere

A single-page streaming front end: free public-domain cinema, live IPTV channels, and
instant-play arcade games, running entirely in the browser with no backend.

**Live:** https://streamssphere.tv/

## Files

| File | Purpose |
| --- | --- |
| `Index.html` | The whole application — markup, styles and logic in one file. |
| `manifest.json` | PWA manifest (installable app, icons, theme). |
| `sw.js` | Service worker. Network-first for the app shell, never caches media or playlists. |
| `robots.txt`, `sitemap.xml` | Search engine directives. |
| `ads.txt` | Google AdSense seller declaration. |

## Where the content comes from

Nothing is hosted here. Every title is fetched at runtime from a third-party source.

archive.org sends `Access-Control-Allow-Origin: *` and supports HTTP range requests, so
its files stream natively in `<video>` with no proxy involved. All archive.org calls go
through `archiveFetch()`, which retries — their CDN nodes return intermittent 5xx often
enough that a single attempt leaves a healthy collection looking empty.

### My Movies — the site's own playlist

`ab19902020/Comedy/Movies.m3u`, grouped A–Z (it carries no group-title tags).

434 of its 766 entries no longer resolve: 326 pointed at the archive item
`movies_202211`, which the Internet Archive has **darkened**, and the rest at items since
deleted or renamed. Those 78 identifiers are listed in `DEAD_ARCHIVE_ITEMS` and filtered
out, leaving ~332 titles that actually play. If one comes back, delete its identifier
from that list.

### Movie Vault / TV Box Sets — whole archive items

Some archive.org items are single uploads holding hundreds of films or a complete series.
Rather than hand-listing files in an M3U, these are enumerated live from
`archive.org/metadata/<identifier>`, so anything the uploader adds appears automatically —
the Mayday playlist listed 109 episodes where the item holds 203.

**28 film vaults (~2,240 titles)** and **70 box sets (~19,600 episodes)**, each verified
live with a browser-playable count before being added.

Found by sweeping archive.org's search API for large multi-title items. The raw sweep
returned far more than shipped here; deliberately excluded were game-capture dumps
mislabelled as films, hentai and adult production-house items, YouTube-personality
archives (several built around hateful or violent creators), religious proselytising
channels, trailer/promo reels, and unlabelled bulk dumps. Curation is the point — the
search API alone will happily hand back 4,400 Counter-Strike clips as a "movie
collection".

Files are grouped by base name so an `.mkv` and its archive-derived `.mp4` count as one
title, and the browser-playable file wins. Titles with no playable derivative are dropped
rather than listed as dead clicks: browsers cannot play Matroska.

Three of the box sets come from playlists in the site's own repos that the old build never
used — The Inbetweeners and Fawlty Towers (`Comedy`), Mayday (`King`).

### Free Cinema — public-domain collections

Queried live from `archive.org/advancedsearch.php` across eighteen collections
(`feature_films`, `moviesandfilms`, `SciFi_Horror`, `anime`, `animationandcartoons`,
`classic_tv`, `silent_films`, `short_films`, `prelinger`, `television`, `nasa`, `avgeeks`,
`computerchronicles` and others), paged in the sidebar. A title is stored as
`archive:<identifier>` and only resolved to a file URL when played.

Collection sizes were checked against the search API before being listed —
`moviesandfilms` alone is 110,609 items and `anime` is 37,632. `opensource_movies` (2.5M)
and `additional_collections_video` (1.9M) are deliberately left out: they are unfiltered
upload dumps, and a browse surface full of phone footage is worse than a smaller shelf of
actual films.

This library is **carried unfiltered and labelled 18+** — the public-domain collections
include vintage adult and exploitation titles alongside classic cinema.

### URL scheme

| Form | Meaning |
| --- | --- |
| `archive:<identifier>` | pick the best video in the item (Free Cinema) |
| `archive:<identifier>\|<file>` | that exact file (vaults) |

### Live TV

~78 verified playlists from [iptv-org/iptv](https://github.com/iptv-org/iptv) and
[Free-TV/IPTV](https://github.com/Free-TV/IPTV), reached through the **Live TV** hub
rather than as top-level pills — 78 pills in a scroll strip is not navigable, and
country / genre / language / network is how people actually look for a channel.

| Section | Contents |
| --- | --- |
| By Country | every country iptv-org carries, grouped into five regions |
| Free TV Networks | Pluto (12 countries), Samsung TV Plus (13), Rakuten TV (7), Tubi, Xumo, Plex, Stirr, Roku, KlowdTV, DistroTV, Vizio, Amagi |
| By Genre | 30 categories |
| By Language | 15 languages |
| Everything | full index, plus the Free-TV community aggregators |

Every network playlist above was probed before being listed — 726 candidate
`<country>_<network>` combinations against the iptv-org repo, keeping the ones that return
a real playlist with a non-zero channel count.

### Free sports and free news

`collectChannels()` merges 21 network playlists into one line-up and `SPORT_MATCH` /
`NEWS_MATCH` filter it, giving a **79-channel sports guide** and a comparable news guide,
grouped by which network carries each channel. Reachable from the tiles at the front of the
home shelf and from the bars at the top of Live TV.

It is all official, ad-supported and legal: NFL Channel, MLB, NBA FAST, NHL Network, beIN
SPORTS XTRA, FOX Sports, NBC Sports NOW, CBS Sports HQ, fubo Sports, UFC, DAZN Ringside and
Combat, Tennis Channel, RugbyPass TV, FIFA+, GolfPass, NASCAR, MODUS Darts, Pluto Snooker,
Cricket Gold, Fuel TV, SportsGrid, Women's Sports Network.

**Sky Sports, TNT Sports and MUTV are deliberately absent.** They are subscription
channels with no free feed in any territory, so every "free" copy circulating in IPTV
indexes is an unauthorised restream — not something to build a front door to. They would
not work here regardless: those entries are pinned to a spoofed VLC user-agent, and a
browser cannot send a custom `User-Agent` from JavaScript.

The matching patterns have two halves. The first anchors at a word start but not a word
end, so `GolfPass`, `PokerGO`, `SportsGrid` and `Newsmax` are caught — station names glue
words together constantly — while `Transport` still fails, because there is no word break
before its "sport". The second half needs both boundaries, for words that only mean sport
in isolation: a loose `bein` would take *Being Human*, a loose `fight` would take
*Fighting Fit*.

The ad-supported networks are by far the most reliable — spot checks put them near 100%
uptime, against roughly 50–80% for the community country and category lists.

> Per-network playlists live under `streams/` in the iptv-org **repo**, not under
> `/networks/` on their GitHub Pages site. That path was removed upstream and is what
> previously broke the Pluto TV and Samsung TV Plus sources.

**Freely (UK) cannot be added.** It has no public playlist: its streams are DRM-protected
and only delivered through the Freely app and certified TVs, so there is nothing a browser
can embed. The channels its line-up covers (BBC One/Two/Four/News, ITV, Channel 4/5) are
already reachable through the United Kingdom source — though many carry a `[Geo-blocked]`
tag and will only play from a UK connection.

### Series & Shows

M3U playlists hosted in sibling GitHub repositories, grouped into shows and sorted by
season/episode.

## The browse surface

Below the player the app is a browse surface rather than a single list:

- **Network shelf** — Pluto (US/UK/CA/DE), Samsung TV+ (US/UK), Plex, Tubi, Xumo, Stirr,
  Roku, Rakuten, DistroTV, KlowdTV and Vizio as tiles, always one click from home. These
  were briefly demoted into the Live TV hub and that was a mistake: they are the most
  reliable content in the app and the brands people recognise, so they stay on the surface.
- **Poster rails** — horizontally scrolling rows built by `renderHomeRows()`: live now,
  your movie library, film vaults, box sets, free cinema, sport, news, kids.
- **Detail sheet** — every VOD poster opens a sheet with backdrop, synopsis, rating, year
  and genre before playing. Live channels skip it and play immediately, because a live
  channel has no synopsis to show.
- **Browse-all grid** (`openGrid`) — the whole catalogue, with genre filter chips, a sort
  control (A–Z / rating / newest / oldest) and a live count. Reached from the
  **Browse all films** / **Browse all shows** bar at the top of Movies and TV Shows, and
  from any genre shelf's *Browse all*. Rails only ever show a sample, so without this
  entry point most of the library is unreachable.
- **Channel wall** (`renderChannelWall`) — see below.

### The browse-all grid

Genre and rating only exist for titles TMDB has already answered for, so the chip row is
built from what is known and grows as enrichment continues — the filter never hides a
title for lacking metadata, and unknown genres stay visible under *All*. Twenty waves of
sixty lookups covers the whole catalogue; every lookup is memoised, so it is a first-visit
cost.

`dedupeTitles()` collapses the same film appearing in more than one collection. Uploaders
overlap heavily — Alita, Birds of Prey and Batman: The Long Halloween each sat in two
vaults — and deduping by URL cannot catch it, because the two copies are genuinely
different files. The key is the TMDB id where known (which also keeps remakes apart), and
normalised name + year before a title has been matched.

### The channel wall

**There are no now/next programme times, and that is not an oversight.** No free,
CORS-accessible EPG exists for these channels:

| Source | Why not |
| --- | --- |
| iptv-org EPG | a grabber you install and run yourself, not a hosted feed |
| Pluto's own API | returns 431 channels with empty timelines; CORS restricted to `pluto.tv` |
| epg.pw | CORS is open but it returned zero programmes and every bulk endpoint 404s |

Inventing schedule times would be worse than omitting them, so the wall gives what a guide
gives you minus the clock: numbered rows, station identity, a category filter over the
whole line-up, and one click to play. Network tiles and the Live TV genre rails both open
it.

### TMDB

Playlist entries carry only a filename, so artwork and metadata come from The Movie
Database. Matching runs in tiers and stops at the first result that passes a similarity
check:

1. cleaned title + filename year
2. same title, no year (filename years are often a different cut or region)
3. title with a trailing subtitle dropped (`Film - Special Edition`, `Film: Subtitle`)
4. the first four words

`tmdbQueryFrom()` strips release noise, bracketed tags, disc/volume markers, trailing
release-group suffixes and leftover empty parentheses. `extractYear()` also catches a year
glued to the title (`Mr Beans Holiday2007`).

**`titlesLookAlike()` is the important part.** TMDB answers almost any query, so without a
guard a short title takes something unrelated — `Grave` came back as *The Mechanical
Grave*. A wrong poster is worse than no poster. The check folds accents (`Pokémon` =
`Pokemon`), normalises roman numerals (`Rocky 5` = `Rocky V`), ignores word-break
differences (`Mocking Bird` = `Mockingbird`), and requires a near-exact match for anything
under nine characters.

Measured against 240 real vault filenames: **100% matched, 100% with posters**, no false
matches across the guard's test cases.

Lookups are memoised in `tmdbMemCache`, persisted to localStorage, and queued 8-at-a-time.
Cards enrich when they scroll into view, but each rail also eagerly fills its first ten —
cards sitting off the right-hand edge of a horizontal rail never intersect the viewport, so
the observer alone left every rail looking half-finished until it was scrolled sideways.

### Live channel logos and categories

The per-network playlists under `streams/` carry `tvg-id` but no `tvg-logo` and no
`group-title`, so those channels would render as blank tiles with every one of them filed
under "Other". `ensureLiveLogoMap()` reads the US, UK, Canada and Germany country
playlists once (~800 KB, which do carry both for ~98% of entries) and builds an
id → { logo, category } map that back-fills the network lists — that is what puts Series /
Entertainment / Movies / News / Sport counts on the channel wall's filter chips. Four
countries rather than two because Pluto and Samsung ship separate German and Canadian
line-ups whose ids only appear in their own country list.

iptv-org also publishes `logos.json`, but that is 7 MB against 800 KB here, and it carries
no categories at all.

## Playback

| Kind | Handling |
| --- | --- |
| HLS (`.m3u8`) | `hls.js`, pinned to a known-good version, with quality selection |
| Progressive (`.mp4` etc.) | Native `<video>` |
| YouTube | IFrame Player API |
| WHEP / WebRTC | `RTCPeerConnection` with a live latency readout |
| Games | Sandboxed `<iframe>` |

Failures retry with backoff, then offer a proxy hop, an external open, and a VLC handoff.

## Conventions worth keeping

- **Never interpolate playlist data into `innerHTML` raw.** Titles, group names and logo
  URLs come from third-party M3U files and from any URL a visitor pastes in. Everything
  goes through `escapeHtml()`.
- **Never auto-open affiliate or ad windows on page clicks.** Traffic to affiliate links
  must come from a deliberate click on a visible link.
- **Don't cache media or playlists in the service worker.** They are large and they expire.
- **Validate that a fetched playlist is actually a playlist.** A moved source returns a
  200 HTML error page, which otherwise renders as a silent, empty list.
- **Configure Tailwind *after* the CDN script tag.** Setting `tailwind = { config: … }`
  beforehand is overwritten on load, silently falling back to `darkMode: 'media'` — every
  `dark:` utility then follows the visitor's OS instead of the site's own toggle, which
  put near-white text on white panels in day mode.
- **Retry archive.org.** Its nodes 5xx intermittently; one failed call is not a dead item.
- **Never accept a TMDB result without checking the titles match.** The API answers almost
  anything; an unrelated poster is worse than a placeholder.
- **Horizontal rails need eager loading as well as an observer.** Off-screen-right cards
  never intersect the viewport.
- **The scroller is `#main-view`, not the document.** `html` and `body` are
  `overflow: hidden`, so `scrollIntoView()` silently does nothing — scroll positions have
  to be computed against `#main-view` and set on it.
- **Re-assert the scroll position across a repaint.** Emptying a list collapses the page
  height, the browser clamps the scroll offset to what still fits, and the reader is thrown
  back to the top every time they touch a filter chip. `keepScrollAcrossRepaint()` holds
  the position for a few frames while the replacement content streams in; the same trick in
  reverse (`scrollBrowseIntoView()`) is needed to scroll *to* a list that has not been
  filled yet.
- **Never let a slow fetch paint over a section the visitor has moved on to.** Anything
  that awaits before rendering captures `sectionToken` first and re-checks it after —
  otherwise a catalogue that takes twenty seconds drops on top of whatever is now on
  screen.
- **Don't invent data the sources don't have.** There is no free EPG feed for these
  channels; a guide with plausible-looking made-up times would be worse than no times.
