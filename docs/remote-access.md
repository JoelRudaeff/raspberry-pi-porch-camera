# Remote access and hardening

The goal: watch the porch camera from outside the house **without exposing Home Assistant to the internet**. The only thing reachable from outside is one WireGuard UDP port, and through it only the Pi.

```
phone (cellular)
   │  WireGuard, UDP <WG_PORT>  (preshared key + split tunnel)
   ▼
internet ── dynamic DNS name ──► main router: port forward UDP <WG_PORT> → <PI_LAN_IP>:<WG_PORT>
                                                   │
                                                   ▼
                               Pi: WireGuard add-on ──► only <PI_LAN_IP>:8123 (HA, HTTPS) and :8555 (live video)
```

## 1. Dynamic DNS

The **Duck DNS** add-on keeps a hostname pointing at the home's changing public IP. Its token and hostname are secrets, so they are not in this repo. Use the hostname as `server.host` in the WireGuard add-on.

## 2. Port forwarding (on the main/ISP router, not on the Pi)

One rule only:

| Setting | Value |
|---|---|
| Protocol | **UDP** |
| External port | `<WG_PORT>`, a high non-default port (not 51820) |
| Internal port | the **same** `<WG_PORT>` (the add-on listens on the port you configure; a mismatch gives "no handshake") |
| Internal host | `<PI_LAN_IP>` |

Also, on the main router: turn **UPnP off**, **WPS off**, **remote management off**, use a strong admin password, and put IoT devices on a guest network. Do **not** forward 8123, 8555 or 22.

## 3. WireGuard add-on

See [`wireguard/addon-options.example.yaml`](../wireguard/addon-options.example.yaml).

- **Split tunnel**: `client_allowed_ips` is just the Pi (`/32`), so the phone's other traffic does not go through home.
- **Firewall inside the tunnel**: a VPN client can reach only `8123/tcp` (Home Assistant) and `8555` tcp/udp (Frigate WebRTC). Everything else, including SSH, is dropped. The whole LAN is not reachable, even with a stolen key.
- **Preshared key** per peer on top of the key pair.
- One peer per device. If a phone is lost, delete its peer and regenerate.

### Phone client tips
- Set **MTU 1280** on the tunnel. Without it, large packets are dropped on cellular: the HTTPS handshake never completes while Wi-Fi works.
- Enable **On-Demand** for cellular and Wi-Fi, *excluding* your home Wi-Fi network name.
- A freshly scanned QR code does **not** carry MTU or On-Demand, so set them again each time.
- Test on cellular: a recent "latest handshake" and growing "data received" mean the VPN is fine. No handshake means the port forward is wrong.

## 4. Home Assistant hardening

- **HTTPS only (TLS 1.3)**, using a private CA that signs a certificate for just this Pi. The CA's signing key is destroyed after issuing. Install the CA certificate on the phone and PC so they trust it. Keep the server key and CA key out of git.
- `http:` with `ip_ban_enabled: true` and `login_attempts_threshold: 5`.
- **2FA** on every account; remove stale refresh tokens and old mobile-app registrations.
- Alerts to the phone for failed logins and IP bans, and for available updates (see `homeassistant/automations.yaml`).
- Unused integrations and add-ons off (Matter, Bluetooth, UPnP, Radio Browser, ...). Add-ons on **auto-update**.
- MQTT stays internal: a dedicated `frigate` user on Mosquitto, no external listener.
- Frigate telemetry/version check off; WebRTC uses the LAN candidate only, with no public STUN.

## 5. SSH access (only when needed)

- The **Advanced SSH & Web Terminal** add-on is stopped and set to manual start.
- Key-only login, **protection mode stays on**, reachable from the home LAN only (the VPN firewall drops port 22).
- A dashboard switch starts and stops it, and an automation turns it off after 2 hours and notifies the phone (see `automations.yaml`).

## What is deliberately not in this repo

WireGuard private/preshared keys and QR codes, the Duck DNS token and hostname, the public IP, the port number, the CA and server private keys, the MQTT password, the HA auth and secrets files, and the databases.
