# <img src="/custom_components/subwave/brand/icon.png" height="60" /> SUB/WAVE for Home Assistant

A HACS-compatible custom integration that connects Home Assistant to a [SUB/WAVE](https://github.com/perminder-klair/subwave) AI radio station server, exposing what's playing, the current AI DJ, listener counts, weather/show context, and the live stream URLs. 

A lovelace card is included with 4 different layout styles allowing you to play your station and make requests right from your Home Assistant dashboard. A built-in proxy allows streaming your station even when accessing Home Assistant remotely.

## Entities created

For each configured SUB/WAVE server you get one device with:

| Entity | Type | Notes |
|---|---|---|
| `media_player.<station>` | Media Player | State reflects `streamOnline`/listener count. Title/artist/album/cover art come from `nowPlaying`. Album art is fetched from `/api/cover/<subsonic_id>` and proxied through HA's own media-image endpoint (works remotely). Carries a `dj_commentary` attribute (the DJ's latest spoken link, from `/api/session`) for use in automations/templates. Supports `browse_media` to list available stream formats (mp3/opus/flac/aac) as playable URLs — hand one to a real speaker via `media_player.play_media`. |
| `sensor.<station>_dj` | Sensor | Current AI DJ name; tagline/station/avatar as attributes |
| `sensor.<station>_now_playing` | Sensor | Track title; artist/album/genre/moods/energy/bpm/year as attributes |
| `sensor.<station>_listeners` | Sensor | Current listener count; peak as attribute |
| `sensor.<station>_weather` | Sensor | Weather condition driving the station's vibe; temp/location/mood as attributes |
| `sensor.<station>_show` | Sensor | Current show/period name; vibe/mood/dominant mood as attributes |
| `sensor.<station>_llm_tokens` | Sensor | Cumulative LLM tokens used by the DJ agent |
| `binary_sensor.<station>_stream_online` | Binary Sensor | Connectivity class; bitrate/format/mount as attributes |
| `sensor.<station>_up_next` | Sensor | Title of the next queued track ("Nothing queued" if empty); artist/requested_by/source/full queue as attributes |
| `sensor.<station>_last_request` | Sensor | Name of whoever most recently requested a track (checks current, then falls back through history); "None" if nothing was listener-requested recently |
| `sensor.<station>_dj_activity` | Sensor | Latest DJ log line (track changes, scheduler events, skill runs); last 10 entries as an attribute |
| `sensor.<station>_dj_commentary` | Sensor | The DJ's most recent spoken link/transition (truncated to 255 chars for the state; full text always in the `full_text` attribute). Also carries the DJ's track-pick reasoning as attributes |
| `sensor.<station>_session` | Sensor | Current autonomous session's kind (e.g. `auto`); id/key/show/started_at plus the last 5 scenario/mood-shift events as attributes |
| `sensor.<station>_broadcast_status` | Sensor | SUB/WAVE's own reported status (e.g. `on-air`) from the lightweight `/api/health` check |
| `binary_sensor.<station>_needs_setup` | Binary Sensor | Diagnostic; true if SUB/WAVE is flagging it needs attention. Also carries `auto_pick`/`auto_link`/`picker_busy` as attributes |

## Installation (HACS)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=CtznSniiips&repository=HA-subwave&category=integration)

1. HACS → the "⋮" menu → **Custom repositories**
2. Add this repo's URL, category **Integration**
3. Install "SUB/WAVE", then restart Home Assistant
4. Settings → Devices & Services → **Add Integration** → search "SUB/WAVE"
5. Enter the host/IP and port (default `7700`) of your SUB/WAVE server

## Manual installation

Copy `custom_components/subwave` into your Home Assistant `config/custom_components/`
directory, restart HA, then add the integration as above.

## Options

After setup, click **Configure** on the integration to change the polling
interval (default 15s, range 5–120s).

## Album art

Track cover art is fetched from SUB/WAVE's `/api/cover/<subsonic_id>`
endpoint (the same `subsonic_id` returned in `nowPlaying`) and falls back
to the DJ's avatar when a track has no cover. Home Assistant fetches the
image bytes itself and serves them through its own authenticated
`/api/media_player_proxy` endpoint (the standard `async_get_media_image`
pattern), so artwork shows up correctly in the frontend whether you're on
the LAN or accessing HA remotely - no extra proxy setup needed for this
part, it's built into `media_player.py`.

## Lovelace card

This integration bundles a custom card - `custom:subwave-card` - showing
now playing/album art, in-browser play/stop, a volume slider, and a
listener request form. It's registered automatically as a frontend module
when the integration loads, so there's no manual step in Settings →
Dashboards → Resources.

**Layouts**: the card ships with four selectable layouts:

| Layout | Feel | Screenshot |
|---|---|---|
| `compact` (default) | Single-row tile - art thumbnail, title/artist, station name, power button, volume slider, listener count. Smallest footprint. | <img src="/screenshots/compact.png" height="300" /> |
| `hero` | Large centered album art, big power button, volume slider, everything stacked and centered. | <img src="/screenshots/hero_art.png" height="300" /> |
| `retro` | Monospace "LED readout" track display with album art nested to the right inside the readout box, an ON AIR / OFFLINE badge, volume slider next to the power button. | <img src="/screenshots/retrofm.png" height="300" /> |
| `requests` | Just the station name and request form — text + optional name + Send button. Nothing else: no art, no now-playing title, no power button, no volume slider. | <img src="/screenshots/requests.png" height="300" /> |

**Adding it:** Edit a dashboard → Add Card → search "SUB/WAVE Radio", or
add it via YAML:

