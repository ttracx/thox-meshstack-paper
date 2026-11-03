"""Single source of truth: read every exp/results/*.json and write summary.json.

Every number that appears in a figure or in the paper text is read from
summary.json, which this script derives from the raw result files. No number
is typed by hand downstream.
"""
from __future__ import annotations

import json
from pathlib import Path

R = Path(__file__).with_name("results")
OUT = R / "summary.json"


def load(name: str) -> dict:
    return json.loads((R / name).read_text())


def compression_summary(c: dict) -> dict:
    rows = c["rows"]
    by = {}
    for r in rows:
        by.setdefault(r["sample"], {})[r["codec"]] = r
    best_kv2048 = max((r for r in rows if r["sample"] == "kv-2048" and r["bit_exact"]), key=lambda r: r["ratio"])
    fast_kv2048 = by["kv-2048"]["bytesplit-zstd3"]
    raw_kv2048 = by["kv-2048"]["raw-zstd3"]
    ctrl = by["control-gaussian"]["bytesplit-zstd3"]
    table = []
    for sample in ["kv-128", "kv-512", "kv-2048", "act-128", "act-512", "act-2048", "control-gaussian"]:
        for codec in ["raw-zstd3", "bytesplit-zstd3", "bytesplit-zstd9", "bytesplit-lzma", "hi-only-zstd3"]:
            r = by[sample][codec]
            table.append({"sample": sample, "codec": codec, "raw_MB": r["raw_bytes"] / 1e6, "ratio": r["ratio"],
                          "enc_MBps": r["encode_MBps_median"], "enc_q1": r["encode_MBps_q1"], "enc_q3": r["encode_MBps_q3"],
                          "dec_MBps": r["decode_MBps_median"], "bit_exact": r["bit_exact"]})
    return {
        "geometry": c["geometry"], "samples": c["samples"], "host": c["host"], "table": table,
        "kpi_ratio_bytesplit_zstd3_kv2048": fast_kv2048["ratio"],
        "kpi_ratio_raw_zstd3_kv2048": raw_kv2048["ratio"],
        "kpi_best_ratio_kv2048": {"codec": best_kv2048["codec"], "ratio": best_kv2048["ratio"]},
        "kpi_enc_MBps_bytesplit_zstd3_kv2048": fast_kv2048["encode_MBps_median"],
        "kpi_dec_MBps_bytesplit_zstd3_kv2048": fast_kv2048["decode_MBps_median"],
        "kpi_hi_plane_ratio_kv2048": by["kv-2048"]["hi-only-zstd3"]["ratio"],
        "kpi_control_gaussian_ratio": ctrl["ratio"],
        "kpi_act_ratio_bytesplit_zstd3_2048": by["act-2048"]["bytesplit-zstd3"]["ratio"],
        "all_bit_exact": all(r["bit_exact"] for r in rows if r["bit_exact"] is not None),
        "roundtrip_checks": sum(1 for r in rows if r["bit_exact"]),
        "timing_reps": rows[0]["timing_reps"],
        "kv_bytes_per_token_bf16": c["geometry"]["kv_bytes_per_token_bf16"],
        "kv_MiB_4096_tokens_bf16": c["geometry"]["kv_bytes_per_token_bf16"] * 4096 / 2 ** 20,
    }


def keying_summary(k: dict) -> dict:
    t = k["timing"]
    return {"properties": {p: v for p, v in k["properties"].items() if p.startswith("P")},
            "known_answer": k["properties"]["known_answer"],
            "per_chunk": t["per_chunk"], "chain": t["chain_4096_tokens_64_per_chunk"],
            "kpi_us_per_64_token_chunk": t["per_chunk"][0]["us_median"],
            "kpi_chain_4096_ms": t["chain_4096_tokens_64_per_chunk"]["us_median"] / 1e3,
            "kpi_keys_per_second_64": 1e6 / t["per_chunk"][0]["us_median"]}


def admission_summary(a: dict) -> dict:
    sc = a["scenarios"]

    def find(label_prefix: str, frac: float, ctx: int) -> dict:
        return next(s for s in sc if s["label"].startswith(label_prefix) and s["usable_fraction"] == frac and s["context_tokens"] == ctx)

    matrix = []
    for s in sc:
        matrix.append({"label": s["label"], "usable_fraction": s["usable_fraction"], "context_tokens": s["context_tokens"],
                       "result": s["result"], "layers_placed": s["layers_placed"], "layers_total": s["layers_total"],
                       "stages": [(st["node"], st["layer_start"], st["layer_end"], st["weight_bytes"] / 2 ** 30, st["kv_bytes"] / 2 ** 20) for st in s["stages"]]})
    trio = {f"{f}": find("C1", f, 2048)["result"] for f in a["assumptions"]["usable_fractions"]}
    hub = {f"{f}": find("C2", f, 2048)["result"] for f in a["assumptions"]["usable_fractions"]}
    return {"assumptions": a["assumptions"], "models": a["models"], "matrix": matrix,
            "kpi_trio_27b_at_floors": trio, "kpi_trio_plus_hub_27b": hub,
            "kpi_trio_total_floor_GB": sum(a["assumptions"]["class_floors_bytes"].values()) / 1e9,
            "kpi_27b_weights_GiB": a["models"]["demo27b"]["total_weight_bytes"] / 2 ** 30,
            "clip_nodes_needed_for_27b": a["clip_nodes_needed_for_27b"],
            "phi4mini_on_air_2048": find("B1", 0.8, 2048)["result"],
            "phi4mini_on_mini_2048": find("B2", 0.8, 2048)["result"],
            "phi4mini_on_mini_32768": find("B2", 0.8, 32768)["result"],
            "phi4mini_on_air_mini_32768": find("B3", 0.8, 32768)["result"],
            "qwen05b_on_air_32768_065": find("A", 0.65, 32768)["result"]}


