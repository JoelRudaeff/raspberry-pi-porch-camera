# Raspberry Pi 5 porch camera: Home Assistant + Frigate

A low-power, fully local porch camera on a **Raspberry Pi 5 running Home Assistant OS**. A USB webcam is analysed by **Frigate** (CPU-only, person detection), and Home Assistant sends a phone notification with a snapshot when someone is at the door. Everything stays on the home network; remote access goes through a VPN.

Personal values are replaced with placeholders: `{FRIGATE_MQTT_PASSWORD}`, `<PI_LAN_IP>`, `notify.mobile_app_YOUR_PHONE`.

## What is in here

| Path | What it does |
|---|---|
| `frigate/config.yml` | Frigate add-on config: one USB webcam (`/dev/video0`, MJPEG) encoded once to H.264 by go2rtc, 640x360 @ 5 fps CPU detection, person-only tracking, recordings kept only around alerts (60 days), MQTT snapshots for notifications. Tuned for ~7 W. |
| `homeassistant/automations.yaml` | Person notification (rate-limited to 1/min), daily people counter, failed-login / IP-ban alert, update-available alert, **SSH auto-off after 2 h**. |
| `homeassistant/dashboard-porch_security.json` | The "Porch & Security" dashboard: live view, last person, counters, system health (CPU, temperature, fan, disk, power status), toggles for detection/recording/alerts, update status, SSH switch. |
| `homeassistant/counter.json` | The `porch_people_today` counter helper. |
| `homeassistant/dashboards-registry.json` | Dashboard registration (storage mode). |
| `docs/remote-access.md`, `wireguard/addon-options.example.yaml` | VPN, dynamic DNS, port forwarding and HA hardening, with placeholders. |
| `homeassistant/configuration.yaml` | Stock config plus includes. |

## Hardening

- Home Assistant over local HTTPS, IP ban after 5 failed logins, with a push alert on every failed login or ban.
- Push alert when a Core, OS, Supervisor or firmware update is available.
- The SSH add-on is **off by default**; a switch on the dashboard turns it on, and an automation turns it off again after 2 hours (checked every 15 min so a restart cannot leave it open).
- Frigate telemetry/version check off; no public STUN server for WebRTC, so nothing leaves the LAN.
- MQTT is the local Mosquitto add-on with a dedicated `frigate` user.
- Remote viewing goes through a WireGuard VPN limited to the Pi, with one UDP port forward. The dashboard itself is never exposed. See [docs/remote-access.md](docs/remote-access.md).

## Setup

1. Install the **Frigate**, **Mosquitto broker** and **Advanced SSH & Web Terminal** add-ons, plus the Frigate integration (HACS).
2. Create a Mosquitto user `frigate` and put its password in `frigate/config.yml` (or keep it in a file on the Pi and substitute it in).
3. Set `<PI_LAN_IP>` to the Pi's LAN address (used for WebRTC live view).
4. Copy `automations.yaml` into the HA config and set your phone's notify service. Find it under Developer Tools > Actions: `notify.mobile_app_<your phone>`.
5. Create the counter helper, then import the dashboard JSON (it is a `.storage` file; or paste its views into a raw-config dashboard).
6. Entity names (`camera.porch_live`, `switch.porch_camera_*`, ...) come from the Frigate integration and the camera name `porch`. If you rename the camera, update the dashboard.

## Tuning notes

- Webcams behind glass score people lower than CCTV, so `threshold` is 0.5 and `min_score` 0.45 (Frigate's default is 0.7).
- Overnight the sensor noise looks like motion and raises CPU use; a motion-threshold tweak helps.
- Measured average draw is roughly 7 W at the wall (about 5 kWh a month).
