# Changelog

All notable changes to the SUB/WAVE Home Assistant integration are documented here.

## 0.6.5

### Added
- New `subwave.submit_request` service for submitting a listener request
  (`text`, optional `name`) to a specific SUB/WAVE server, for use in
  scripts, automations, or Assist.
- New `SubwaveSubmitRequest` Assist intent, registered so voice control can
  trigger a request. Targets the first configured SUB/WAVE server if more
  than one is set up.
- Sample custom sentences (`custom_sentences/en/subwave.yaml`) to copy into
  `config/custom_sentences/en/` for phrases like "request Take On Me by
  a-ha" through Assist.
- README section documenting the new service and voice setup steps.

### Changed
- Refactored listener-request submission into a shared
  `SubWaveCoordinator.async_submit_request()` method (with a new
  `SubWaveRequestError` exception) so the Lovelace card's HTTP proxy and
  the new service share identical logic instead of duplicating the POST
  and error handling.

## 0.6.4
- Initial release

### What's Included
#### Setup
- Config flow: connect by host/port, validated against the SUB/WAVE now-playing endpoint before the entry is created
- Options flow: configurable polling interval
- HACS-compatible, with frontend module auto-registered on setup (no manual Lovelace resource needed)

#### Media Player
- media_player.* entity for the station, supporting media browsing and playback
- Browse menu offers both a direct LAN stream (fastest, same-network only) and a proxied-through-HA stream (works remotely via Nabu Casa or a reverse proxy)
- Multiple stream formats supported where the station has them enabled (MP3/Opus/FLAC/AAC)

#### Sensors
- DJ, Now Playing, Listeners, Weather, Show, Up Next, Last Request, DJ Activity, DJ Commentary, Session, Broadcast Status, and LLM Tokens Used
- Stream Online (connectivity)
- Needs Setup (diagnostic, disabled by default in the entity registry)

#### Switch
- Stream Proxy — enables/disables the HA-side stream proxy per server, default on; lets you disable the unauthenticated proxy stream if/when remote playback isn't needed

#### Backend
- Stream proxy endpoint: relays the live audio stream through HA's own webserver for remote-friendly playback
- Listener request proxy endpoint: authenticated, forwards song/vibe requests to the station
- Devices grouped per SUB/WAVE server, showing station name and a link back to the server

#### Lovelace Card (custom:subwave-card)
- Four layouts: Compact, Hero art, Retro FM, and Requests only 
- Built-in listener request form with name/text fields and feedback messaging
- Configurable: card title, DJ name/tagline visibility, and a toggle for whether the request form is always shown or tap-to-reveal
