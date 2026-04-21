import asyncio
import logging
import os
import time

from evohomeasync2 import EvohomeClientOld
from prometheus_client import Gauge, start_http_server

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

TEMPERATURE = Gauge("evohome_temperature_celsius", "Measured zone temperature", ["zone"])
SETPOINT = Gauge("evohome_setpoint_celsius", "Target zone setpoint", ["zone"])
UP = Gauge("evohome_up", "1 if last poll succeeded, 0 if it failed")
LAST_SCRAPE = Gauge("evohome_last_scrape_timestamp_seconds", "Unix timestamp of last successful poll")


def _require_env(key):
    val = os.environ.get(key)
    if not val:
        raise SystemExit(f"Missing required environment variable: {key}")
    return val


def _int_env(key, default, minimum=None):
    raw = os.environ.get(key, str(default))
    try:
        val = int(raw)
    except ValueError:
        raise SystemExit(f"{key} must be an integer, got: {raw!r}")
    if minimum is not None and val < minimum:
        raise SystemExit(f"{key} must be >= {minimum}, got: {val}")
    return val


# Set VERBOSE=1 to log each zone reading on every successful poll.
# By default only errors are logged.
VERBOSE = os.environ.get("VERBOSE", "0") == "1"
POLL_INTERVAL = _int_env("POLL_INTERVAL", 60, minimum=10)
PORT = _int_env("PORT", 8082)
UPDATE_TIMEOUT = 30  # seconds before evo.update() is considered hung


async def _poll_once(evo):
    await asyncio.wait_for(evo.update(), timeout=UPDATE_TIMEOUT)
    for zone in evo.tcs.zones:
        if zone.temperature is not None:
            TEMPERATURE.labels(zone=zone.name).set(zone.temperature)
        if zone.target_heat_temperature is not None:
            SETPOINT.labels(zone=zone.name).set(zone.target_heat_temperature)
        if VERBOSE:
            log.info("%s: %.1fC -> %.1fC", zone.name, zone.temperature or 0, zone.target_heat_temperature or 0)
    UP.set(1)
    LAST_SCRAPE.set(time.time())


async def poll(username, password):
    # Outer loop: reconnects (re-authenticates) on any connection-level failure.
    # Auth happens once per connection, not on every poll.
    while True:
        try:
            async with EvohomeClientOld(username, password) as evo:
                while True:
                    await _poll_once(evo)
                    await asyncio.sleep(POLL_INTERVAL)
        except Exception as e:
            log.error("Connection error, will reconnect: %s", e)
            UP.set(0)
            await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    username = _require_env("EVOHOME_USERNAME")
    password = _require_env("EVOHOME_PASSWORD")
    UP.set(0)  # defined state before first poll completes
    start_http_server(PORT)
    log.info("Metrics on :%d, polling every %ds", PORT, POLL_INTERVAL)
    asyncio.run(poll(username, password))
