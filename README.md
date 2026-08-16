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

Files are grouped by base name so an `.mkv` and its archive-derived `.mp4` count as one
title, and the browser-playable file wins. Titles with no playable derivative are dropped
rather than listed as dead clicks: browsers cannot play Matroska.

Three of the box sets come from playlists in the site's own repos that the old build never
used — The Inbetweeners and Fawlty Towers (`Comedy`), Mayday (`King`).

### Free Cinema — public-domain collections

Queried live from `archive.org/advancedsearch.php` across thirteen collections
(`feature_films`, `SciFi_Horror`, `animationandcartoons`, `classic_tv`, `silent_films`,
`short_films`, `prelinger`, `television`, and others), paged in the sidebar. A title is
stored as `archive:<identifier>` and only resolved to a file URL when played.

This library is **carried unfiltered and labelled 18+** — the public-domain collections
include vintage adult and exploitation titles alongside classic cinema.

### URL scheme

| Form | Meaning |
| --- | --- |
| `archive:<identifier>` | pick the best video in the item (Free Cinema) |
| `archive:<identifier>\|<file>` | that exact file (vaults) |

### Live TV — iptv-org

Country, category and per-network playlists come from
[iptv-org/iptv](https://github.com/iptv-org/iptv). The free ad-supported networks
(Pluto TV, Samsung TV Plus, Tubi, Xumo, Plex, Stirr, Roku) are the most reliable sources
in the app — spot checks put them at ~100% uptime, versus roughly 50–80% for the
general country and category lists, which are community-maintained and go dark often.

> Per-network playlists live under `streams/` in the iptv-org **repo**, not under
> `/networks/` on their GitHub Pages site. That path was removed upstream and is what
> previously broke the Pluto TV and Samsung TV Plus sources.

### Series & Shows

M3U playlists hosted in sibling GitHub repositories, grouped into shows and sorted by
season/episode.

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
