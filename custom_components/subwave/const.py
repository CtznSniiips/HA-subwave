"""Constants for the SUB/WAVE integration."""

DOMAIN = "subwave"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_PORT = 7700
DEFAULT_NAME = "SUB/WAVE"
DEFAULT_SCAN_INTERVAL = 15  # seconds

MIN_SCAN_INTERVAL = 5
MAX_SCAN_INTERVAL = 120

API_NOW_PLAYING = "/api/now-playing"
API_STATE = "/api/state"
API_SESSION = "/api/session"

# Maps stream format key -> file name served by SUB/WAVE
STREAM_FORMATS = {
    "mp3": "stream.mp3",
    "opus": "stream.opus",
    "flac": "stream.flac",
    "aac": "stream.aac",
}

MANUFACTURER = "SUB/WAVE"
