"""Generate every paper figure as SVG from exp/results/summary.json.

Fonts are referenced by name (svg.fonttype none) so the HTML embeds them.
Colors: THOX green #047C3D on white, ink #111827, greys. No number is typed
here; everything is read from summary.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import logging
import matplotlib
matplotlib.use("Agg")
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import NullFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
S = json.loads((ROOT / "exp" / "results" / "summary.json").read_text())
FIG = ROOT / "wp" / "figures"
FIG.mkdir(exist_ok=True)

GREEN = "#047C3D"
GREEN2 = "#05A451"
INK = "#111827"
GREY = "#6B7280"
LIGHT = "#C7CCD4"
PALE = "#E6F4EC"

plt.rcParams.update({
    "svg.fonttype": "none",
    "font.family": "Inter",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.titleweight": "600",
    "axes.labelsize": 9,
    "axes.edgecolor": GREY,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "xtick.color": GREY,
    "ytick.color": GREY,
    "legend.fontsize": 8,
    "legend.frameon": False,
    "figure.dpi": 100,
})
MONO = {"family": "JetBrains Mono"}


def save(fig, name: str):
    fig.savefig(FIG / name, format="svg", bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def fig_compression():
    t = S["compression"]["table"]
    samples = ["kv-128", "kv-512", "kv-2048", "act-2048", "control-gaussian"]
    labels = ["KV\n128 tok", "KV\n512 tok", "KV\n2048 tok", "Activation\n2048 tok", "Gaussian\ncontrol"]
    codecs = ["raw-zstd3", "bytesplit-zstd3", "bytesplit-zstd9", "bytesplit-lzma"]
    cnames = ["zstd-3 on raw bf16", "byte-split + zstd-3", "byte-split + zstd-9", "byte-split + lzma-6"]
    colors = [LIGHT, GREEN, GREEN2, INK]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.2), gridspec_kw={"width_ratios": [3, 2]})
    x = np.arange(len(samples))
    w = 0.2
    for i, (c, cn, col) in enumerate(zip(codecs, cnames, colors)):
        vals = [next(r["ratio"] for r in t if r["sample"] == s and r["codec"] == c) for s in samples]
        bars = a1.bar(x + (i - 1.5) * w, vals, w, label=cn, color=col)
        for b, v in zip(bars, vals):
            a1.text(b.get_x() + b.get_width() / 2, v + 0.015, f"{v:.2f}", ha="center", va="bottom", fontsize=6.5, color=INK, **MONO)
    a1.axhline(1.0, color=GREY, lw=0.6, ls=":")
    a1.set_xticks(x, labels, rotation=0, fontsize=7.5)
    a1.set_ylabel("Lossless compression ratio (bf16)")
    a1.set_ylim(0.9, 2.15)
    a1.set_title("A. Ratio, bit-exact round trip verified")
    a1.legend(loc="upper left", ncol=2, fontsize=7)
    # throughput panel for kv-2048
    rows = [next(r for r in t if r["sample"] == "kv-2048" and r["codec"] == c) for c in codecs]
    enc = [r["enc_MBps"] for r in rows]
    dec = [r["dec_MBps"] for r in rows]
    e1 = [r["enc_MBps"] - r["enc_q1"] for r in rows]
    e3 = [r["enc_q3"] - r["enc_MBps"] for r in rows]
    y = np.arange(len(codecs))
    a2.barh(y + 0.18, enc, 0.34, left=0.5, color=GREEN, label="encode", xerr=[e1, e3], error_kw={"ecolor": INK, "lw": 0.7})
    a2.barh(y - 0.18, dec, 0.34, left=0.5, color=LIGHT, label="decode")
    a2.set_xscale("log")
    a2.set_xlim(0.5, 3000)
    a2.set_yticks(y, cnames, fontsize=7.5)
    a2.invert_yaxis()
    a2.set_xlabel("MB/s on the authoring host (2 vCPU), median of 30")
    a2.set_title("B. Throughput, KV 2048 tok")
    a2.legend(loc="lower right")
    for yy, v in zip(y, enc):
        a2.text(v * 1.08, yy + 0.18, f"{v:.0f}", va="center", fontsize=6.5, color=INK, **MONO)
    save(fig, "fig_compression.svg")


def fig_keying():
    k = S["keying"]
    pc = k["per_chunk"]
    xs = [p["chunk_tokens"] for p in pc]
    med = [p["us_median"] for p in pc]
    lo = [p["us_median"] - p["us_q1"] for p in pc]
    hi = [p["us_q3"] - p["us_median"] for p in pc]
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    ax.errorbar(xs, med, yerr=[lo, hi], fmt="o-", color=GREEN, ecolor=INK, capsize=3, lw=1.2, ms=4)
    for x, m in zip(xs, med):
        ax.annotate(f"{m:.1f} us", (x, m), textcoords="offset points", xytext=(8, -3), fontsize=7, color=INK, ha="left", **MONO)
    ax.set_xscale("log", base=2)
    ax.set_xticks(xs, [str(x) for x in xs])
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("Tokens per chunk")
    ax.set_ylabel("Time per chunk key (us), median and IQR of 30")
    ch = k["chain"]
    ax.set_title(f"HMAC-SHA256 chunk keying cost; 4096-token chain in 64-token chunks: {ch['us_median']/1e3:.2f} ms", pad=10, fontsize=9)
    ax.set_ylim(0, max(med) * 1.3)
    save(fig, "fig_keying.svg")


def fig_admission():
    a = S["admission"]
    floors = a["assumptions"]["class_floors_bytes"]
    fracs = a["assumptions"]["usable_fractions"]
    w27 = a["kpi_27b_weights_GiB"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.1), gridspec_kw={"width_ratios": [3, 2]})
    # Panel A: usable RAM of trio and trio+hub vs 27B weight bytes
    names = ["Air", "Mini", "Clip"]
    bottoms = np.zeros(len(fracs) * 2)
    xlab = []
    cols = {"Air": LIGHT, "Mini": GREEN2, "Clip": GREEN, "Hub 16 GB": INK}
    groups = []
    for f in fracs:
        groups.append((f, False))
        groups.append((f, True))
    x = np.arange(len(groups))
    for n in names + ["Hub 16 GB"]:
        vals = []
        for f, hub in groups:
            if n == "Hub 16 GB":
                vals.append(16e9 * f / 2 ** 30 if hub else 0)
            else:
                vals.append(floors[n] * f / 2 ** 30)
        a1.bar(x, vals, 0.6, bottom=bottoms, color=cols[n], label=n)
        bottoms += np.array(vals)
    for i, (f, hub) in enumerate(groups):
        xlab.append(f"{int(f*100)}%\n{'trio+hub' if hub else 'trio'}")
        a1.text(i, bottoms[i] + 0.3, f"{bottoms[i]:.1f}", ha="center", fontsize=7, color=INK, **MONO)
    a1.axhline(w27, color="#B91C1C", lw=1.2, ls="--")
    a1.text(-0.3, w27 + 0.4, f"27.8B Q4 weights {w27:.1f} GiB", ha="left", fontsize=7.5, color="#B91C1C")
    a1.set_xticks(x, xlab, fontsize=7.5)
    a1.set_ylabel("Usable RAM, GiB (floors x usable fraction)")
    a1.set_title("A. Aggregate usable RAM at public class floors vs the 27.8B demo model")
    a1.set_ylim(0, max(bottoms) * 1.45)
    a1.legend(loc="upper left", ncol=4, fontsize=7)
    # Panel B: Clip-class nodes needed
    cc = a["clip_nodes_needed_for_27b"]
    for ctx, col in [(2048, GREEN), (8192, INK)]:
        pts = [(c["usable_fraction"], c["clip_nodes_needed"]) for c in cc if c["context_tokens"] == ctx]
        a2.plot([p[0] * 100 for p in pts], [p[1] for p in pts], "o-", color=col, label=f"context {ctx}")
        for p in pts:
            a2.annotate(str(p[1]), (p[0] * 100, p[1]), textcoords="offset points", xytext=(5, 4), fontsize=7, color=col, **MONO)
    a2.set_xlabel("Usable fraction of the 6 GB Clip floor (%)")
    a2.set_ylabel("Clip-class nodes to place 27.8B")
    a2.set_title("B. Nodes needed, first-fit contiguous")
    a2.set_ylim(0, max(c["clip_nodes_needed"] or 0 for c in cc) + 2)
    a2.legend(loc="upper right")
    save(fig, "fig_admission.svg")


def fig_place():
    p = S["place"]
    grid = [g for g in p["grid"] if g["geometry"].startswith("27.8B")]
    links = sorted({g["link_mbps"] for g in grid})
    fig, ax = plt.subplots(figsize=(6.0, 3.3))
    for P, col in [(50, LIGHT), (100, GREY), (500, GREEN2), (2000, GREEN)]:
        yc = [next(g["crossover_tokens_compressed"] for g in grid if g["link_mbps"] == l and g["prefill_tok_s"] == P) for l in links]
        yu = [next(g["crossover_tokens_uncompressed"] for g in grid if g["link_mbps"] == l and g["prefill_tok_s"] == P) for l in links]
        ax.plot(links, [v if v else np.nan for v in yc], "o-", color=col, label=f"prefill {P} tok/s, compressed", ms=3.5)
        ax.plot(links, [v if v else np.nan for v in yu], "s--", color=col, ms=3, alpha=0.7, label=f"prefill {P} tok/s, uncompressed")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(links, [str(l) for l in links])
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("Effective link payload rate (Mb/s), assumed")
    ax.set_ylabel("Crossover prefix L* (tokens); transfer wins above")
    ax.set_title(f"PLACE crossover, 27.8B geometry (64 KiB/token), ratio {p['inputs']['measured_ratio_bytesplit_zstd3_kv2048']:.2f} measured")
    ax.legend(ncol=4, fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, -0.22))
    ax.text(links[0], ax.get_ylim()[0] * 1.3, "missing points: recompute always wins", fontsize=7, color=GREY)
    save(fig, "fig_place.svg")


def fig_lora():
    l = S["lora"]
    rows = [r for r in l["rows"] if r["duty_cycle"] == 0.1]
    presets = ["ShortTurbo", "ShortFast", "MediumFast", "LongFast", "LongModerate"]
    msgs = ["presence_beacon", "lease_heartbeat", "revocation_notice", "capability_advert", "max_payload"]
    mlabel = ["presence 24 B", "heartbeat 48 B", "revocation 64 B", "advert 160 B", "max 239 B"]
    cols = [PALE, GREEN2, GREEN, GREY, INK]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.1), gridspec_kw={"width_ratios": [3, 2]})
    x = np.arange(len(presets))
    w = 0.16
    for i, (m, ml, c) in enumerate(zip(msgs, mlabel, cols)):
        vals = [next(r["t_air_ms"] for r in rows if r["preset"] == p and r["message"] == m) for p in presets]
        a1.bar(x + (i - 2) * w, vals, w, color=c, label=ml, edgecolor=GREY if c == PALE else None, lw=0.4)
    a1.set_yscale("log")
    a1.set_xticks(x, presets, fontsize=7.5)
    a1.set_ylabel("Time on air (ms), log")
    a1.set_title("A. Airtime per control message (16-byte header included)")
    a1.legend(ncol=3, fontsize=6.5, loc="upper left")
    hb = l["heartbeat_budgets"]
    for preset, col, mk in [("LongFast", INK, "o"), ("MediumFast", GREY, "s"), ("ShortFast", GREEN, "^")]:
        for dc, ls in [(0.1, "-"), (0.01, "--")]:
            pts = [(b["heartbeat_interval_s"], b["nodes_supported"]) for b in hb if b["preset"] == preset and b["duty_cycle"] == dc]
            a2.plot([p[0] for p in pts], [max(p[1], 0.5) for p in pts], marker=mk, ls=ls, color=col, ms=3.5,
                    label=f"{preset} @{int(dc*100)}% duty")
    a2.set_xscale("log")
    a2.set_yscale("log")
    a2.set_xticks([5, 20, 60, 300], ["5", "20", "60", "300"])
    a2.xaxis.set_minor_formatter(NullFormatter())
    a2.set_xlabel("Lease heartbeat interval (s)")
    a2.set_ylabel("Nodes whose heartbeats fit the duty cycle")
    a2.set_title("B. Heartbeat capacity (48 B)")
    a2.legend(fontsize=6, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.25))
    save(fig, "fig_lora.svg")


def fig_churn():
    c = S["churn"]
    cfgs = [x for x in c["configs"] if x["mean_up_s"] == 600.0]
    ttls = sorted({x["lease_ttl_s"] for x in cfgs})
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(9.6, 2.9))

    def val(ttl, cache, key):
        s = next(x for x in cfgs if x["lease_ttl_s"] == ttl and x["decision_cache_s"] == cache)["summary"][key]
        return s["median"], s["median"] - s["q1"], s["q3"] - s["median"]

    x = np.arange(len(ttls))
    for i, (key, lab, col) in enumerate([("stale_completions_unfenced_accepted", "unfenced: stale completions accepted", "#B91C1C"),
                                         ("stale_completions_fenced_rejected", "fenced: same completions rejected", GREEN)]):
        v = [val(t, 30.0, key) for t in ttls]
        a1.bar(x + (i - 0.5) * 0.36, [m for m, _, _ in v], 0.36, color=col, label=lab,
               yerr=[[q1 for _, q1, _ in v], [q3 for _, _, q3 in v]], error_kw={"ecolor": INK, "lw": 0.7})
    a1.set_xticks(x, [f"TTL {int(t)} s" for t in ttls])
    a1.set_ylabel("Count per 2 h run, median and IQR (30 seeds)")
    a1.set_title("A. Lease fencing")
    a1.set_ylim(0, max(val(t, 30.0, "stale_completions_unfenced_accepted")[0] + val(t, 30.0, "stale_completions_unfenced_accepted")[2] for t in ttls) * 1.6)
    a1.legend(fontsize=6.5, loc="upper right")
    for i, (cache, lab, col) in enumerate([(300.0, "cached decision, 300 s", "#B91C1C"), (30.0, "cached decision, 30 s", GREY), (0.0, "live graph at consumption", GREEN)]):
        v = [val(t, cache, "stale_auth_cached" if cache > 0 else "stale_auth_live") for t in ttls]
        a2.bar(x + (i - 1) * 0.27, [m for m, _, _ in v], 0.27, color=col, label=lab,
               yerr=[[q1 for _, q1, _ in v], [q3 for _, _, q3 in v]], error_kw={"ecolor": INK, "lw": 0.7})
    a2.set_xticks(x, [f"TTL {int(t)} s" for t in ttls])
    a2.set_ylabel("Accesses authorized after grant path died")
    a2.set_title("B. Consumption-time validity")
    a2.set_ylim(0, max(val(t, 300.0, "stale_auth_cached")[0] + val(t, 300.0, "stale_auth_cached")[2] for t in ttls) * 1.6)
    a2.legend(fontsize=6.5, loc="upper right")
    v = [val(t, 30.0, "detect_latency_median") for t in ttls]
    a3.errorbar(ttls, [m for m, _, _ in v], yerr=[[q1 for _, q1, _ in v], [q3 for _, _, q3 in v]], fmt="o-", color=GREEN, ecolor=INK, capsize=3)
    a3.plot(ttls, ttls, ls=":", color=GREY, lw=0.8)
    a3.text(ttls[-1], ttls[-1] - 8, "y = TTL", fontsize=7, color=GREY, ha="right")
    a3.set_xlabel("Lease TTL (s), heartbeat 5 s")
    a3.set_ylabel("Departure detection latency (s)")
    a3.set_title("C. Detection latency")
    save(fig, "fig_churn.svg")


if __name__ == "__main__":
    fig_compression()
    fig_keying()
    fig_admission()
    fig_place()
    fig_lora()
    fig_churn()
