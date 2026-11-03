"""Build the paper HTML from summary.json and the verified reference table.

Every number comes from exp/results/summary.json via the S dict. Citations are
[@key]; numbering is by first use. Run: python3 wp/build.py -> wp/paper.src.html
then node wp/katex_render.cjs wp/paper.src.html wp/paper.html.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = json.loads((ROOT / "exp" / "results" / "summary.json").read_text())
REFS_RAW = json.loads((ROOT / "wp" / "refs_raw.json").read_text())
FIG = ROOT / "wp" / "figures"

VERSION = "v1.0.1"
DATE = "2026-11-03"
TITLE = "THOX MeshStack: Capacity-Priced Pipeline Sharding, Grant-Gated KV Transfer and Lease-Fenced Device Roles for a Private Household Mesh"
SHORT = "THOX MeshStack: sharding, grant-gated KV and lease-fenced roles"

# ----------------------------------------------------------------------------
# References: arXiv entries come verbatim from refs_raw.json (fetched live from
# the arXiv export API on 2026-11-03). Non-arXiv entries were opened live the
# same day; titles and authors are copied from those pages.
# ----------------------------------------------------------------------------
MANUAL_REFS = {
    "wireguard": {"authors": ["Jason A. Donenfeld"], "title": "WireGuard: Next Generation Kernel Network Tunnel", "venue": "NDSS 2017", "url": "https://www.wireguard.com/papers/wireguard.pdf"},
    "borg": {"authors": ["Abhishek Verma", "Luis Pedrosa", "Madhukar Korupolu", "David Oppenheimer", "Eric Tune", "John Wilkes"], "title": "Large-scale cluster management at Google with Borg", "venue": "EuroSys 2015", "url": "https://research.google/pubs/large-scale-cluster-management-at-google-with-borg/"},
    "omega": {"authors": ["Malte Schwarzkopf", "Andy Konwinski", "Michael Abd-El-Malek", "John Wilkes"], "title": "Omega: flexible, scalable schedulers for large compute clusters", "venue": "EuroSys 2013", "url": "https://research.google/pubs/omega-flexible-scalable-schedulers-for-large-compute-clusters/"},
    "chubby": {"authors": ["Mike Burrows"], "title": "The Chubby Lock Service for Loosely-Coupled Distributed Systems", "venue": "OSDI 2006, pp. 335-350", "url": "https://www.usenix.org/legacy/event/osdi06/tech/burrows.html"},
    "orca": {"authors": ["Gyeong-In Yu", "Joo Seong Jeong", "Geon-Woo Kim", "Soojeong Kim", "Byung-Gon Chun"], "title": "Orca: A Distributed Serving System for Transformer-Based Generative Models", "venue": "OSDI 2022", "url": "https://www.usenix.org/conference/osdi22/presentation/yu"},
    "k8slease": {"authors": ["The Kubernetes Authors"], "title": "Leases (Kubernetes documentation, Cluster Architecture)", "venue": "kubernetes.io, accessed 2026-11-03", "url": "https://kubernetes.io/docs/concepts/architecture/leases/"},
    "rfc2104": {"authors": ["Hugo Krawczyk", "Mihir Bellare", "Ran Canetti"], "title": "HMAC: Keyed-Hashing for Message Authentication", "venue": "RFC 2104, IETF, 1997", "url": "https://www.rfc-editor.org/rfc/rfc2104"},
    "fips180": {"authors": ["National Institute of Standards and Technology"], "title": "Secure Hash Standard (SHS), FIPS PUB 180-4", "venue": "NIST, 2015", "url": "https://csrc.nist.gov/pubs/fips/180-4/upd1/final"},
    "rfc8878": {"authors": ["Yann Collet", "Murray Kucherawy (Ed.)"], "title": "Zstandard Compression and the 'application/zstd' Media Type", "venue": "RFC 8878, IETF, 2021", "url": "https://www.rfc-editor.org/rfc/rfc8878"},
    "meshalgo": {"authors": ["Meshtastic project"], "title": "Mesh Broadcast Algorithm (Meshtastic documentation)", "venue": "meshtastic.org, accessed 2026-11-03", "url": "https://meshtastic.org/docs/overview/mesh-algo/"},
    "meshenc": {"authors": ["Meshtastic project"], "title": "Meshtastic Encryption (Meshtastic documentation)", "venue": "meshtastic.org, accessed 2026-11-03", "url": "https://meshtastic.org/docs/overview/encryption/"},
    "meshradio": {"authors": ["Meshtastic project"], "title": "Radio Settings: modem presets (Meshtastic documentation)", "venue": "meshtastic.org, accessed 2026-11-03", "url": "https://meshtastic.org/docs/overview/radio-settings/"},
    "sx1262": {"authors": ["Semtech Corporation"], "title": "SX1262 Long Range, Low Power, sub-GHz LoRa RF Transceiver: product page and data sheet (LoRa packet structure, time on air)", "venue": "semtech.com, accessed 2026-11-03", "url": "https://www.semtech.com/products/wireless-rf/lora-connect/sx1262"},
    "exo": {"authors": ["exo-explore contributors"], "title": "exo: Run frontier AI locally (repository)", "venue": "GitHub, accessed 2026-11-03", "url": "https://github.com/exo-explore/exo"},
    "qwenmodel": {"authors": ["Qwen team, Alibaba Cloud"], "title": "Qwen/Qwen2.5-0.5B-Instruct model repository (model.safetensors, config.json)", "venue": "Hugging Face, accessed 2026-11-03", "url": "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct"},
    "thoxA": {"authors": ["Craig Ross", "Tommy Xaypanya"], "title": "Storage Aware Parallel Inference for THOX MeshStack Devices", "venue": "THOX.ai LLC internal document THOX-RP-MESH-2026-1101, edition 1.1.0, 2026-11-01 (confidential, unpublished)", "url": ""},
    "thoxB": {"authors": ["THOX.ai"], "title": "MeshStack v2: Distributed Inference for the Private Device Mesh (design paper v1.0.0)", "venue": "THOX.ai internal design paper, 2026-10-30 (unpublished; records decisions D1-D23, the Qwen3.6-27B demo geometry and the fleet engine spike)", "url": ""},
    "thoxOS": {"authors": ["THOX.ai"], "title": "ThoxOS: An Open Kernel and Operating System for Local-First AI (technical whitepaper v0.1.0)", "venue": "THOX.ai, 2026-10-31 (unpublished; source of the E2/P4/P6 class floors and the open/paid line)", "url": ""},
    "thoxRole": {"authors": ["THOX.ai"], "title": "Auto Device Role Mode for THOX MeshStack (research note)", "venue": "THOX.ai internal research note, October 2026 (unpublished)", "url": ""},
    "thoxLossless": {"authors": ["THOX.ai"], "title": "MeshStack v2: Architecture and Methodology for Lossless Distributed Inference in Private Local AI Meshes (draft note)", "venue": "THOX.ai internal draft, October 2026 (unpublished)", "url": ""},
}

CITED: list[str] = []


def ref_entry(key: str) -> dict:
    if key in REFS_RAW and REFS_RAW[key]["status"] == "resolved":
        r = REFS_RAW[key]
        return {"authors": r["authors"], "title": r["title"],
                "venue": f"arXiv:{r['arxiv_id']}, first posted {r['published'][:10]}, version inspected {r['updated'][:10]}" + (f"; {r['journal_ref']}" if r.get("journal_ref") else ""),
                "url": r["url"]}
    if key in MANUAL_REFS:
        return MANUAL_REFS[key]
    raise KeyError(f"unknown citation key {key}")


def cite(text: str) -> str:
    def repl(m):
        keys = [k.strip().lstrip("@") for k in m.group(1).split(";")]
        nums = []
        for k in keys:
            ref_entry(k)
            if k not in CITED:
                CITED.append(k)
            nums.append(str(CITED.index(k) + 1))
        return '<span class="cite">[' + ", ".join(nums) + "]</span>"
    return re.sub(r"\[@([^\]]+)\]", repl, text)


# ----------------------------------------------------------------------------
# HTML helpers
# ----------------------------------------------------------------------------
OUT: list[str] = []


def p(text: str):
    OUT.append(f"<p>{cite(text)}</p>")


def h2(num: str, text: str, anchor: str):
    OUT.append(f'<h2 id="{anchor}"><span class="num">{num}</span>{text}</h2>')


def h3(text: str):
    OUT.append(f"<h3>{text}</h3>")


def eq(tex: str, display: bool = True):
    OUT.append(f'<div class="eq"><span class="katex-src" data-display="{1 if display else 0}">{html.escape(tex)}</span></div>')


def ieq(tex: str) -> str:
    return f'<span class="katex-src" data-display="0">{html.escape(tex)}</span>'


def table(headers: list[str], rows: list[list[str]], caption: str = "", cls: str = ""):
    th = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{cite(c)}</td>" for c in r) + "</tr>" for r in rows)
    cap = f"<caption>{cite(caption)}</caption>" if caption else ""
    OUT.append(f'<table class="{cls}">{cap}<thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>')


def figure(svg: str, num: int, caption: str):
    content = (FIG / svg).read_text()
    content = re.sub(r"<\?xml[^>]*\?>", "", content)
    content = re.sub(r"<!DOCTYPE[^>]*>", "", content)
    OUT.append(f'<figure id="fig{num}"><div class="figwrap">{content}</div><figcaption><b>Figure {num}.</b> {cite(caption)}</figcaption></figure>')


def callout(title: str, body: str, kind: str = "note"):
    OUT.append(f'<div class="callout {kind}"><div class="ct">{title}</div><div>{cite(body)}</div></div>')


def algo(title: str, lines: list[str]):
    body = "\n".join(html.escape(l) for l in lines)
    OUT.append(f'<div class="algo"><div class="at">{title}</div><pre>{body}</pre></div>')


def ul(items: list[str]):
    OUT.append("<ul>" + "".join(f"<li>{cite(i)}</li>" for i in items) + "</ul>")


def ol(items: list[str]):
    OUT.append("<ol>" + "".join(f"<li>{cite(i)}</li>" for i in items) + "</ol>")


def fmt(x: float, nd: int = 2) -> str:
    return f"{x:,.{nd}f}"


# ----------------------------------------------------------------------------
# Numbers (all from summary.json)
# ----------------------------------------------------------------------------
C = S["compression"]; K = S["keying"]; A = S["admission"]; P = S["place"]; L = S["lora"]; CH = S["churn"]
ratio = C["kpi_ratio_bytesplit_zstd3_kv2048"]
ratio_raw = C["kpi_ratio_raw_zstd3_kv2048"]
ratio_best = C["kpi_best_ratio_kv2048"]
enc = C["kpi_enc_MBps_bytesplit_zstd3_kv2048"]
dec = C["kpi_dec_MBps_bytesplit_zstd3_kv2048"]
hi_ratio = C["kpi_hi_plane_ratio_kv2048"]
ctrl_ratio = C["kpi_control_gaussian_ratio"]
act_ratio = C["kpi_act_ratio_bytesplit_zstd3_2048"]
kv_pt = C["kv_bytes_per_token_bf16"]
kv4096 = C["kv_MiB_4096_tokens_bf16"]
us64 = K["kpi_us_per_64_token_chunk"]
chain_ms = K["kpi_chain_4096_ms"]
keys_s = K["kpi_keys_per_second_64"]
trio_floor_gb = A["kpi_trio_total_floor_GB"]
w27 = A["kpi_27b_weights_GiB"]
clip_needed = A["clip_nodes_needed_for_27b"]
lf_hb = L["kpi_longfast_heartbeat_ms"]; sf_hb = L["kpi_shortfast_heartbeat_ms"]
lf_max = L["kpi_longfast_maxpayload_ms"]; sf_max = L["kpi_shortfast_maxpayload_ms"]
kv_hours = L["kpi_4096_kv_MiB_over_shortfast_hours"]
sess = CH["kpi_sessions_median"]; repl = CH["kpi_replans_median"]
stale_unf = CH["kpi_stale_unfenced_median"]; stale_fenced = CH["kpi_stale_fenced_rejected_median"]
auth30 = CH["kpi_stale_auth_cached30_median"]; auth300 = CH["kpi_stale_auth_cached300_median"]; authlive = CH["kpi_stale_auth_live_median"]
det20 = CH["kpi_detect_latency_ttl20"]; det60 = CH["kpi_detect_latency_ttl60"]; det10 = CH["kpi_detect_latency_ttl10"]
x27_100_100 = P["kpi_27b_100mbps_P100_compressed"]; x27_100_100u = P["kpi_27b_100mbps_P100_uncompressed"]
x27_100_500 = P["kpi_27b_100mbps_P500_compressed"]; x27_800_500 = P["kpi_27b_800mbps_P500_compressed"]
xq_100_500 = P["kpi_qwen_100mbps_P500_compressed"]
geom = C["geometry"]
samp2048 = next(s for s in C["samples"] if s["tokens"] == 2048)


def xo(v):
    return "none (recompute always wins)" if v is None else f"{v:,.0f} tokens"


# ----------------------------------------------------------------------------
# Cover
# ----------------------------------------------------------------------------
ABSTRACT = (
    "A household owns several small computers that are idle most of the day and together hold more memory than any one of them. "
    "Today every serving path in the THOX fleet routes a whole request to one node that already holds a whole model, so the largest "
    "model a home can run is bounded by its largest device. This paper reconciles two THOX design lineages for MeshStack&trade;, "
    "the private device mesh, into one specification and tests the parts of it that can be tested without a device fleet. The "
    "design has four mechanisms: a capacity-priced pipeline sharder whose two-domain admission rule fails closed; a KV cache "
    "organised as a parent-chained, HMAC-keyed graph whose cross-node transfer is gated by both a cost model and a live authority "
    "path; a lease-fenced role layer that keeps device owners sovereign under routine churn; and a control plane that degrades to a "
    "239-byte LoRa carrier when the LAN is gone. We report measured results for the mechanisms that run on a general host: lossless "
    f"compression of real bfloat16 KV state from Qwen2.5-0.5B reaches {fmt(ratio)}x with a byte-split zstd codec at {fmt(enc,0)} MB/s "
    f"encode on a 2-vCPU host, with every round trip verified bit-exact; parent-chained HMAC keying costs {fmt(us64,1)} microseconds "
    f"per 64-token chunk. We report calculated results where the inputs are public: at the published THOX class floors (2, 4 and 6 GB) "
    f"a three-device mesh cannot place the 27.8B demo model used by the current reference implementation at any usable fraction we "
    "tried, which contradicts the reference demo's fixtures and is the paper's central negative result. A simulation of the lease "
    "protocol shows that epoch fencing rejects every stale completion and that consumption-time validity removes the stale "
    "authorisation window that a cached decision leaves open. No engine throughput, no cross-host run and no device measurement is "
    "claimed; the evaluation protocol that would produce those numbers is stated with its claim gate."
)

CONTENTS = [
    ("Executive summary", "exec"), ("1. Introduction", "intro"), ("2. Background and related work", "related"),
    ("3. System and threat model", "model"), ("4. Design", "design"), ("5. Implementation", "impl"),
    ("6. Evaluation", "eval"), ("7. Discussion and limitations", "limits"), ("8. Conclusion", "concl"),
    ("9. Roadmap and decisions for the founders", "roadmap"), ("Appendix A. Reproducibility", "appA"),
    ("Appendix B. Notation", "appB"), ("Appendix C. Authorship and disclosure", "appC"), ("References", "refs"),
]

cover = f"""
<section class="cover">
  <div class="cover-inner">
    <div class="eyebrow"><span>THOX.ai Research &middot; Technical report {VERSION} &middot; {DATE}</span><span class="pill">Preprint, not peer reviewed</span></div>
    <h1>{TITLE}</h1>
    <p class="deck">Two design lineages reconciled into one specification, with the parts that run on a general host measured, the parts that depend on public device floors calculated, and the parts that need a fleet stated as a gated protocol.</p>
    <p class="byline">THOX.ai Research &middot; Authors: Craig Ross, Chief Executive Officer, and Tommy Xaypanya, CTO and Co-Founder (corresponding author), THOX.ai LLC, Cedar Park, Texas &middot; ORCID 0009-0000-4425-9565</p>
    <div class="abstract"><div class="ct">Abstract</div><p>{ABSTRACT}</p></div>
    <div class="contents"><div class="ct">Contents</div><ol>{''.join(f'<li><a href="#{a}">{t}</a></li>' for t, a in CONTENTS)}</ol></div>
    <div class="cover-foot">Your AI. Your Data. Your Rules.&trade; &middot; THOX&reg;, ThoxOS&trade;, MeshStack&trade; and ThoxWork&trade; are marks of THOX.ai LLC.</div>
  </div>
