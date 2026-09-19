# StreamSphere TV — television experience refresh

## Design concepts

Three complementary concepts guide this implementation:

1. **Cinema at home.** A dark navy canvas, restrained sea-glass accent, generous artwork, a featured billboard and clear content rails. Home begins with something to discover; the player appears when a viewer selects something.
2. **The channel guide.** A channel-first destination with UK, sports and news entry points, network selection, full-width channel rows, stable numbers, category filters, channel search, alphabetical sorting and saved-channel filtering. No invented programmes or schedules: the feeds provide channel information only.
3. **Your television.** My List brings saved films, series and channels together, while continue watching retains the existing saved playback positions. Mobile has persistent Home / Live TV / Movies / Search / My List shortcuts.

The result combines these concepts. It keeps the existing one-file application, source catalogue, player integrations and optional local preferences.

## Main changes

- Content-first Home; source browsing moves to a dismissible drawer on every screen size.
- One visual search with Everything / Movies / TV shows / Live channels filters. Search includes loaded sources, the movie catalogue, the series catalogue, a UK/Pluto channel index and Internet Archive search. Additional networks enter the index when browsed.
- Search cards open details for films/shows and tune directly to live channels. Series open an episode selector; collection identifiers are never handed to the media player.
- Guide favourites, channel-name search, category chips, alphabetical sorting, stable channel numbers and useful empty states.
- Collection grids have title search alongside genre and sort controls.
- Favourites refresh My List; shows can also be saved.
- An explicit close-player action releases media and cancels stale playback work. Blocked-source explanations stay visible in the content-first layout.
- Mobile playback actions retain Cast/AirPlay, picture-in-picture and fullscreen access. Light mode remains available in Settings.
- Search supports Escape from its input, focus containment and return focus. The closed source drawer is inert.
- Rapid filter changes cancel obsolete DOM-render chunks; interrupted shelves can rebuild on return.
- Smaller sponsor placement after browsing; no changes to source URLs or automatic affiliate behavior.
- Default dark appearance, updated installable-app colours and service-worker cache version.

## Validation

`tests/tv-experience.cjs` uses deterministic playlists and metadata, isolated from production data. It checks navigation, guide filtering, favourites, number stability, stale render cancellation, blocked-source UI, search scopes, Escape, detail handoff, media URL assignment and cleanup, My List, series selection, theme switching, and layouts at 320, 390, 768 and 1440 pixels.

Run with Node and Playwright installed:

```sh
npm install --no-save playwright
npx playwright install chromium
node tests/tv-experience.cjs
```

For an existing browser installation, set `BROWSER_EXECUTABLE_PATH`. `TAILWIND_CDN_PATH` can point to a local copy of the app's Tailwind CDN script for offline test runs. The test server chooses a free local port and closes on exit.

These tests validate the interface and player handoffs. They do not establish the availability of every third-party channel, regional playback rights, or physical Cast/AirPlay-device behavior. Existing stream restrictions and failures remain visible in the player.

## Screenshots

These are captures of the implemented page, with the default Home billboard visible while external catalogue artwork loads.

![Desktop Home](home-desktop.png)

![Mobile Home](home-mobile.png)

![Live TV](live-tv-desktop.png)