```yaml
type: custom:subwave-card
entity: media_player.weird_music_radio   # your SUB/WAVE media_player entity
layout: hero                              # optional - compact | hero | retro (default compact)
title: Weird Music Radio                  # optional - defaults to no header
requests_mode: always                     # optional - hidden | always (default always)
show_dj: true                             # optional - default true
```

`requests_mode` controls the listener request form:
- `hidden` - collapsed by default; click anywhere on the card (outside
  the power button/volume/inputs) to show/hide it. The card gets a
  pointer cursor as the only affordance - useful for keeping it compact
  day-to-day while still making requests easy to find.
- `always` (default) - always visible

The layout picker, entity picker, title field, request-form mode, and DJ
toggle are all configurable through the card's own UI editor (click the
pencil icon after adding it) - no YAML required. Changing the layout or
request mode in the editor rebuilds the card's DOM immediately so you can
compare options live.

The power button matches SUB/WAVE's own native player styling: an outline
circle (no fill) with a grey glyph when off and a red glyph when playing,
using `mdi:power` throughout rather than swapping icons.

**Playback**: the card plays the stream directly in the browser tab via
an embedded `<audio>` element pointed at the HA-proxied stream URL (see
[Remote access](#remote-access-stream-proxy) above) - so it works the same
whether you're on the LAN or accessing HA remotely. This is separate from
the `media_player.<station>` entity's own state, which reflects SUB/WAVE's
broadcast status, not whether the card's local `<audio>` element happens
to be playing in your browser right now. To cast to a real speaker instead
of playing in-tab, use the entity's `browse_media` picker (see the
[cast example](#example-cast-the-stream-to-a-speaker) above).

**Requests**: submitting the form POSTs `{"text": ..., "name": ...}` to
SUB/WAVE's `/api/requests`, via a Home Assistant proxy endpoint
(`/api/subwave/<entry_id>/requests`) rather than hitting SUB/WAVE
directly - this keeps it working through remote access and avoids
cross-origin issues, the same way the stream/artwork proxies do. Unlike
those, this endpoint requires normal HA authentication, since it's a
write action; the card handles that automatically via `hass.callApi()`.
The "Your name" field is remembered in the browser (`localStorage`) so
repeat listeners don't have to retype it.

### Requests via voice / Assist

There's also a `subwave.submit_request` service that does the same thing
as the card's Requests form, for use in scripts, automations, or Assist:

```yaml
service: subwave.submit_request
data:
  config_entry_id: <your SUB/WAVE config entry>
  text: "Take On Me by a-ha"
  name: "Steve"   # optional
```

To trigger this by voice, copy
[`custom_sentences/en/subwave.yaml`](custom_sentences/en/subwave.yaml) from
this repo into your HA config at `config/custom_sentences/en/subwave.yaml`
and restart Home Assistant (custom sentences have to live in your config
directory - HACS can't install them there automatically). That gives you
sentences like "request Take On Me by a-ha" through Assist. If you run more
than one SUB/WAVE server, the voice intent always targets whichever one
was set up first; use the service directly (e.g. from a sentence trigger
automation) if you need to pick a specific server.

## Remote access (stream proxy)

SUB/WAVE's own stream URLs (`http://192.168.x.x:7700/stream.mp3`) only work
on your local network. If you access Home Assistant remotely - Nabu Casa,
or your own reverse proxy - and want a device outside your LAN (or the
mobile app) to play the stream, use the built-in HA proxy instead:

```
https://<your-ha-external-url>/api/subwave/<config_entry_id>/stream.mp3
```

This integration registers that endpoint automatically. Home Assistant
fetches the stream from SUB/WAVE on your LAN and relays the bytes out
through its own webserver - so the URL works anywhere HA itself is
reachable, without ever exposing SUB/WAVE directly to the internet.

You don't need to build this URL by hand:

- The `media_player.<station>` entity's `browse_media` picker (Lovelace
  media browser) shows two folders: **Direct stream (same network)** and
  **Via Home Assistant (remote-accessible)** - pick a format from whichever
  fits your target device.
- The entity also exposes a `proxy_stream_url` attribute you can reference
  directly in scripts/automations.

The proxy resolves to whatever URL Home Assistant considers "best" for the
request context - Nabu Casa Remote UI URL if you have a subscription,
otherwise your configured external URL, falling back to your internal URL.
Set these under **Settings → System → Network** if you haven't already, or
just rely on Nabu Casa if that's how you access HA remotely.

Endpoint is unauthenticated (same pattern HA core uses for camera stream
proxies, since cast targets and `<audio>` players can't attach HA's auth
headers) - it only ever relays read-only audio bytes, but be aware anyone
who can reach your HA instance can hit it.

## Example: cast the stream to a speaker

```yaml
service: media_player.play_media
target:
  entity_id: media_player.living_room_speaker
data:
  media_content_id: http://YOUR_SUBWAVE_IP:7700/stream.mp3   # LAN only
  # or, for a remote/external speaker:
  # media_content_id: https://your-ha-url/api/subwave/<entry_id>/stream.mp3
  media_content_type: music
```

Or use `media_player.<station>`'s `browse_media` picker in the Lovelace
media browser to pick a format and send it to another player.

## Notes

- This integration is `local_polling` — no cloud, no auth, just periodic
  HTTP GETs to `/api/now-playing`.
- The `media_player` entity does not play audio on the HA host; SUB/WAVE
  has no device to "control" beyond exposing stream URLs, so play/pause
  aren't wired up as real transport controls.
- Tested against a `now-playing` payload shape including `nowPlaying`,
  `context` (time/weather/date/clock), `dj`, `listeners`, `stream`, and
  `llmTokens`. If your SUB/WAVE version's schema differs, the sensors will
  just show `unknown` for missing fields rather than erroring.