</section>
"""

# ----------------------------------------------------------------------------
# Executive summary
# ----------------------------------------------------------------------------
OUT.append('<section class="paper-body">')
h2("", "Executive summary", "exec")
p("MeshStack&trade; exists to spend a household's aggregate device memory on models no single device can hold. Two THOX design "
  "documents answer how: the storage-aware parallelism paper of edition 1.1.0 [@thoxA], which recommends whole-request placement first "
  "and pipeline distribution only after measurement, and the MeshStack v2 design paper [@thoxB], which fixes pipeline sharding as the "
  "mesh form and adds a KV graph, a secrets graph and a scheduler cost form. A third note proposes expert parallelism and speculative "
  "decoding on top [@thoxLossless], and a fourth proposes a lease-based device role layer [@thoxRole]. They agree on principles and "
  "disagree on sequencing, control-plane ownership and what the device floors permit. This paper is the reconciliation, and it adds "
  "the evidence that could be produced without a fleet.")
kpis = [
    (f"{fmt(ratio)}&times;", f"lossless bf16 KV compression, byte-split zstd-3, 2048 tokens, real Qwen2.5-0.5B state (unit Gaussian control {fmt(ctrl_ratio)}x)", "measured"),
    (f"{fmt(us64,1)} &micro;s", "per 64-token parent-chained HMAC-SHA256 chunk key; 4096-token chain " + fmt(chain_ms, 2) + " ms", "measured"),
    ("Unplaceable", f"27.8B Q4 demo model on an Air+Mini+Clip trio at the public floors ({trio_floor_gb:.0f} GB total vs {fmt(w27,1)} GiB weights)", "calculated"),
    (f"{stale_fenced:.0f} / {stale_fenced:.0f}", "stale completions rejected by epoch fencing per 2-hour churn run (median of 30 seeds); " + f"{authlive:.0f} stale authorisations with consumption-time validity vs {auth300:.0f} with a 300 s cache", "simulated"),
]
OUT.append('<div class="kpis">' + "".join(f'<div class="kpi"><div class="kv">{v}</div><div class="kl">{l}</div><div class="kt">{t}</div></div>' for v, l, t in kpis) + "</div>")
callout("Product implications",
        "First, the demo fixtures in the current reference implementation (a 9.6 GiB usable anchor) describe a host, not a THOX device; "
        "at the published class floors the trio needs a hub for anything in the 27B class, so the first shipped MeshStack capability "
        "must be stated as device-plus-hub, not device-only. Second, lossless wire compression of KV and activations is worth about "
        f"{fmt(ratio)}x, and a unit Gaussian control gets {fmt(ctrl_ratio)}x with the same codec, so the gain is mostly exponent concentration; the PLACE "
        "cost model should use a measured ratio per model, never a constant, and the lossless-transport note's expectation of large gains is not supported. Third, the role and lease layer proposed outside the v2 paper fits the v2 secrets "
        "graph without a second control plane: a lease is a grant with an epoch and a TTL. Fourth, a LoRa auxiliary mesh can carry "
        "presence, heartbeats and revocation for a household-sized mesh, and nothing else; it is a control-plane fallback, not a transport.",
        "green")

# ----------------------------------------------------------------------------
# 1 Introduction
# ----------------------------------------------------------------------------
h2("1", "Introduction", "intro")
p("The THOX device line (ThoxAir, ThoxMini, ThoxClip, the ThoxKey companion and desktop hosts) runs ThoxOS&trade;, a local-first "
  "operating system whose public class floors are 2 GB, 4 GB and 6 GB of RAM for the E2, P4 and P6 classes [@thoxOS]. A fleet audit of "
  "34 MeshStack-related repositories on 2026-10-30 found that every serving path routes a whole request to a node that already holds "
  "the whole model [@thoxB]. That pattern is correct for models that fit and useless for models that do not. The design question is "
  "how to pool the memory of a few small, churn-prone, owner-controlled devices without pretending the home is a datacenter.")
p("Published systems answer the capacity half of that question. prima.cpp runs 30B to 70B models on heterogeneous home clusters with "
  "pipelined-ring parallelism and disk offload [@primacpp]; TPI-LLM argues for tensor parallelism on low-resource edge devices "
  "[@tpillm]; EdgeShard, Galaxy and LinguaLinked partition models across cooperating edge devices [@edgeshard; @galaxy; @lingualinked]; "
  "Petals and BloomBee run pipelines over the internet with checkpoint-and-replay recovery and lossless activation compression "
  "[@petals; @petalsinternet; @bloombee]; exo is the best-known hobbyist implementation [@exo]. None of them answers the authority half: "
  "who may move a household's KV state, when a departed device's permissions die, and how an owner's foreground work stays ahead of "
  "mesh jobs. That half is where THOX's design differs, and it is where this paper spends its design effort.")
p("Within THOX the record is split. Lineage A [@thoxA] is a source-grounded architecture over five parallelism families with a "
  "calculator and an unexecuted physical protocol; it recommends whole-request placement and local staging first. Lineage B [@thoxB] "
  "fixes pipeline sharding, a five-tier KV graph with grant-gated transfer, a secrets grant graph and a Dynamo-style cost form, with a "
  "Python reference implementation whose root suite passed 63 tests at HEAD b01bc03 after a recorded admission regression. Two notes "
  "add a lossless-transport proposal with expert parallelism [@thoxLossless] and a lease-based Auto Device Role Mode [@thoxRole]. The "
  "contributions of this paper are:")
ol([
    "<b>A reconciled specification</b> (Section 4) that keeps lineage B's mechanisms, adopts lineage A's sequencing (whole-request "
    "placement is the degenerate one-stage case of the sharder and ships first), folds the lease and role proposal into the secrets "
    "graph as epoch-bearing grants, and rejects expert parallelism and speculative decoding for generation 1 with stated reasons.",
    f"<b>Measured lossless wire behaviour</b> (Section 6.1, 6.2): on real bfloat16 KV and activation tensors from a public model the "
    f"byte-split zstd codec reaches {fmt(ratio)}x on KV and {fmt(act_ratio)}x on layer-boundary activations with bit-exact round trips, "
    f"and parent-chained HMAC keying costs {fmt(us64,1)} microseconds per 64-token chunk. These numbers bound the PLACE cost model and the KV "
    "graph's overhead from below on a general host.",
    "<b>A negative capacity result</b> (Section 6.3): at the public class floors, with first-fit contiguous placement and stated usable "
    "fractions, the reference demo's 27.8B Q4 geometry is Unplaceable on an Air+Mini+Clip trio and needs either a hub or a larger "
    f"number of Clip-class nodes ({clip_needed[0]['clip_nodes_needed']} at a {int(clip_needed[0]['usable_fraction']*100)}% usable fraction and 2048-token context).",
    "<b>Protocol evidence by simulation</b> (Section 6.6): epoch fencing rejects every stale completion and consumption-time validity "
    "removes the stale authorisation window, under stated churn distributions, with the departure detection latency tied to the lease TTL.",
    "<b>A control-plane degradation analysis</b> (Section 6.5): the LoRa airtime of each MeshStack control message on every Meshtastic "
    "preset, and the number of nodes whose lease heartbeats fit a regulatory duty cycle.",
])
p("Everything the paper measures ran on the authoring host (2 vCPU, no accelerator) with one 0.5B model. Nothing ran on a THOX device, "
  "nothing ran across two hosts, and no engine throughput is claimed. Section 7 states those limits once more, itemised, and Section 9 "
  "lists the decisions that only the founders can take.")

# ----------------------------------------------------------------------------
# 2 Background and related work
# ----------------------------------------------------------------------------
h2("2", "Background and related work", "related")
h3("2.1 Parallelism forms and why the mesh form is pipeline")
p("Tensor parallelism slices every layer's matrices across workers and needs a collective per layer, which assumes a fast symmetric "
  "interconnect [@megatron]. Pipeline parallelism assigns contiguous layer ranges to stages and moves one activation tensor per token "
  "or micro-batch per boundary. Expert parallelism places experts of a mixture-of-experts layer on different workers and routes "
  "tokens to them [@deepspeedmoe]. Context parallelism partitions sequence or attention state [@ring]. Lineage A translated all five "
  "families into a resource contract and found that only whole-request and pipeline placement are admissible over slow links without "
  "backend support that does not yet exist in the fleet [@thoxA]; lineage B fixed pipeline as the mesh form and tensor as intra-node "
  "only (decision D10) [@thoxB]. TPI-LLM's counter-argument, that tensor parallelism can beat pipeline for single-user edge inference, "
  "holds when links are fast enough for per-layer collectives and memory is the binding constraint [@tpillm]; its evaluation used a "
  "controlled testbed, and the THOX relay and Wi-Fi assumptions of Section 3 do not satisfy its premise. This paper keeps pipeline as "
  "the generation-1 form and records tensor-on-LAN as a measured question for the benchmark wave.")
h3("2.2 KV cache as a movable resource")
p("Datacenter serving systems treat the KV cache as a first-class, tiered, movable object: Mooncake builds a KV-centric disaggregated "
  "architecture [@mooncake], LMCache a KV layer across engines and tiers [@lmcache], CacheBlend reuses precomputed KV at non-prefix "
  "positions by selective recomputation [@cacheblend], CacheGen streams compressed KV over bandwidth-limited links [@cachegen], and "
  "PagedAttention manages KV inside one engine [@pagedattention]. Orca, DistServe and SGLang contribute iteration-level scheduling, "
  "prefill/decode disaggregation and radix-tree prefix reuse [@orca; @distserve; @sglang]. Tutti and SARIA make SSD-backed KV "
  "practical with reload scheduling and persistence selection [@tutti; @saria]. MeshStack borrows the premise and changes three "
  "things: tiers are devices in a home, movement is gated by authority as well as by cost, and mesh-wide prefill/decode "
  "disaggregation is rejected for generation 1 [@thoxB].")
h3("2.3 Lossless compression of KV and activations")
p("Lossless KV compression is a young line: GAAC exploits bfloat16 exponent redundancy with calibrated per-channel codes for "
  "personal devices [@gaac]; SplitZip targets disaggregated serving with ultra-fast codecs [@splitzip]; ZipFusion and others fuse "
  "decompression into attention. BloomBee uses a byte-split layout plus entropy coding for activations over the internet [@bloombee]. "
  "This paper does not design a codec. It measures the simplest construction in that family (byte planes plus a general entropy "
  "coder, Zstandard [@rfc8878]) on real tensors so that the PLACE cost model has a measured ratio instead of a borrowed one, and it "
  "compares against a Gaussian control to show that the gain is a property of the tensors.")
h3("2.4 Schedulers, leases and fencing")
p("Borg and Omega established capability-aware placement with shared state and optimistic concurrency [@borg; @omega]; Chubby and "
  "Kubernetes leases established the renewable lease as the primitive that makes ownership disappear when its holder does "
  "[@chubby; @k8slease]. The Auto Device Role Mode note maps those lessons onto MeshStack: a metadata-only coordinator, a lease with "
  "a fencing epoch, hard filters before scoring, and a strict queue in which owner work is P0 [@thoxRole]. The Dynamo KV Router and "
  "llm-d cost form that lineage B adopts prices prefill by prefix overlap and decode by load [@thoxB]. Kafila plans stage and memory "
  "placement on a trusted set of heterogeneous commodity machines [@kafila]; its fleets are not churn-prone mobile devices.")
h3("2.5 Storage, offload and the edge")
p("FlexGen and LLM in a flash established that disk and flash can extend capacity at a latency cost that depends on the demanded "
  "fraction of weights and on read layout [@flexgen; @flash]; FlashMoE and the SSD-resident MoE work extend that to experts "
  "[@flashmoe; @edge0]. CEMA-Router, Prism, Mesh-Attention and EasyBalance address routing, expert placement, attention locality and "
  "cross-layer balance at datacenter or edge-server scale [@cemarouter; @prism; @meshattention; @easybalance]; the lossless-transport "
  "note cites them as motivation [@thoxLossless], and this paper keeps them in that role: their numbers are theirs, on their hardware. "
  "The stage-level NPU study and the mobile battery study motivate recording dispatch, fallback and energy costs rather than "
  "selecting engines by advertised ratings [@npu; @batteryprice]. InferSlice's reference architecture for SLO-driven inference over a "
  "telco WAN is the closest formal treatment of SLO gates [@inferslice].")
h3("2.6 Positioning")
table(["System", "Setting", "Sharding form", "KV movement", "Authority model", "Owner sovereignty, churn", "Evidence class"], [
    ["prima.cpp [@primacpp]", "home cluster, mixed CPU/GPU, Wi-Fi", "pipelined ring with disk offload", "none across nodes", "none (trusted cluster)", "not modelled", "measured, authors' hardware"],
    ["TPI-LLM [@tpillm]", "low-resource edge devices", "tensor", "none", "none", "not modelled", "measured, authors' testbed"],
    ["EdgeShard / Galaxy [@edgeshard; @galaxy]", "cooperating edge devices", "layer partition / hybrid", "none", "none", "not modelled", "measured, authors' testbed"],
    ["Petals, BloomBee [@petals; @bloombee]", "internet volunteers", "pipeline", "node-local", "none (untrusted peers assumed)", "checkpoint and replay", "measured, authors' deployments"],
    ["Mooncake, LMCache [@mooncake; @lmcache]", "datacenter", "n/a", "tiered, cost-driven", "none", "n/a", "measured, production"],
    ["Kafila [@kafila]", "trusted heterogeneous machines", "pipeline, memory-aware", "none", "trusted set", "not modelled", "measured, authors' fleet"],
    ["MeshStack lineage A [@thoxA]", "THOX devices, SSD hosts", "whole-request first; pipeline later", "session-bound, ephemeral", "leases per request", "fail closed", "calculated; protocol unexecuted"],
    ["MeshStack lineage B [@thoxB]", "THOX private mesh", "contiguous pipeline (D10)", "grant-gated T3 (D9)", "secrets graph, consumption-time", "replan or fail closed (D13)", "reference implementation, plan level"],
    ["Auto Device Role Mode [@thoxRole]", "THOX private mesh", "whole-request routing", "none", "lease with fencing epoch", "P0 owner work, drain", "design note"],
    ["<b>This paper</b>", "THOX private mesh plus LoRa fallback", "contiguous pipeline, one-stage degenerate case first", "grant-gated, cost-gated, measured ratio", "secrets graph with epoch-bearing lease grants", "P0 owner work, fencing, consumption-time validity", "measured on a host, calculated on floors, simulated protocol"],
], "Table 1. Design positioning. Evidence class names what each row's claims rest on; no row's measurements are quoted as THOX results.")

# ----------------------------------------------------------------------------
# 3 System and threat model
# ----------------------------------------------------------------------------
h2("3", "System and threat model", "model")
h3("3.1 Setting")
p("A mesh is the set of nodes under one household's administrative control, reachable over a LAN or a private tailnet built on "
  "WireGuard [@wireguard]. Nodes are E2, P4 and P6 class devices with the public floors of Table 2 [@thoxOS], plus at most a few larger "
  "hub nodes (a desktop, a ThoxKey host). Devices are personal: an owner may close, move or drain one at any moment, and a device "
  "that leaves is a routine event with a routine consequence. Links are shared and variable; a broadcast relay documented under "
  "roughly 50 peers is the current cross-site path [@thoxB]. A LoRa auxiliary mesh on ESP32-class radios running Meshtastic may be "
  "present; its over-the-air packet carries a 16-byte cleartext header and at most 239 bytes of encrypted payload, and its fastest "
  "preset is rated at 21.88 kbit/s [@meshalgo; @meshradio].")
table(["Class", "Device line", "RAM floor", "Storage floor", "On-device model class"], [
    ["E2", "ThoxAir (wireless edge node)", "2 GB", "16 GB flash", "about 1B at 4-bit"],
    ["P4", "ThoxMini (personal edge server)", "4 GB", "32 GB flash", "about 3B, quantised"],
    ["P6", "ThoxClip (clip-on edge compute)", "6 GB", "64 GB flash", "about 3B, quantised"],
], "Table 2. Public THOX compute-class floors as recorded in the ThoxOS whitepaper [@thoxOS]. Floors are category-level definitions, not measurements of shipped hardware; no device is qualified.")
h3("3.2 Requirements")
ol([
    "<b>R1 Capacity truth.</b> A plan admits only when the two-domain inequalities of Section 4.2 hold for every stage; there is no partial admission and Unplaceable is a value, not an exception.",
    "<b>R2 Contiguity.</b> A stage is a contiguous layer range; the activation traffic per token is one frame per stage boundary.",
    "<b>R3 Lossless wire by default.</b> Activation frames and KV bytes cross nodes bit-exact (raw f32 or bf16 with a lossless codec); a lossy transfer tier (FP8/INT8, decision D15 in lineage B) is a labelled opt-in that the benchmark wave must gate, never a default.",
    "<b>R4 Chunk identity.</b> KV chunks are content-addressed by a parent-chained HMAC key bound to the principal's secret and the model fingerprint.",
    "<b>R5 Authority at consumption.</b> A capability is valid only if a live path exists in the grant graph at the moment of use; there is no cached positive decision.",
    "<b>R6 Fencing.</b> Every completion, activation frame and KV transfer carries the lease epoch of its session; anything older than the session's current epoch is rejected.",
    "<b>R7 Owner sovereignty.</b> Hard filters (opt-in, mesh membership, model residency, memory reservation floor, owner foreground state, thermal band, battery policy) run before any score; owner work is P0 and a mesh job never evicts it; an established lease drains rather than dies.",
    "<b>R8 Fail closed.</b> Local-only requests never fall through to a hosted route; an Unplaceable plan or a dead grant path ends the session audibly.",
    "<b>R9 Coordinator outside the payload path.</b> The coordinator stores routing metadata only; prompts, activations, KV bytes and weights never transit it.",
    "<b>R10 Control-plane degradation.</b> Presence, lease heartbeats and revocation survive LAN loss on a carrier whose packets are at most 239 bytes; model and KV traffic does not use that carrier.",
])
h3("3.3 Threat model")
p("In scope: an honest-but-curious peer in the same home that holds a channel key and sees headers and advertisements; a departed node "
  "that returns holding stale leases and stale decisions; a stolen or compromised device that retains ciphertext and keys for its own "
  "chunks; a LAN observer who sees WireGuard ciphertext and LoRa headers. Out of scope: a compromised coordinator host, a malicious "
  "engine binary on a certified node, side channels in timing of compression and routing, and physical attacks on key storage. "
  "Lineage A's warning stands: activations and KV expose input, and partitioning is not anonymisation [@thoxA; @petals].")

# ----------------------------------------------------------------------------
# 4 Design
# ----------------------------------------------------------------------------
h2("4", "Design", "design")
h3("4.1 Architecture")
OUT.append("""
<div class="arch">
  <div class="arch-row"><div class="box ghost"><b>Client surface</b><span>ThoxChat, device portal, OpenAI-wire node server, signed peer requests (existing Apple and Linux stacks)</span></div></div>
  <div class="arch-arrow">requests, route provenance</div>
  <div class="arch-row three">
    <div class="box"><b>Control plane (one)</b><span>membership, certification roster, placement decisions, lease issue and expiry, grant graph edits; metadata only (R9)</span></div>
    <div class="box hi"><b>MeshStack core</b><span>shard planner (two-domain, R1, R2) &middot; KV graph T0-T4 with PLACE (R3, R4) &middot; secrets graph with epoch-bearing lease grants (R5, R6)</span></div>
    <div class="box"><b>Scheduler</b><span>hard filters first (R7), KV-affinity cost form, bootstrap constants until fitted, P0..P4 queue</span></div>
  </div>
  <div class="arch-arrow">plans, grants, leases (epoch, TTL)</div>
  <div class="arch-row four">
    <div class="box"><b>Stage host (E2/P4/P6)</b><span>contiguous layers, engine adapter, role agent, owner reservation floor</span></div>
    <div class="box"><b>Stage host</b><span>activation frames out, bf16 lossless or raw f32</span></div>
    <div class="box"><b>Stage host</b><span>KV T1/T2 local, T3 transfer only under live grant</span></div>
    <div class="box ghost"><b>Hub node</b><span>large memory, replan target, anchor candidate, not a different citizen</span></div>
  </div>
  <div class="arch-row two">
    <div class="box"><b>Primary carrier</b><span>LAN or WireGuard tailnet: activation frames, KV bytes, weights, control</span></div>
    <div class="box dim"><b>Degraded carrier (MeshLink, LoRa)</b><span>presence, lease heartbeat, revocation; 239-byte payload, no model or KV traffic (R10)</span></div>
  </div>
