# SUB/WAVE for Home Assistant

A HACS-compatible custom integration that connects Home Assistant to a
[SUB/WAVE](https://github.com/yourusername/subwave) AI radio station server,
polling `/api/now-playing` and exposing what's playing, the current AI DJ,
listener counts, weather/show context, and the live stream URLs.

## Entities created

For each configured SUB/WAVE server you get one device with:

| Entity | Type | Notes |
|---|---|---|
| `media_player.<station>` | Media Player | State reflects `streamOnline`/listener count. Title/artist/album/cover art come from `nowPlaying`. Album art is fetched from `/api/cover/<subsonic_id>` and proxied through HA's own media-image endpoint (works remotely). Supports `browse_media` to list available stream formats (mp3/opus/flac/aac) as playable URLs — hand one to a real speaker via `media_player.play_media`. |
| `sensor.<station>_dj` | Sensor | Current AI DJ name; tagline/station/avatar as attributes |
| `sensor.<station>_now_playing` | Sensor | Track title; artist/album/genre/moods/energy/bpm/year as attributes |
| `sensor.<station>_listeners` | Sensor | Current listener count; peak as attribute |
| `sensor.<station>_weather` | Sensor | Weather condition driving the station's vibe; temp/location/mood as attributes |
| `sensor.<station>_show` | Sensor | Current show/period name; vibe/mood/dominant mood as attributes |
| `sensor.<station>_llm_tokens` | Sensor | Cumulative LLM tokens used by the DJ agent |
| `binary_sensor.<station>_stream_online` | Binary Sensor | Connectivity class; bitrate/format/mount as attributes |

## Installation (HACS)

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
