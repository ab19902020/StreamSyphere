# Open library expansion

The September 2026 snapshot adds 219 films and shorts, 18 publisher series with 2,167 unique episodes, and six official live players. These are additional source-backed records; totals are not a claim of unique additions across every legacy playlist.

| Source | Included | Basis and credits |
| --- | --- | --- |
| Blender Studio | 16 open movies and shorts | Publisher reuse policy; official embedded players; individual film credits |
| Internet Archive | 52 classic cinema records | Explicit item-level public-domain or approved Creative Commons declaration |
| Prelinger Archives | 40 historical films | Explicit item-level public-domain or approved Creative Commons declaration |
| Wikimedia Commons | 111 historic films | File-level licence and creator metadata |
| Jupiter Broadcasting | 14 technology series, 1,583 unique episodes | Publisher's CC BY-SA 4.0 statement |
| NASA | Four science series, 584 episodes | NASA media usage guidelines; third-party-rights and promotional-item filters |
| Official live players | France 24 in four languages, Al Jazeera Arabic, Jupiter Broadcasting | Broadcaster YouTube embeds or publisher-licensed stream |

## Viewing

Open **Open library** in the desktop sidebar or **A bigger world of stories** on Home. Filter films, series or live channels by publisher and search titles, descriptions or creators. New records also appear in Movies, TV Shows, Home rails and global search. Live TV includes an **Official channels** tab and integrates those players into their country guides.

Added titles retain publisher artwork, description, source link, creator and licence/usage link. Older shows use publisher artwork where episode-specific art is unavailable. Eleven feed entries without a synopsis use their descriptive episode title. Series open an episode picker with year/season selection, Previous, Next and the existing autoplay-next control. Saved shows are stored by reference rather than copying entire episode catalogues into browser storage.

NASA media URLs resolve on selection from the official asset manifest, prefer a medium MP4 and accept files only from images-assets.nasa.gov. Archive titles resolve through the existing Archive player. YouTube retains publisher playback restrictions and offers a source link if embedding is unavailable.

## Refreshing

Run `python scripts/refresh_open_catalogue.py` with Python 3.10 or newer. No API keys or third-party Python packages are required. The script downloads metadata, not media, and writes `data/open-catalogue.json` and its companion report. A missing major content type prevents overwriting the snapshot. Review the report, source permissions and catalogue diff before committing.

Metadata responses are cached in `../source-cache` by default. Set `STREAMSPHERE_SOURCE_CACHE` to a new directory for a fresh online snapshot, or set `STREAMSPHERE_CACHE_ONLY=1` for an offline rebuild from a complete cache. Partial provider failures are recorded in the report; the shipped snapshot includes one timed-out Archive query and does not claim exhaustive coverage.

Source-declared public-domain status can depend on jurisdiction. Archive hosting alone is not evidence of permission. The importer requires an explicit accepted declaration and records its source; it does not certify every legacy playlist or imply endorsement by publishers. Official news embeds are distinct from a Creative Commons redistribution licence. Upstream availability can change.

## Validation

`tests/tv-experience.cjs` covers catalogue filters, visible source and licence credits, compact saved shows, year-based episode selection, Next, NASA trusted-host asset resolution, official live playback, and responsive layouts alongside existing TV regressions. The real snapshot was checked for required metadata and duplicate episode URLs; representative NASA, Blender, Wikimedia and live-stream endpoints responded successfully. This does not assert that every remote media file was played end to end.
