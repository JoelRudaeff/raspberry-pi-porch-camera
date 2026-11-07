# Raspberry Pi 5 porch camera: Home Assistant + Frigate

A low-power, fully local porch camera on a **Raspberry Pi 5 running Home Assistant OS**. A USB webcam is analysed by **Frigate** (CPU-only), which tells people apart from pigeons:

- **People**: Home Assistant sends a phone notification with a snapshot.
- **Pigeons**: a USB speaker on the Pi plays a quiet bird-of-prey call to chase them off. It only plays during set hours, and both the hours and an on/off switch are on the dashboard.

Everything stays on the home network, and remote access goes through a VPN.

Personal values are replaced with placeholders: `{FRIGATE_MQTT_PASSWORD}`, `<PI_LAN_IP>`, `<PC_LAN_IP>`, `notify.mobile_app_YOUR_PHONE`.

## What is in here

| Path | What it does |
|---|---|
| `frigate/config.yml` | Frigate add-on config. One USB webcam (`/dev/video0`, MJPEG) is encoded once to H.264 by go2rtc, with 640x360 @ 5 fps CPU detection. It tracks `person` (review **alerts**, kept 60 days) and `bird` (review **detections**, kept 14 days), and publishes MQTT snapshots for notifications. Tuned for ~7 W. |
| `homeassistant/automations.yaml` | Person notification (rate-limited to 1/min), daily people counter, **pigeon scare-off sound** and daily pigeon-visit counter, failed-login / IP-ban alert, update-available alert, **SSH auto-off after 2 h**, **Remote Desktop over VPN** switch. |
| `homeassistant/scripts.yaml` | `play_pigeon_scare_sound`: sets the volume and plays a random call through the VLC add-on. |
| `homeassistant/dashboard-porch_security.json` | The "Porch & Security" dashboard. **Porch view:** live view, last person, Pigeons section (status, visits today, last pigeon, sound switch, hours, volume, test button, 24 h timeline and log), privacy/recording toggles, SSH and Remote Desktop switches. **System view:** CPU, temperature, fan, disk, power status, updates. |
| `homeassistant/counter.json`, `input_boolean.json`, `input_datetime.json`, `input_number.json` | Helpers (`.storage` files): people and pigeon counters, pigeon sound switch, hours (default 08:00–20:00) and volume (default 30 %), Remote Desktop switch. |
| `homeassistant/rdp_vpn/rdp_vpn.py`, `windows/enable-rdp-via-pi.ps1` | Optional Remote Desktop to a home PC over the VPN; see [docs/remote-access.md](docs/remote-access.md#6-remote-desktop-to-a-home-pc-optional). |
| `pigeon/make_pigeon_sounds.py` | Synthesises the three scare-off calls (`scare_1..3.wav`). No downloaded audio. |
| `homeassistant/dashboards-registry.json` | Dashboard registration (storage mode). |
| `docs/remote-access.md`, `wireguard/addon-options.example.yaml` | VPN, dynamic DNS, port forwarding and HA hardening, with placeholders. |
| `homeassistant/configuration.yaml` | Stock config plus includes and the `rdp_vpn` shell command. |

## Pigeon deterrent

1. A pigeon is detected (Frigate label `bird`), and a review item on `frigate/reviews` contains it.
2. The counter goes up. If the **Scare-off sound** switch is on and the time is between **Sound from** and **Sound until**, `script.play_pigeon_scare_sound` plays one of three synthesised hawk-like calls through the USB speaker.
3. While the pigeon stays, it repeats every minute, at most 3 times. Varying the calls slows down habituation.

Playback uses the official **VLC** add-on (`media_player.vlc_telnet`). Its output is set to the USB speaker, and it has no host ports.

- Files are played as `file:///media/pigeon/scare_N.wav`. A Home Assistant media URL would not work here, because HA serves HTTPS with a private CA that VLC does not trust.
- On VLC's scale, HA volume `0.5` is 100 % (unamplified), so the dashboard's 0–100 % slider is divided by 200.

To create the sounds on the Pi: `python3 pigeon/make_pigeon_sounds.py /media/pigeon`.

## Hardening

- Home Assistant over local HTTPS, IP ban after 5 failed logins, with a push alert on every failed login or ban.
- Push alert when a Core, OS, Supervisor or firmware update is available.
- The SSH add-on is **off by default**; a switch on the dashboard turns it on, and an automation turns it off again after 2 hours (checked every 15 min so a restart cannot leave it open).
- Frigate telemetry/version check off; no public STUN server for WebRTC, so nothing leaves the LAN.
- MQTT is the local Mosquitto add-on with a dedicated `frigate` user.
- Remote viewing goes through a WireGuard VPN limited to the Pi, with one UDP port forward. The dashboard itself is never exposed. See [docs/remote-access.md](docs/remote-access.md).
- Remote Desktop to a home PC is **off by default**. It needs both the VPN and a dashboard switch, which opens only port 3389 to that one PC. The PC's own firewall accepts RDP only from the Pi, and Windows sign-in (NLA) is still required.

## Setup

1. Install the **Frigate**, **Mosquitto broker**, **Advanced SSH & Web Terminal** and (for the pigeon sound) **VLC** add-ons, plus the Frigate integration (HACS). Set the VLC add-on's audio output to the USB speaker and accept the discovered *VLC media player via Telnet* integration.
2. Create a Mosquitto user `frigate` and put its password in `frigate/config.yml` (or keep it in a file on the Pi and substitute it in).
3. Set `<PI_LAN_IP>` to the Pi's LAN address (used for WebRTC live view).
4. Copy `automations.yaml` into the HA config and set your phone's notify service. Find it under Developer Tools > Actions: `notify.mobile_app_<your phone>`.
5. Create the helpers (counters, switches, times, volume; see the helper JSON files), copy `scripts.yaml`, then import the dashboard JSON (it is a `.storage` file; or paste its views into a raw-config dashboard).
6. Entity names (`camera.porch_live`, `switch.porch_camera_*`, ...) come from the Frigate integration and the camera name `porch`. If you rename the camera, update the dashboard.

## Tuning notes

- Webcams behind glass score people lower than CCTV, so `threshold` is 0.5 and `min_score` 0.45 (Frigate's default is 0.7).
- The stock CPU model labelled pigeons as `person` at 50–70 %, nearly always as small boxes, so a person must cover at least 6000 px of the 640x360 frame (`min_area`). Pigeons are tracked as `bird` with lenient filters. If the stock model keeps calling pigeons "person", a YOLO model is the next step.
- Overnight the sensor noise looks like motion and raises CPU use; a motion-threshold tweak helps.
- Measured average draw is roughly 7 W at the wall (about 5 kWh a month).
