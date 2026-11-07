#!/usr/bin/env python3
"""Open or close Remote Desktop access to the home PC for WireGuard VPN clients.

Called by Home Assistant (shell_command.rdp_vpn) with "on" or "off". It runs inside the
Home Assistant container and uses its SUPERVISOR_TOKEN to rewrite the WireGuard add-on's
firewall rules, then restarts the add-on so they take effect (VPN drops for a few seconds).

VPN clients may always reach Home Assistant (8123) and Frigate live view (8555) on the Pi.
When "on", they may additionally reach the PC on 3389 (RDP over TCP and UDP). Everything
else from the VPN is dropped either way.
"""
import json
import os
import sys
import urllib.request

SLUG = "a0d7b954_wireguard"
PI = "<PI_LAN_IP>"
PC = "<PC_LAN_IP>"
API = "http://supervisor"
HEADERS = {"Authorization": "Bearer " + os.environ["SUPERVISOR_TOKEN"], "Content-Type": "application/json"}


def firewall(rdp: bool) -> tuple[str, str]:
    allow = [f"-d {PI} -p tcp --dport 8123", f"-d {PI} -p tcp --dport 8555", f"-d {PI} -p udp --dport 8555"]
    if rdp:
        allow += [f"-d {PC} -p tcp --dport 3389", f"-d {PC} -p udp --dport 3389"]
    up = [
        "iptables -A INPUT -i %i -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT",
        "iptables -A INPUT -i %i -j DROP",
        *[f"iptables -A FORWARD -i %i {a} -j ACCEPT" for a in allow],
        "iptables -A FORWARD -i %i -j DROP",
        "iptables -A FORWARD -o %i -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT",
        "iptables -A FORWARD -o %i -j DROP",
        "iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE",
    ]
    post_up = "; ".join(up)
    return post_up, post_up.replace("-A ", "-D ")


def call(method: str, path: str, data: dict | None = None) -> dict:
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(API + path, data=body, headers=HEADERS, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else {}


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("on", "off"):
        sys.exit("usage: rdp_vpn.py on|off")
    want = sys.argv[1] == "on"
    options = call("GET", f"/addons/{SLUG}/info")["data"]["options"]
    post_up, post_down = firewall(want)
    if options["server"].get("post_up") == post_up:
        print(f"RDP over VPN already {sys.argv[1]}")
        return
    options["server"]["post_up"], options["server"]["post_down"] = post_up, post_down
    call("POST", f"/addons/{SLUG}/options", {"options": options})
    call("POST", f"/addons/{SLUG}/restart")
    print(f"RDP over VPN {sys.argv[1]}")


if __name__ == "__main__":
    main()
