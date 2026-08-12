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

### Free Cinema — the Internet Archive

Public-domain films are queried live from `archive.org/advancedsearch.php` across six
collections (`feature_films`, `SciFi_Horror`, `animationandcartoons`, `classic_tv`,
`silent_films`, `short_films`). A title is stored as `archive:<identifier>` and only
resolved to a real file URL when played, via `archive.org/metadata/<identifier>`, picking
the most browser-friendly derivative available.

archive.org sends `Access-Control-Allow-Origin: *` and supports HTTP range requests, so
these files stream natively in `<video>` with no proxy involved.

This library is **carried unfiltered and labelled 18+** — the public-domain collections
include vintage adult and exploitation titles alongside classic cinema.

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
