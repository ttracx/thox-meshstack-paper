"""PLACE crossover: when does transferring a KV prefix beat recomputing it?

Closed-form screen, evaluated on a grid. For a prefix of L tokens with k bytes
of KV per token (real geometry), a lossless wire ratio r (measured in
compression_experiments.py and read from its results file), an effective link
payload rate B bytes/s and a per-transfer overhead a seconds:

    T_transfer(L)  = (L * k / r) / B + a
    T_recompute(L) = L / P                 (P = prefill tokens/s on the stage)

PLACE chooses transfer when T_transfer < T_recompute. The crossover prefix is

    L* = a / (1/P - k/(r B))   when  1/P > k/(r B), else no crossover (recompute always wins).

B and P are swept, not measured: no THOX link or prefill rate has been measured.
The output is the sign and location of the crossover under stated inputs.

Outputs exp/results/place.json.
"""
from __future__ import annotations

import json
from pathlib import Path

RESULTS = Path(__file__).with_name("results") / "place.json"
COMPRESSION = Path(__file__).with_name("results") / "compression.json"

LINK_RATES_MBPS = [25, 50, 100, 200, 400, 800]        # effective payload rates, assumed sweep
PREFILL_TOK_S = [20, 50, 100, 200, 500, 1000, 2000]   # assumed sweep (no THOX measurement)
OVERHEAD_S = 0.02                                      # per-transfer overhead, assumed
PREFIXES = [256, 1024, 4096, 16384]


def kv_per_token_geometries(ratio_measured: float) -> list[dict]:
    return [
        {"name": "Qwen2.5-0.5B (real)", "kv_bytes_per_token": 12288, "ratio": ratio_measured},
        {"name": "27.8B demo geometry (design record)", "kv_bytes_per_token": 65536, "ratio": ratio_measured},
        {"name": "32-layer GQA 8x128 (illustrative)", "kv_bytes_per_token": 131072, "ratio": ratio_measured},
    ]


def crossover(k: float, r: float, B: float, P: float, a: float) -> float | None:
    denom = 1.0 / P - k / (r * B)
    return (a / denom) if denom > 0 else None


def main() -> int:
    comp = json.loads(COMPRESSION.read_text())
    # measured lossless ratio: bytesplit-zstd3 on the 2048-token real KV sample
    row = next(r for r in comp["rows"] if r["sample"] == "kv-2048" and r["codec"] == "bytesplit-zstd3")
    ratio = row["ratio"]
    grid = []
    for g in kv_per_token_geometries(ratio):
        for mbps in LINK_RATES_MBPS:
            B = mbps * 1e6 / 8
            for P in PREFILL_TOK_S:
                L = crossover(g["kv_bytes_per_token"], 1.0, B, P, OVERHEAD_S)
                Lc = crossover(g["kv_bytes_per_token"], g["ratio"], B, P, OVERHEAD_S)
                grid.append({"geometry": g["name"], "link_mbps": mbps, "prefill_tok_s": P,
                             "crossover_tokens_uncompressed": L, "crossover_tokens_compressed": Lc})
    examples = []
    for g in kv_per_token_geometries(ratio):
        for L in PREFIXES:
            for mbps in [50, 200, 800]:
                B = mbps * 1e6 / 8
                for P in [50, 500]:
                    tt = (L * g["kv_bytes_per_token"] / g["ratio"]) / B + OVERHEAD_S
                    tu = (L * g["kv_bytes_per_token"]) / B + OVERHEAD_S
                    tr = L / P
                    examples.append({"geometry": g["name"], "prefix_tokens": L, "link_mbps": mbps,
                                     "prefill_tok_s": P, "t_transfer_compressed_s": tt,
                                     "t_transfer_uncompressed_s": tu, "t_recompute_s": tr,
                                     "place": "transfer" if tt < tr else "recompute"})
    out = {"evidence_label": "calculated screen on an assumed link and prefill grid; the only measured input is the lossless ratio",
           "inputs": {"measured_ratio_bytesplit_zstd3_kv2048": ratio, "link_rates_mbps": LINK_RATES_MBPS,
                      "prefill_tok_s": PREFILL_TOK_S, "overhead_s": OVERHEAD_S},
           "grid": grid, "examples": examples}
    RESULTS.write_text(json.dumps(out, indent=2))
    print("ratio", ratio)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
