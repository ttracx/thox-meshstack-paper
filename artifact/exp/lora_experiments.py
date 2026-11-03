"""LoRa airtime for MeshStack control-plane messages (calculated).

Why. MeshLink, a LoRa auxiliary mesh on ESP32-class nodes running Meshtastic
firmware, is a candidate carrier for control-plane traffic (presence, lease
heartbeats, revocation) when the LAN or tailnet is down. It can never carry
activation frames or KV bytes: the Meshtastic over-the-air payload ceiling is
239 bytes behind a 16-byte cleartext header, and the fastest preset moves about
21.9 kbit/s. This script quantifies what the control plane could afford.

Formula. Standard LoRa airtime (Semtech SX1276/SX1262 data sheets, section on
LoRa packet structure and time on air):

    T_sym       = 2^SF / BW
    T_preamble  = (n_pre + 4.25) * T_sym
    N_payload   = 8 + max( ceil( (8 PL - 4 SF + 28 + 16 CRC - 20 IH) / (4 (SF - 2 DE)) ) * (CR + 4), 0 )
    T_payload   = N_payload * T_sym
    T_air       = T_preamble + T_payload

with PL the on-air bytes (16-byte header + encrypted payload), explicit header
(IH = 0), CRC on (CRC = 1), CR = 1 for 4/5 and 4 for 4/8, and DE = 1 (low data
rate optimisation) when T_sym exceeds 16 ms, as the SX126x driver convention.
The 16-symbol sub-GHz preamble is the value stated in the Meshtastic mesh
algorithm documentation. Presets are the values in the Meshtastic radio
settings table (fetched 2026-11-03).

Duty-cycle budgets are regulatory and region specific; the 1 percent and 10
percent figures are illustrative EU sub-band limits and are swept as inputs.
No THOX radio was measured.

Outputs exp/results/lora.json.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

RESULTS = Path(__file__).with_name("results") / "lora.json"
HEADER_BYTES = 16
MAX_PAYLOAD = 239
PREAMBLE_SYMBOLS = 16
PRESETS = {
    "ShortTurbo": (500e3, 7, 1), "ShortFast": (250e3, 7, 1), "ShortSlow": (250e3, 8, 1),
    "MediumTurbo": (500e3, 9, 1), "MediumFast": (250e3, 9, 1), "MediumSlow": (250e3, 10, 1),
    "LongTurbo": (500e3, 11, 4), "LongFast": (250e3, 11, 1), "LongModerate": (125e3, 11, 4),
}
# Control-plane message sizes (encrypted payload bytes, before the 16-byte header).
MESSAGES = {
    "presence_beacon": 24,       # node id, epoch, flags, battery, thermal band
    "lease_heartbeat": 48,       # lease id, epoch, seq, state, headroom summary, MAC
    "revocation_notice": 64,     # grant id, principal, reason, signature prefix
    "capability_advert": 160,    # compact advertisement, nearly fills a packet
    "max_payload": MAX_PAYLOAD,
}
DUTY_CYCLES = [0.01, 0.10]


def airtime(bw: float, sf: int, cr: int, payload_bytes: int, crc: int = 1, ih: int = 0) -> dict:
    t_sym = (2 ** sf) / bw
    de = 1 if t_sym > 0.016 else 0
    pl = HEADER_BYTES + payload_bytes
    num = 8 * pl - 4 * sf + 28 + 16 * crc - 20 * ih
    den = 4 * (sf - 2 * de)
    n_payload = 8 + max(math.ceil(num / den) * (cr + 4), 0)
    t_pre = (PREAMBLE_SYMBOLS + 4.25) * t_sym
    t_pay = n_payload * t_sym
    return {"t_sym_ms": t_sym * 1e3, "ldro": de, "on_air_bytes": pl,
            "t_preamble_ms": t_pre * 1e3, "t_payload_ms": t_pay * 1e3, "t_air_ms": (t_pre + t_pay) * 1e3}


def main() -> int:
    rows = []
    for preset, (bw, sf, cr) in PRESETS.items():
        for mname, size in MESSAGES.items():
            a = airtime(bw, sf, cr, size)
            for dc in DUTY_CYCLES:
                a2 = dict(a)
                a2.update({"preset": preset, "bandwidth_hz": bw, "sf": sf, "cr_denominator": cr + 4,
                           "message": mname, "payload_bytes": size, "duty_cycle": dc,
                           "max_messages_per_minute": dc * 60e3 / a["t_air_ms"],
                           "max_messages_per_hour": dc * 3600e3 / a["t_air_ms"]})
                rows.append(a2)
    # Heartbeat budget: nodes x heartbeats/min under duty cycle on LongFast and ShortFast
    budgets = []
    for preset in ["LongFast", "MediumFast", "ShortFast"]:
        bw, sf, cr = PRESETS[preset]
        a = airtime(bw, sf, cr, MESSAGES["lease_heartbeat"])
        for dc in DUTY_CYCLES:
            for interval_s in [5, 20, 60, 300]:
                per_node_per_min = 60 / interval_s
                budgets.append({"preset": preset, "duty_cycle": dc, "heartbeat_interval_s": interval_s,
                                "t_air_ms": a["t_air_ms"],
                                "nodes_supported": math.floor((dc * 60e3 / a["t_air_ms"]) / per_node_per_min)})
    out = {"evidence_label": "calculated from the standard LoRa airtime formula and the Meshtastic preset table; no radio measured",
           "constants": {"header_bytes": HEADER_BYTES, "max_payload_bytes": MAX_PAYLOAD, "preamble_symbols": PREAMBLE_SYMBOLS},
           "presets": {k: {"bandwidth_hz": v[0], "sf": v[1], "cr": f"4/{v[2] + 4}"} for k, v in PRESETS.items()},
           "messages": MESSAGES, "rows": rows, "heartbeat_budgets": budgets}
    RESULTS.write_text(json.dumps(out, indent=2))
    for r in rows:
        if r["duty_cycle"] == 0.10 and r["message"] in ("lease_heartbeat", "max_payload"):
            print(f"{r['preset']:13s} {r['message']:16s} {r['t_air_ms']:8.1f} ms  {r['max_messages_per_minute']:7.1f}/min @10%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
