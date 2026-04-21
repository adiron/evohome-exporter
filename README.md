# evohome-exporter

Prometheus exporter for Honeywell evohome thermostats connected via the RFG100
internet gateway and similar systems. Uses
[evohome-async](https://github.com/zxdavb/evohome-async) to poll the Honeywell
Total Connect Comfort API.

## Metrics

```
evohome_temperature_celsius{zone="Thermostat"}  19.5
evohome_setpoint_celsius{zone="Thermostat"}     19.0
evohome_up                                       1.0
evohome_last_scrape_timestamp_seconds            1776687201.29
```

- `evohome_temperature_celsius` - measured temperature per zone
- `evohome_setpoint_celsius` - temperature the actual unit is set to
- `evohome_up` - 1 if the last poll succeeded, 0 if it failed
- `evohome_last_scrape_timestamp_seconds` - unix timestamp of last successful poll

## Usage

This guide assumes you already have an account set up and your thermostat is
properly connected to it. This sounds simple, but Honeywell has a million apps
that are all similarly named, only *one* works. Anyway, that's on you.

```bash
cp .env.example .env
# fill in your Honeywell account credentials in .env
docker compose up -d --build
```

It is also possible to just straight up run the script on your own bare metal
like some kind of monster:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Set all the env variables as needed, see .env.example
python exporter.py
```

## Configuration

All configuration is via environment variables (`.env` file).

| Variable | Default | Description |
|---|---|---|
| `EVOHOME_USERNAME` | required | Honeywell account email |
| `EVOHOME_PASSWORD` | required | Honeywell account password |
| `POLL_INTERVAL` | `60` | Seconds between polls (minimum 10) |
| `PORT` | `8082` | Port to serve metrics on |
| `VERBOSE` | `0` | Set to `1` to log each zone reading on every poll |

## Adding to Prometheus

```yaml
- job_name: evohome
  static_configs:
    - targets: ['localhost:8082']
```

## License

MIT