</div>
<figcaption><b>Figure 0.</b> Reconciled architecture. The client surface and node servers are the existing stacks; one control plane issues decisions and leases; the MeshStack core holds the three mechanisms of lineage B; the scheduler holds the filters and queue of the role proposal; a LoRa carrier exists only for control-plane survival. Schematic, not a deployed topology.</figcaption>
""")
h3("4.2 Two-domain capacity admission")
p("The sharder takes a model geometry (layer count, per-layer weight bytes at the target quantisation, per-layer KV bytes per token), "
  "a context policy " + ieq("T") + " in tokens, a workspace estimate per stage, and a mesh state. For every stage " + ieq("s") +
  " on node " + ieq("n") + " the plan is admissible only if")
eq(r"W(s) + K(s)\,T \le R(n) \quad\text{and}\quad \mathit{WS}(s) \le \Sigma(n),")
p("where " + ieq("W(s)") + " is the stage's weight bytes including the embedding on stage 0 and the head on the last stage, " +
  ieq("K(s)") + " is the stage's KV bytes per token summed over its attention layers, " + ieq("R(n)") + " is usable RAM, " +
  ieq("\\mathit{WS}(s)") + " is priced host workspace and " + ieq("\\Sigma(n)") + " is the node's system budget. The two domains are not "
  "summed. Lineage B records why this sentence is written so carefully: a merge that charged workspace against the RAM domain stranded "
  "23 of 64 layers and failed four planner tests until decision D23 restored the two-domain semantics [@thoxB]. Algorithm 1 is the "
  "first-fit contiguous planner used in this paper's calculations; it is conservative and reproducible, and the paper does not claim "
  "it is optimal. Whole-request placement is the case in which the first node admits every layer, so the existing routing path is a "
  "one-stage plan and ships first, as lineage A recommended [@thoxA].")
algo("Algorithm 1. First-fit contiguous two-domain planner", [
    "Input:  layers 0..L-1 with weight bytes w[l], kv bytes per token k[l]; context T;",
    "        workspace WS; nodes n_0..n_m in order (anchor first) with R(n), Sigma(n)",
    "Output: plan (list of stages) or UNPLACEABLE",
    "l <- 0",
    "for each node n in order:",
    "    if WS > Sigma(n): continue                      # workspace domain",
    "    start <- l; W <- embed if start = 0 else 0; K <- 0",
    "    while l < L and W + w[l] + head(l) + (K + k[l]) * T <= R(n):   # RAM domain",
    "        W <- W + w[l] + head(l); K <- K + k[l]; l <- l + 1",
    "    if l > start: emit stage(n, start, l-1, W, K*T, WS)",
    "    if l = L: return plan",
    "return UNPLACEABLE                                  # no partial admission (R1, R8)",
])
h3("4.3 Chunk identity: parent-chained HMAC keys")
p("A KV chunk is the state for a span of tokens at one stage's layer range. Its key is")
eq(r"\kappa_0 = \mathrm{HMAC}_{K}\big(d \,\|\, 0^{32} \,\|\, f \,\|\, \tau_0 \,\|\, \ell(e)\big),\qquad \kappa_i = \mathrm{HMAC}_{K}\big(d \,\|\, \kappa_{i-1} \,\|\, f \,\|\, \tau_i \,\|\, \ell(e)\big),")
p("with " + ieq("K") + " the principal's keying secret, " + ieq("d") + " a fixed domain string, " + ieq("f") + " the 32-byte model "
  "fingerprint, " + ieq("\\tau_i") + " the chunk's tokens as 4-byte big-endian integers and " + ieq("\\ell(e)") + " a length-prefixed "
  "extra field. HMAC-SHA256 is the construction of RFC 2104 over FIPS 180-4 [@rfc2104; @fips180]. Lineage B records that an earlier "
  "reference serialised tokens as decimal text and omitted the extra field, and that a two-language test against published vectors now "
  "pins the construction (decision D21) [@thoxB]; Appendix A gives this paper's own known-answer vector.")
p("<b>Proposition 1 (prefix sharing).</b> Two sessions of the same principal and model whose first " + ieq("j") + " chunks are "
  "identical produce identical keys " + ieq("\\kappa_0,\\dots,\\kappa_{j-1}") + ". <i>Proof.</i> By induction on " + ieq("i") +
  ": the inputs to the " + ieq("i") + "-th HMAC are a deterministic function of " + ieq("(K, f, \\tau_0,\\dots,\\tau_i)") +
  ", which the sessions share for " + ieq("i < j") + ". " + ieq("\\square"))
p("<b>Proposition 2 (no false hit from a divergent prefix).</b> If HMAC-SHA256 with secret " + ieq("K") + " is a pseudorandom "
  "function, then for sessions whose chunk sequences first differ at position " + ieq("j") + ", the keys " + ieq("\\kappa_j, \\kappa_{j+1},\\dots") +
  " collide with those of the other session with probability at most " + ieq("q^2/2^{256}") + " over " + ieq("q") + " keys, and a "
  "different model fingerprint or a different principal gives independent keys at every position. <i>Proof sketch.</i> The PRF inputs "
  "differ in " + ieq("\\tau_j") + " (or in " + ieq("f") + ", or the secret differs), so the outputs are computationally independent of "
  "the honest session's keys; the chain propagates the difference because " + ieq("\\kappa_{i-1}") + " is an input to " + ieq("\\kappa_i") +
  ". A collision would require a PRF output collision. " + ieq("\\square") + " Properties P1 to P5 in Section 6.2 are the executable form of these statements.")
h3("4.4 PLACE: local hit, transfer or recompute")
p("When a session needs a chunk, PLACE answers from three options. A local hit costs nothing. A transfer of a prefix of " + ieq("L") +
  " tokens with " + ieq("k") + " bytes of KV per token over a link of effective payload rate " + ieq("B") + " with per-transfer overhead " +
  ieq("a") + ", using a lossless wire ratio " + ieq("r") + ", and a recompute on a stage that prefills at " + ieq("P") + " tokens per second, cost")
eq(r"T_{\mathrm{xfer}}(L) = \frac{L\,k}{r\,B} + a, \qquad T_{\mathrm{rec}}(L) = \frac{L}{P}, \qquad L^{*} = \frac{a}{\,1/P - k/(rB)\,}\ \text{ when } \tfrac{1}{P} > \tfrac{k}{rB},")
p("and transfer wins for " + ieq("L > L^{*}") + "; when the denominator is not positive, recompute wins at every prefix length. Transfer "
  "is additionally gated by authority (R5): a chunk moves only under a live grant path, however favourable the cost. Lineage B's cost "
  "form for session routing, " + ieq("w_1\\,\\mathrm{prefill}\\,(1-\\mathrm{overlap}) + w_2\\,\\mathrm{decode\\ load} + \\dots") +
  " with thermal, battery, churn and link terms, is kept unchanged with its weights labelled bootstrap constants [@thoxB]. The ratio " +
  ieq("r") + " is a measured per-model input (Section 6.1), not a constant.")
h3("4.5 Roles as epoch-bearing lease grants")
p("The Auto Device Role Mode note proposes a renewable lease with fields that include a monotonic fencing epoch, an absolute expiry, a "
  "heartbeat interval, an owner-preemptible flag that must be false, and a fence token proving that inference belongs to the current "
  "epoch [@thoxRole]. This paper folds that lease into lineage B's secrets graph rather than adding a second control plane: a lease is a "
  "grant edge from the coordinator principal to a node for a scope (a stage of a session, or a role class), carrying an epoch and a "
  "TTL. Validity is evaluated against the live graph at consumption (R5), so a departed node's leases die with its edges, and the epoch "
  "fences late arrivals (R6). The state machine is the note's: AVAILABLE, OFFERED, LEASED, DRAINING, back to AVAILABLE, with EXPIRED on "
  "timeout, disconnect or thermal emergency. Hard filters run before scoring, and the queue is P0 owner foreground, P1 owner local "
  "inference, P2 running leased completion, P3 new lease, P4 speculative work (R7).")
p("<b>Proposition 3 (no stale completion under fencing).</b> If the coordinator increments the session epoch on every re-lease and a "
  "completion is accepted only when its epoch equals the session's current epoch, then no completion produced under a superseded lease "
  "is accepted. <i>Proof.</i> A superseded lease carries epoch " + ieq("e") + "; the session's epoch is at least " + ieq("e+1") +
  " from the re-lease onward and never decreases; equality cannot hold. " + ieq("\\square"))
p("<b>Proposition 4 (bounded stale authorisation).</b> With consumption-time validity, the number of accesses authorised after a "
  "grant-path node departs is zero; with a positive decision cache of lifetime " + ieq("C") + " and consumption interval " + ieq("\\delta") +
  ", it is at most " + ieq("\\lceil C/\\delta \\rceil") + " per session. <i>Proof.</i> Live evaluation sees the missing edge at the first "
  "consumption after departure. A cached decision taken at time " + ieq("t_0") + " authorises consumptions until " + ieq("t_0 + C") +
  ", at most " + ieq("\\lceil C/\\delta\\rceil") + " of them. " + ieq("\\square") + " Section 6.6 measures both in simulation.")
h3("4.6 Control plane and degradation to MeshLink")
p("The control plane is one service (R9) that the record names sadie-mesh in lineage B and the Role Coordinator in the role note; the "
  "paper treats the name as a founder decision (Section 9) and specifies the behaviour. On the primary carrier it issues plans, grants "
  "and leases. When the LAN is gone, a MeshLink radio carries three messages: a presence beacon, a lease heartbeat and a revocation "
  "notice. Each fits in one Meshtastic packet. Meshtastic's channel traffic is AES-CTR under a shared key by default, with AES-CCM "
  "and signed broadcasts available on recent firmware and no forward secrecy [@meshenc]; the heartbeat therefore carries its own MAC "
  "under the lease key and the radio is never trusted for authority. Airtime is computed with the standard LoRa formula [@sx1262] in Section 6.5.")
h3("4.7 Security argument")
p("Against an honest-but-curious peer: KV bytes move only under a grant the peer does not hold, advertisements are principal-keyed, "
  "positive-evidence only and bounded (lineage B's D19), and chunk keys reveal nothing about tokens without " + ieq("K") +
  ". Against a departed node that returns: Propositions 3 and 4. Against a stolen device: crypto-shredding of the entry keys that made "
  "its chunks readable, so retained ciphertext is inert; this is a key operation, not a data hunt. Against a LAN observer: WireGuard on "
  "the primary carrier; on the LoRa carrier the observer sees the 16-byte header, which is why that carrier carries no content. Not "
  "argued here: a compromised coordinator, timing side channels in PLACE and the codec, and physical key extraction; Section 7 lists them.")

# ----------------------------------------------------------------------------
# 5 Implementation
# ----------------------------------------------------------------------------
h2("5", "Implementation", "impl")
p("Two implementations exist. Lineage B's Python reference implementation (pipeline sharder, KV graph, secrets grant graph, "
  "KV-affinity scheduler, five frozen generation-1 wire schemas) has simulation semantics: it computes plans, keys, costs and grant "
  "decisions and executes no tokens; its root suite passed 63 tests with 44 subtests at HEAD b01bc03 on 2026-10-30 [@thoxB]. That "
  "repository is private and not attached to this work; its test states are quoted from the record and were not re-run here. "
  "Lineage A's calculator (33 scenarios, 10 unit tests) is attached and was re-run for this paper: 10 of 10 pass with 83 of 83 "
  "executable lines covered. This paper's own code is the experiment set of Appendix A: a clean-room planner, a clean-room keying "
  "implementation with property tests, the codec harness, the PLACE grid, the LoRa airtime calculator and the churn simulator, in "
  "stdlib Python plus NumPy, PyTorch (CPU) and the zstandard binding.")
table(["Requirement", "Where specified", "Test or evidence in this paper", "Result"], [
    ["R1 capacity truth, R2 contiguity", "Section 4.2, Algorithm 1", "exp/admission_experiments.py: 54 scenarios, Unplaceable emitted with no partial plan", "runs; results in Section 6.3"],
    ["R3 lossless wire", "Section 4.4", f"exp/compression_experiments.py: {C['roundtrip_checks']} bit-exact round trips (SHA-256 of decoded bytes)", "all pass" if C["all_bit_exact"] else "FAIL"],
    ["R4 chunk identity", "Section 4.3", "exp/keying_experiments.py: properties P1-P5, known-answer vector", "all pass" if all(K["properties"].values()) else "FAIL"],
    ["R5 authority at consumption", "Section 4.5, Prop. 4", "exp/churn_sim.py: stale authorisations, live vs cached", "simulated; Section 6.6"],
    ["R6 fencing", "Section 4.5, Prop. 3", "exp/churn_sim.py: stale completions, fenced vs unfenced", "simulated; Section 6.6"],
    ["R7 owner sovereignty", "Section 4.5", "not tested here; filters and queue are specification", "unbuilt"],
    ["R8 fail closed", "Algorithm 1 last line", "admission scenarios that return Unplaceable", "runs"],
    ["R9 coordinator outside payload", "Section 4.1", "architectural; lineage B schemas carry no KV bytes in T4 manifests", "specification"],
    ["R10 control-plane degradation", "Section 4.6", "exp/lora_experiments.py: airtime and heartbeat capacity", "calculated; Section 6.5"],
], "Table 3. Requirement-to-test map. 'Runs' means the script executes and its outputs are in summary.json; 'simulated' and 'calculated' are evidence classes, not measurements on devices.")

# ----------------------------------------------------------------------------
# 6 Evaluation
# ----------------------------------------------------------------------------
h2("6", "Evaluation", "eval")
p("<b>Setup.</b> Host: the authoring container, Linux, 2 vCPU, 7 GB RAM, no accelerator, Python " + C["host"]["python"] +
  ", PyTorch " + C["host"]["torch"] + " (CPU). Model: Qwen/Qwen2.5-0.5B-Instruct [@qwenmodel; @qwen25], " +
  f"{geom['num_hidden_layers']} layers, {geom['num_key_value_heads']} KV heads of dimension {geom['head_dim']}, so {kv_pt:,} bytes of bf16 KV per token "
  f"({fmt(kv4096,0)} MiB at 4096 tokens) and {geom['activation_bytes_per_token_bf16']:,} bytes of bf16 activation per token at a layer boundary. "
  "Prompts: a fixed public-domain passage repeated to 128, 512 and 2048 tokens (the repetition is itself a shared-prefix workload and is "
  "recorded). Timing: one warm-up then 30 repetitions per configuration, medians with interquartile ranges. Nothing else ran on the host "
  "during timed runs. Every number below is read from summary.json; every figure is generated from it.")

h3(f"6.1 How much does a lossless codec buy on the wire? ({fmt(ratio)}x on KV)")
figure("fig_compression.svg", 1,
       f"Lossless compression of real bfloat16 tensors. A: ratio by codec and sample; every bar is a verified bit-exact round trip. The unit Gaussian control "
       f"({fmt(ctrl_ratio)}x with byte-split zstd-3) compresses almost as well as real KV state, so most of the gain is exponent concentration that any "
       f"magnitude-concentrated bf16 stream shares; the model-specific surplus is the difference between the bars. B: encode (with IQR) and decode "
       f"throughput on the 2048-token KV sample, median of 30, authoring host.")
p(f"On the 2048-token KV sample, zstd-3 on the raw byte stream reaches {fmt(ratio_raw)}x; splitting the sign-and-exponent byte plane from the mantissa "
  f"plane before coding lifts that to {fmt(ratio)}x at level 3 and {fmt(ratio_best['ratio'])}x with {ratio_best['codec']}, which is too slow to use. The high plane alone compresses "
  f"{fmt(hi_ratio)}x, the low plane barely at all: the redundancy is in the exponents, which is the observation GAAC builds a calibrated codec on [@gaac]. "
  f"Layer-boundary activations compress {fmt(act_ratio)}x at 2048 tokens. Encode runs at {fmt(enc,0)} MB/s and decode at {fmt(dec,0)} MB/s for the "
  f"byte-split zstd-3 codec on this host.")
p(f"The control is the surprising result. A unit Gaussian bf16 stream of the same size compresses {fmt(ctrl_ratio)}x with the same codec, within "
  f"{fmt((ratio-ctrl_ratio)/ctrl_ratio*100,0)} percent of real KV state. Values whose magnitudes cluster within a few binades use few exponent codes, "
  "and both real activations and a unit Gaussian do; the byte-split codec is exploiting that concentration, not structure that is specific to the model. "
  "Three consequences follow. A lossless tier halves nothing, so PLACE must use a measured ratio per model and the lossless-transport note's "
  "expectation of large lossless gains is not supported by this measurement [@thoxLossless]. A model-specific gain beyond the Gaussian baseline exists "
  "but is small here, so calibrated codecs of the GAAC kind are where further lossless gain would come from, not from stronger general entropy "
  f"coders. And at {fmt(enc,0)} MB/s the codec is not the bottleneck on any LAN a household owns, so compression is on by default for T3 transfers and "
  "off only on links faster than the encoder.")

h3(f"6.2 What does chunk keying cost? ({fmt(us64,1)} microseconds per 64-token chunk)")
figure("fig_keying.svg", 2, "Cost of one parent-chained HMAC-SHA256 chunk key by chunk size (median and IQR of 30), stdlib implementation on the authoring host. The 4096-token chain cost is the title's second number.")
p(f"Keying a 64-token chunk costs {fmt(us64,1)} microseconds ({fmt(keys_s,0)} keys per second on one core); a 4096-token prefix keyed in 64-token "
  f"chunks costs {fmt(chain_ms,2)} ms end to end. Against a prefill that takes seconds and a transfer that takes tens of milliseconds, keying is noise, "
  "and there is no reason to batch or cache it. Properties P1 to P5 (prefix sharing, divergence, model binding, principal binding, determinism) "
  "all pass; the script fails if any does not. The known-answer vector in Appendix A lets the demo page and any other implementation check the "
  "same construction.")

h3("6.3 Does a trio at the public floors place the 27.8B demo model? (No)")
figure("fig_admission.svg", 3,
       f"A: aggregate usable RAM of an Air+Mini+Clip trio at the public floors (2, 4, 6 GB) for three usable fractions, with and without a 16 GB hub, "
       f"against the {fmt(w27,1)} GiB of Q4 weights in the reference demo geometry. B: Clip-class nodes needed to place that geometry with first-fit "
       "contiguous placement. Calculated from floors and recorded geometry; nothing measured.")
p(f"The reference implementation's demo places the 27.8B model on three nodes because its fixtures give the anchor 9.6 GiB usable [@thoxB]. At the "
  f"public floors the trio holds {trio_floor_gb:.0f} GB in total, less than the {fmt(w27,1)} GiB of weights before any KV reserve or usable fraction, so the "
  "plan is Unplaceable at every fraction and every context we tried; adding a 16 GB hub places it at "
  + ", ".join(f"{int(float(f)*100)}% ({r})" for f, r in A["kpi_trio_plus_hub_27b"].items()) + ". "
  f"Without a hub the geometry needs {clip_needed[0]['clip_nodes_needed']} Clip-class nodes at {int(clip_needed[0]['usable_fraction']*100)}% usable and 2048 tokens of context, "
  f"and {clip_needed[-1]['clip_nodes_needed']} at {int(clip_needed[-1]['usable_fraction']*100)}% and 8192 tokens. The smaller models behave as the ThoxOS "
  f"whitepaper's capacity section predicts [@thoxOS]: the published 2.49 GB ThoxMini-Phi4Mini file is {A['phi4mini_on_air_2048']} on one Air at 2048 tokens and "
  f"{A['phi4mini_on_mini_2048']} on one Mini; at 32768 tokens it is {A['phi4mini_on_mini_32768']} on one Mini and {A['phi4mini_on_air_mini_32768']} on Mini+Air, "
  f"which is the regime where a two-stage plan buys context rather than parameters. The 0.5B model is {A['qwen05b_on_air_32768_065']} on one Air at 32768 tokens "
  "and 65% usable. This is the paper's central negative result and it changes the product statement: generation-1 MeshStack serves the 27B class only "
  "with a hub in the mesh, and the benchmark wave's bench trio must be described by its real memory, not by the fixtures.")

h3("6.4 When does transfer beat recompute?")
figure("fig_place.svg", 4,
       "PLACE crossover prefix for the 27.8B geometry (64 KiB of bf16 KV per token) as a function of assumed link rate, for four assumed prefill rates, "
       f"with the measured ratio {fmt(ratio)} (solid) and without compression (dashed). A missing point means recompute wins at every prefix length. "
       "Only the ratio is measured; links and prefill rates are a sweep.")
p(f"With 100 Mb/s of effective payload and a 100 tok/s prefill, transfer wins above {xo(x27_100_100)} compressed and {xo(x27_100_100u)} uncompressed; "
  f"at 500 tok/s prefill on the same link the crossover is {xo(x27_100_500)}, and at 800 Mb/s and 500 tok/s it returns at {xo(x27_800_500)}. For the 0.5B "
  f"geometry (12 KiB per token) at 100 Mb/s and 500 tok/s it is {xo(xq_100_500)}. The shape is the point: because both costs are linear in the prefix, "
  "the decision is a rate comparison between the stage's prefill rate and the link's token rate " + ieq("rB/k") + ", and the per-transfer overhead only "
  "matters within a few tokens of that boundary. On a household LAN the answer flips with the prefill rate of the stage that would recompute, so the "
  "measured link cost and per-stage compute terms of lineage B's D13 telemetry are not optional inputs [@thoxB]. Reported prefill rates for THOX "
  "devices do not exist; the grid is a screen, not a forecast.")

h3("6.5 What can a LoRa control plane carry?")
figure("fig_lora.svg", 5,
       "A: time on air for each MeshStack control message on five Meshtastic presets, 16-byte header included, standard LoRa airtime formula with a "
       "16-symbol preamble. B: number of nodes whose 48-byte lease heartbeats fit a 10% or 1% duty cycle at each heartbeat interval. Calculated; no radio measured.")
p(f"A 48-byte lease heartbeat takes {fmt(lf_hb,0)} ms on LongFast and {fmt(sf_hb,0)} ms on ShortFast; a full 239-byte packet takes {fmt(lf_max,0)} ms and "
  f"{fmt(sf_max,0)} ms. Under a 10% duty cycle LongFast carries 20-second heartbeats for {L['kpi_longfast_nodes_20s_10pct']} nodes and ShortFast for "
  f"{L['kpi_shortfast_nodes_20s_10pct']}; under 1% LongFast carries them for {L['kpi_longfast_nodes_20s_1pct']} nodes at 20 seconds and "
  f"{L['kpi_longfast_nodes_300s_1pct']} at 300 seconds, and ShortFast {L['kpi_shortfast_nodes_5s_1pct']} at 5 seconds. A household mesh of a dozen nodes "
  "fits on the slow presets only with heartbeats of a minute or more, which is adequate for presence and revocation and inadequate for the 5-second "
  "heartbeat the role note proposes for the primary carrier [@thoxRole]; the degraded mode therefore stretches lease TTLs rather than fail. For "
  f"scale, moving the 0.5B model's 4096-token KV ({fmt(kv4096,0)} MiB) over ShortFast at a 10% duty cycle would take about {fmt(kv_hours,0)} hours: the carrier is "
  "a control plane and nothing else (R10). Duty cycles are region specific and the Meshtastic firmware is GPL-3.0, which ThoxOS keeps out of its "
  "Core linking boundary [@thoxOS]; MeshLink is therefore a separate device, not a ThoxOS component.")

h3("6.6 Do fencing and consumption-time validity hold under churn? (Simulation)")
figure("fig_churn.svg", 6,
       f"Discrete-event simulation, {CH['model']['nodes']} nodes, 2-hour runs, 30 seeds, mean uptime 600 s, heartbeat 5 s. A: stale completions an unfenced "
       "protocol would accept versus the same completions rejected by epoch fencing. B: accesses authorised after the grant-path node departed, for two "
       "decision-cache lifetimes and for live evaluation. C: departure detection latency against lease TTL. Medians with IQR. Protocol logic only.")
p(f"With a 20-second TTL and 30-second decision cache the median run has {sess:.0f} sessions and {repl:.0f} re-leases; an unfenced protocol accepts "
  f"{stale_unf:.0f} stale completions from returning holders and the fenced protocol rejects all {stale_fenced:.0f} of them, as Proposition 3 requires. "
  f"Live evaluation authorises {authlive:.0f} accesses after a grant-path node has left and fails {CH['kpi_fail_closed_live_median']:.0f} sessions closed at "
  f"their next consumption; a 30-second cache authorises {auth30:.0f} accesses per run with at most {CH['kpi_max_stale_auth_per_session_cache30']:.0f} in one session "
  f"(the Proposition 4 bound at a 2-second consumption interval is 15), and a 300-second cache {auth300:.0f} with at most {CH['kpi_max_stale_auth_per_session_cache300']:.0f}, "
  f"where the session's own remaining service time, not the cache, is the binding limit. Detection latency tracks the TTL: {fmt(det10,1)} s at 10 s, {fmt(det20,1)} s at 20 s, "
  f"{fmt(det60,1)} s at 60 s, which is the trade the role note names: a shorter TTL finds departures faster and costs more heartbeats, and the LoRa "
  "budget of Section 6.5 bounds how short it can be in degraded mode. These are properties of the protocol under stated distributions; they say nothing "
  "about how often real devices leave.")

# ----------------------------------------------------------------------------
# 7 Discussion and limitations
# ----------------------------------------------------------------------------
h2("7", "Discussion and limitations", "limits")
p("The section a sceptical reader should read first.")
ol([
    "<b>Host and model.</b> All measurements ran on one 2-vCPU container with no accelerator, on one 0.5B model in fp32 with bf16 serialisation. Ratios and throughputs for other models, quantisations or hosts must be measured; the ratio in particular is a per-model input.",
    "<b>Repetitions and statistics.</b> Timing used one warm-up and 30 repetitions per configuration, reported as medians with interquartile ranges; no confidence intervals or significance tests are computed. The simulation used 30 seeds of 2 simulated hours.",
    "<b>No engine, no mesh, no device.</b> No model ran across two hosts, no stage executed on a THOX device, and no throughput, latency or energy figure for MeshStack exists. Lineage B's single-host loopback spike is reproducibility data under its own warning and is not quoted here.",
    "<b>Calculated inputs.</b> The admission results rest on public floors, a usable-fraction sweep, a 256 MiB workspace assumption, uniform per-layer weight splits for the 27.8B and Phi-4-mini geometries, and unpriced SSM state. The PLACE grid rests on assumed link and prefill rates. The LoRa results rest on the standard formula, the documented 16-symbol preamble and illustrative duty cycles.",
    "<b>Not built.</b> Owner-sovereignty filters and the P0..P4 queue, the role agent, production endpoint authentication, real key custody, crypto-shredding and erasure, and the MeshLink message formats are specification. Lineage B's reference implementation was not re-run; its test states are quoted.",
    "<b>Codec scope.</b> The byte-split zstd codec is a baseline from the literature, not a contribution; GAAC-style calibrated codes and fused decompression were not evaluated.",
    "<b>Security scope.</b> No adversarial evaluation of the grant graph, inventory keying or frame scoping has been run; timing side channels in PLACE and the codec are unexamined.",
    "<b>Control-plane ownership.</b> Three documents name three control-plane owners; this paper specifies behaviour and leaves the name to Section 9.",
    "<b>Record motion.</b> The ThoxOS whitepaper (2026-10-31) states that no kernel-model weights exist, while the kernel-model cards dated 2026-11-01 report gate records; that is a one-day staleness in a cited source, not a finding of this paper, and it does not affect any result here.",
    "<b>Not peer reviewed.</b> This is a preprint prepared by THOX.ai Research with AI assistance (Appendix C). External submission needs explicit founder approval.",
])

# ----------------------------------------------------------------------------
# 8 Conclusion
# ----------------------------------------------------------------------------
h2("8", "Conclusion", "concl")
p("MeshStack's two design lineages agree more than their documents suggest: pipeline sharding with fail-closed two-domain admission, a "
  "KV graph whose transfers are gated by cost and authority, and routine churn handled by replanning. This paper writes the agreement down "
  "once, adds the lease and role layer as epoch-bearing grants inside the same secrets graph, and names the LoRa carrier's job. The "
  f"measurements say the lossless wire is worth about {fmt(ratio)}x and the keying is free. The calculation says the current demo "
  "geometry does not fit the devices the company sells without a hub, which the product statement must now reflect. The simulation says "
  "the fencing and consumption-time rules do what their propositions claim. What remains is the evidence that needs a fleet, and the "
  "paper states the gate it must pass.")

# ----------------------------------------------------------------------------
# 9 Roadmap
# ----------------------------------------------------------------------------
h2("9", "Roadmap and decisions for the founders", "roadmap")
p("Ordered by what unblocks what. Items 1 to 3 are decisions; the rest is work.")
ol([
    "<b>Control-plane name and owner.</b> Lineage B names sadie-mesh canonical (DECIDE-01); the role note embeds a Role Coordinator beside routing; THOX_MeshStack ships a Rust coordinator. One service, one name; the lease-grant unification here lets any of the three carry it.",
    "<b>Product statement for generation 1.</b> Device-plus-hub for the 27B class (Section 6.3); device-only for the 3B class with context as the lever. The benchmark wave's bench trio must be described by its real memory.",
    "<b>Authorship and venue.</b> arXiv does not permit AI systems as authors. The roster for this edition is settled: Craig Ross and Tommy Xaypanya are the authors, with Tommy Xaypanya as corresponding author; no AI system is an author.",
    "<b>Measure the ratio per model.</b> Run the codec harness on the Qwen3.6-27B GGUF-derived KV on a fleet host and on a 3B class model on a Mini; replace the PLACE constant with the measured value.",
    "<b>Bench trio with real floors.</b> First real pipeline run of a 3B class model across Air, Mini and Clip at their floors with activation telemetry (per-hop latency, per-stage compute) as the exit gate; then the 27B class with a hub.",
    "<b>Fit the scheduler weights.</b> Replace the bootstrap constants of the cost form with values fitted from the telemetry; print the losing regime (short, cold, unique requests with a capable hub present).",
    "<b>MeshLink message spec.</b> Freeze presence, heartbeat and revocation formats under 239 bytes with a lease-key MAC; test on two ESP32 radios; record the regional duty cycle.",
    "<b>Adversarial pass.</b> Grant graph, inventory keying, frame scoping and timing channels, before any public performance claim.",
])

# ----------------------------------------------------------------------------
# Appendices
# ----------------------------------------------------------------------------
h2("A", "Appendix A. Reproducibility", "appA")
p("Environment: Linux container, 2 vCPU, 7 GB RAM; Python " + C["host"]["python"] + "; PyTorch " + C["host"]["torch"] +
  " (CPU wheel); transformers 5.22.1; zstandard; NumPy; Matplotlib. Node 22 with katex 0.16.11, @fontsource/inter 5.1.0, @fontsource/jetbrains-mono 5.1.1 and Playwright for rendering.")
algo("Commands (from the artifact root)", [
    "pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install transformers safetensors zstandard numpy matplotlib pypdf",
    "python3 exp/compression_experiments.py   # downloads Qwen/Qwen2.5-0.5B-Instruct; ~15 min on 2 vCPU",
    "python3 exp/keying_experiments.py        # fails on any property violation",
    "python3 exp/admission_experiments.py",
    "python3 exp/place_experiments.py         # reads the measured ratio from compression.json",
    "python3 exp/lora_experiments.py",
    "python3 exp/churn_sim.py                 # 30 seeds x 18 configurations, ~2 min",
    "python3 exp/analyze.py                   # writes exp/results/summary.json",
    "python3 wp/figures.py && python3 wp/build.py && node wp/katex_render.cjs wp/paper.src.html wp/paper.html",
    "node wp/pdf.cjs wp/paper.html wp/cover.pdf wp/body.pdf && python3 wp/merge_pdf.py",
])
kav = K["known_answer"]
p("Known-answer vector for the keying construction (secret = bytes 0x00..0x1f, fingerprint = 32 bytes of 0xab, chunks [1,2,3,4] then [5,6]):")
OUT.append('<pre class="small">key_0 = ' + kav["keys_hex"][0] + "\nkey_1 = " + kav["keys_hex"][1] + "</pre>")
p(f"Prompt SHA-256 for the 2048-token sample: <code>{samp2048['prompt_sha256']}</code> ({samp2048['prompt_repeats_of_base']} repeats of the base passage; "
  f"host prefill {fmt(samp2048['prefill_seconds_host'],1)} s). The artifact zip contains every script, raw results JSON, summary.json, figure sources and the built outputs.")

h2("B", "Appendix B. Notation", "appB")
table(["Symbol", "Meaning"], [
    [ieq("W(s), K(s), \\mathit{WS}(s)"), "stage weight bytes, KV bytes per token, priced workspace bytes"],
    [ieq("R(n), \\Sigma(n)"), "node usable RAM and system (workspace) budget"],
    [ieq("T"), "context policy in tokens"],
    [ieq("\\kappa_i, K, f, \\tau_i"), "chunk key, principal keying secret, model fingerprint, chunk tokens"],
    [ieq("L, k, r, B, a, P"), "prefix tokens, KV bytes per token, lossless ratio, link payload rate, transfer overhead, prefill rate"],
    [ieq("L^{*}"), "PLACE crossover prefix"],
    [ieq("C, \\delta"), "decision-cache lifetime, consumption interval"],
    ["E2, P4, P6", "THOX compute classes (Air, Mini, Clip)"],
    ["T0-T4", "KV tiers: in-context, node-local memory, node-local persistent, mesh transfer, manifest"],
])

h2("C", "Appendix C. Authorship and disclosure", "appC")
p("This preprint is issued by THOX.ai Research. The authors are Craig Ross (Chief Executive Officer) and Tommy Xaypanya (Chief Technology "
  "Officer and Co-Founder), THOX.ai LLC; Tommy Xaypanya is the corresponding and accountable human author. Author consent to this "
  "edition is recorded before any submission. Generative AI assistance: the literature retrieval, experiment scripts, analysis, figures and draft "
  "text were produced by an AI system (Claude, Anthropic) operating as the THOX digital human Odette Lark under the direction of the "
  "corresponding author; every citation was resolved live against its primary page on 2026-11-03 and every number is generated from "
  "the experiment outputs. No AI system is an author. Conflicts: the authors are THOX.ai principals; this is an interested-party "
  "technical account. Edition v1.0.0 was an internal confidential draft. This edition (v1.0.1) is the public preprint edition authorised "
  "by the founders: it corrects a rendering defect in Section 6.6 (the detection-latency values), removes an internal host name from the "
  "text, settles the author roster above, and retires the internal draft's confidential marking. No result, measurement or conclusion changed.")

# ----------------------------------------------------------------------------
# References
# ----------------------------------------------------------------------------
h2("", "References", "refs")
refs_html = []
for i, key in enumerate(CITED, 1):
    r = ref_entry(key)
    authors = ", ".join(r["authors"])
    link = f' <a href="{r["url"]}">{r["url"]}</a>' if r["url"] else ""
    refs_html.append(f'<li id="ref{i}"><span class="rn">[{i}]</span> {html.escape(authors)}. <i>{html.escape(r["title"])}</i>. {html.escape(r["venue"])}.{link}</li>')
OUT.append('<ol class="refs">' + "".join(refs_html) + "</ol>")
OUT.append("</section>")

# ----------------------------------------------------------------------------
# Page
# ----------------------------------------------------------------------------
CSS = """
/*__FONTS__*/
/*__KATEX__*/
:root{--green:#047C3D;--green-dark:#05A451;--ink:#111827;--muted:#6B7280;--rule:#E5E7EB;--pale:#E6F4EC;--bg:#FFFFFF}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:var(--bg);color:var(--ink);font-family:Inter,system-ui,sans-serif;font-size:10.5pt;line-height:1.5}
.cover{background:#0B0F14;color:#F3F4F6;min-height:100vh;padding:0}
.cover-inner{max-width:7.1in;margin:0 auto;padding:0.9in 0.6in 0.6in}
.eyebrow{display:flex;justify-content:space-between;align-items:center;font-family:'JetBrains Mono',monospace;font-size:8pt;color:#9CA3AF;border-bottom:1px solid #1F2937;padding-bottom:8px}
.pill{border:1px solid var(--green-dark);color:var(--green-dark);border-radius:999px;padding:2px 10px}
.cover h1{font-size:21pt;line-height:1.2;font-weight:700;margin:22px 0 10px;color:#fff}
.deck{font-size:11pt;color:#D1D5DB;margin:0 0 10px}
.byline{font-size:8.5pt;color:#9CA3AF;margin:0 0 16px}
.abstract{border-left:3px solid var(--green-dark);padding:4px 0 4px 12px;margin:10px 0 14px}
.abstract p{font-size:9.2pt;line-height:1.45;color:#E5E7EB;margin:4px 0 0}
.ct{font-family:'JetBrains Mono',monospace;font-size:8pt;letter-spacing:.08em;text-transform:uppercase;color:var(--green-dark)}
.contents ol{columns:2;column-gap:28px;font-size:8.6pt;margin:6px 0 0;padding-left:0;list-style:none;color:#D1D5DB}
.contents a{color:#D1D5DB;text-decoration:none}
.cover-foot{margin-top:18px;font-size:8pt;color:#6B7280;border-top:1px solid #1F2937;padding-top:8px}
.paper-body{max-width:7.1in;margin:0 auto;padding:0.5in 0.6in 0.8in}
@media screen{.paper-body{padding-top:0.6in}}
h2{font-size:14pt;font-weight:700;margin:26px 0 8px;padding-bottom:4px;border-bottom:2px solid var(--green);break-after:avoid}
h2 .num{color:var(--green);margin-right:10px;font-family:'JetBrains Mono',monospace;font-size:11pt}
h3{font-size:11pt;font-weight:600;margin:16px 0 6px;break-after:avoid}
p{margin:0 0 8px;text-align:left}
.cite{color:var(--green);font-size:9pt}
table{width:100%;border-collapse:collapse;font-size:8.4pt;margin:8px 0 12px;break-inside:auto}
caption{caption-side:bottom;text-align:left;font-size:8.2pt;color:var(--muted);padding-top:5px}
th{background:var(--ink);color:#fff;text-align:left;padding:5px 6px;font-weight:600;font-size:8pt}
td{padding:4px 6px;border-bottom:1px solid var(--rule);vertical-align:top}
tr{break-inside:avoid}
figure{margin:12px 0 14px;break-inside:avoid}
.figwrap svg{width:100%;height:auto}
figcaption{font-size:8.4pt;color:var(--muted);margin-top:4px}
.eq{margin:6px 0 8px;text-align:center;font-size:10pt;overflow-x:auto}
.callout{border-left:3px solid var(--green);background:var(--pale);padding:8px 12px;margin:10px 0 12px;font-size:9.5pt;break-inside:avoid}
.callout .ct{margin-bottom:3px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:10px 0 12px}
.kpi{border:1px solid var(--rule);border-top:3px solid var(--green);padding:8px 9px;break-inside:avoid}
.kv{font-family:'JetBrains Mono',monospace;font-size:17pt;font-weight:700;color:var(--green);line-height:1.1}
.kl{font-size:8pt;color:var(--ink);margin-top:4px;line-height:1.3}
.kt{font-family:'JetBrains Mono',monospace;font-size:7pt;color:var(--muted);text-transform:uppercase;margin-top:5px;letter-spacing:.06em}
.algo{border:1px solid var(--rule);margin:8px 0 12px;break-inside:avoid}
.algo .at{background:var(--ink);color:#fff;font-size:8.4pt;font-weight:600;padding:4px 8px}
.algo pre,pre.small{font-family:'JetBrains Mono',monospace;font-size:7.8pt;line-height:1.4;margin:0;padding:8px;white-space:pre-wrap;overflow-x:auto}
pre.small{border:1px solid var(--rule)}
code{font-family:'JetBrains Mono',monospace;font-size:8pt;word-break:break-all}
ol,ul{margin:0 0 8px;padding-left:20px}
li{margin:0 0 4px}
.arch{border:1px solid var(--rule);padding:10px;margin:8px 0 2px;font-size:7.8pt;break-inside:avoid}
.arch-row{display:grid;gap:8px;margin:0}
.arch-row.three{grid-template-columns:1fr 1.3fr 1fr}.arch-row.four{grid-template-columns:repeat(4,1fr)}.arch-row.two{grid-template-columns:1fr 1fr}
.arch-arrow{text-align:center;color:var(--muted);font-family:'JetBrains Mono',monospace;font-size:7pt;padding:4px 0}
.box{border:1px solid var(--ink);border-radius:4px;padding:6px 8px;background:#fff}
.box b{display:block;font-size:8.2pt;margin-bottom:2px}.box span{color:#374151}
.box.hi{background:var(--pale);border-color:var(--green)}.box.ghost{background:#F3F4F6;border-color:#9CA3AF}.box.dim{border-style:dashed}
.refs{font-size:8.3pt;padding-left:0;list-style:none}
.refs li{margin:0 0 5px;padding-left:28px;text-indent:-28px}
.refs .rn{font-family:'JetBrains Mono',monospace;color:var(--green);margin-right:4px}
.refs a{color:var(--green);word-break:break-all;text-decoration:none}
@media print{.cover{min-height:11in;height:11in}h2{page-break-after:avoid}}
@media (max-width:600px){.paper-body,.cover-inner{padding:24px 16px}.cover h1{font-size:17pt}.kpis{grid-template-columns:1fr 1fr}.arch-row.three,.arch-row.four,.arch-row.two{grid-template-columns:1fr}.contents ol{columns:1}table{display:block;overflow-x:auto;white-space:normal}.eq{font-size:8.5pt}pre{font-size:7pt}.refs a{word-break:break-all}}
"""

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(SHORT)}</title>
<meta name="description" content="THOX.ai Research technical report {VERSION}">
<style>{CSS}</style></head>
<body data-version="{VERSION}">
{cover}
{''.join(OUT)}
</body></html>"""

out = ROOT / "wp" / "paper.src.html"
out.write_text(page)
print("wrote", out, "cited", len(CITED), "refs")
unused = [k for k in list(REFS_RAW) + list(MANUAL_REFS) if k not in CITED]
print("uncited keys (not listed):", unused)
em = page.count("—")
print("em dashes:", em)