def place_summary(p: dict) -> dict:
    g = p["grid"]

    def pick(geom_prefix, mbps, P):
        return next(x for x in g if x["geometry"].startswith(geom_prefix) and x["link_mbps"] == mbps and x["prefill_tok_s"] == P)

    return {"inputs": p["inputs"], "grid": g, "examples": p["examples"],
            "kpi_27b_100mbps_P100_compressed": pick("27.8B", 100, 100)["crossover_tokens_compressed"],
            "kpi_27b_100mbps_P100_uncompressed": pick("27.8B", 100, 100)["crossover_tokens_uncompressed"],
            "kpi_27b_100mbps_P500_compressed": pick("27.8B", 100, 500)["crossover_tokens_compressed"],
            "kpi_27b_800mbps_P500_compressed": pick("27.8B", 800, 500)["crossover_tokens_compressed"],
            "kpi_qwen_100mbps_P500_compressed": pick("Qwen", 100, 500)["crossover_tokens_compressed"]}


def lora_summary(l: dict) -> dict:
    rows = l["rows"]

    def pick(preset, msg, dc):
        return next(r for r in rows if r["preset"] == preset and r["message"] == msg and r["duty_cycle"] == dc)

    hb = {b["preset"] + f"@{b['duty_cycle']}@{b['heartbeat_interval_s']}s": b["nodes_supported"] for b in l["heartbeat_budgets"]}
    return {"presets": l["presets"], "messages": l["messages"], "rows": rows, "heartbeat_budgets": l["heartbeat_budgets"],
            "kpi_longfast_heartbeat_ms": pick("LongFast", "lease_heartbeat", 0.1)["t_air_ms"],
            "kpi_shortfast_heartbeat_ms": pick("ShortFast", "lease_heartbeat", 0.1)["t_air_ms"],
            "kpi_longfast_maxpayload_ms": pick("LongFast", "max_payload", 0.1)["t_air_ms"],
            "kpi_shortfast_maxpayload_ms": pick("ShortFast", "max_payload", 0.1)["t_air_ms"],
            "kpi_longfast_nodes_20s_10pct": hb["LongFast@0.1@20s"],
            "kpi_longfast_nodes_20s_1pct": hb["LongFast@0.01@20s"],
            "kpi_shortfast_nodes_20s_10pct": hb["ShortFast@0.1@20s"],
            "kpi_shortfast_nodes_5s_1pct": hb["ShortFast@0.01@5s"],
            "kpi_longfast_nodes_300s_1pct": hb["LongFast@0.01@300s"],
            "kpi_4096_kv_MiB_over_shortfast_hours": (4096 * 12288 / 239) * pick("ShortFast", "max_payload", 0.1)["t_air_ms"] / 3.6e6}


def churn_summary(c: dict) -> dict:
    cfgs = c["configs"]

    def pick(up, ttl, cache):
        return next(x for x in cfgs if x["mean_up_s"] == up and x["lease_ttl_s"] == ttl and x["decision_cache_s"] == cache)

    base = pick(600.0, 20.0, 30.0)["summary"]
    return {"model": c["model"], "configs": cfgs,
            "kpi_sessions_median": base["sessions"]["median"],
            "kpi_replans_median": base["replans"]["median"],
            "kpi_stale_unfenced_median": base["stale_completions_unfenced_accepted"]["median"],
            "kpi_stale_fenced_rejected_median": base["stale_completions_fenced_rejected"]["median"],
            "kpi_stale_auth_cached30_median": base["stale_auth_cached"]["median"],
            "kpi_stale_auth_cached300_median": pick(600.0, 20.0, 300.0)["summary"]["stale_auth_cached"]["median"],
            "kpi_stale_auth_live_median": base["stale_auth_live"]["median"],
            "kpi_max_stale_auth_per_session_cache30": base["max_stale_auth_per_session"]["median"],
            "kpi_max_stale_auth_per_session_cache300": pick(600.0, 20.0, 300.0)["summary"]["max_stale_auth_per_session"]["median"],
            "kpi_fail_closed_live_median": pick(600.0, 20.0, 0.0)["summary"]["fail_closed_on_dead_path"]["median"],
            "kpi_detect_latency_ttl20": base["detect_latency_median"]["median"],
            "kpi_detect_latency_ttl60": pick(600.0, 60.0, 30.0)["summary"]["detect_latency_median"]["median"],
            "kpi_detect_latency_ttl10": pick(600.0, 10.0, 30.0)["summary"]["detect_latency_median"]["median"]}


def main() -> int:
    summary = {
        "compression": compression_summary(load("compression.json")),
        "keying": keying_summary(load("keying.json")),
        "admission": admission_summary(load("admission.json")),
        "place": place_summary(load("place.json")),
        "lora": lora_summary(load("lora.json")),
        "churn": churn_summary(load("churn.json")),
    }
    OUT.write_text(json.dumps(summary, indent=2))
    kp = {k: v for sec in summary.values() for k, v in sec.items() if k.startswith("kpi")}
    print(json.dumps(kp, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
