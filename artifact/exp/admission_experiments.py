"""Two-domain shard admission over THOX device-class floors (calculated).

A clean-room, first-fit contiguous sharder that applies the two-domain rule:
for every stage s on node n,

    W(s) + KV(s) <= usable_ram(n)      and      WS(s) <= usable_system(n).

Weights and KV reserve admit against the node's usable RAM; priced host
workspace admits against a separate system budget. Stages are contiguous layer
ranges, one per node, placed in node order with the anchor first. If layers
remain after the last node, the plan is Unplaceable and nothing partial is
emitted. First-fit is a conservative, reproducible choice; this script does
not claim it is optimal.

All inputs are either (a) the public THOX class floors (Air 2 GB, Mini 4 GB,
Clip 6 GB RAM floors) with a stated usable fraction, (b) real model geometry
read from the Qwen2.5-0.5B-Instruct safetensors file, (c) the published
ThoxMini-Phi4Mini Q4_K_M file size (2,493,840,576 bytes) with Phi-4-mini's
public layer and KV geometry, or (d) the 27.8B/64-layer Q4 demo geometry
recorded in the MeshStack v2 design paper (14.6 GiB weights, 16 attention
layers with 4 KV heads of head dimension 256). Nothing here is a measurement.

Outputs exp/results/admission.json.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

RESULTS = Path(__file__).with_name("results") / "admission.json"
GIB = 1024 ** 3
MIB = 1024 ** 2
GB = 10 ** 9

# Public class floors (RAM). Usable fractions are stated assumptions covering
# OS, services and runtime; they are swept, not asserted.
CLASS_FLOORS = {"Air": 2 * GB, "Mini": 4 * GB, "Clip": 6 * GB}
USABLE_FRACTIONS = [0.5, 0.65, 0.8]
WORKSPACE_PER_STAGE = 256 * MIB  # stated assumption, priced in its own domain
SYSTEM_BUDGET_FRACTION = 0.25     # of floor, for the workspace domain (assumption)


@dataclass
class Model:
    name: str
    layers: int
    layer_weight_bytes: list[float]      # per layer, in order
    embed_bytes: float                   # charged to stage 0
    head_bytes: float                    # charged to last stage
    kv_bytes_per_token_per_layer: list[float]
    source: str


@dataclass
class Node:
    name: str
    usable_ram_bytes: float
    usable_system_bytes: float


@dataclass
class Stage:
    node: str
    layer_start: int
    layer_end: int
    weight_bytes: float
    kv_bytes: float
    workspace_bytes: float


def qwen_geometry() -> Model:
    """Read real per-layer parameter counts from the cached safetensors file."""
    from huggingface_hub import hf_hub_download
    from safetensors import safe_open
    path = hf_hub_download("Qwen/Qwen2.5-0.5B-Instruct", "model.safetensors")
    per_layer: dict[int, int] = {}
    embed = head = other = 0
    with safe_open(path, "pt") as f:
        for k in f.keys():
            n = 1
            for d in f.get_slice(k).get_shape():
                n *= d
            if k.startswith("model.layers."):
                i = int(k.split(".")[2])
                per_layer[i] = per_layer.get(i, 0) + n
            elif k.startswith("model.embed_tokens"):
                embed += n
            elif k.startswith("lm_head"):
                head += n
            else:
                other += n
    layers = max(per_layer) + 1
    # Qwen2.5-0.5B ties lm_head to embed_tokens; the file carries one copy, so
    # the head adds no bytes beyond the embedding already charged to stage 0.
    return Model(
        name="Qwen2.5-0.5B-Instruct bf16 (real geometry)",
        layers=layers,
        layer_weight_bytes=[per_layer[i] * 2 for i in range(layers)],
        embed_bytes=embed * 2,
        head_bytes=head * 2 + other * 2,
        kv_bytes_per_token_per_layer=[2 * 2 * 64 * 2] * layers,  # 2 KV heads, head_dim 64, bf16
        source="model.safetensors of Qwen/Qwen2.5-0.5B-Instruct, parameter counts per tensor",
    )


def phi4mini_geometry() -> Model:
    total = 2_493_840_576  # published ThoxMini-Phi4Mini Q4_K_M size (bytes)
    layers = 32
    embed_share = 0.08  # stated assumption for embedding plus head share at Q4_K_M
    body = total * (1 - embed_share)
    return Model(
        name="ThoxMini-Phi4Mini Q4_K_M (published file size, uniform per-layer split)",
        layers=layers,
        layer_weight_bytes=[body / layers] * layers,
        embed_bytes=total * embed_share / 2,
        head_bytes=total * embed_share / 2,
        kv_bytes_per_token_per_layer=[2 * 8 * 128 * 2] * layers,  # 8 KV heads, head_dim 128, bf16
        source="published GGUF size 2,493,840,576 B; Phi-4-mini public geometry; uniform split is an assumption",
    )


def demo27b_geometry() -> Model:
    layers = 64
    total = 14.6 * GIB
    attn = set(range(0, 64, 4))  # 16 attention layers; positions are an assumption (every fourth)
    return Model(
        name="27.8B/64-layer Q4 demo geometry (MeshStack v2 design paper record)",
        layers=layers,
        layer_weight_bytes=[total / layers] * layers,
        embed_bytes=0.0,
        head_bytes=0.0,
        kv_bytes_per_token_per_layer=[(2 * 4 * 256 * 2) if i in attn else 0.0 for i in range(layers)],
        source="14.6 GiB total weights, 64 layers, 16 attention layers x 4 KV heads x 256 head_dim, bf16 KV; SSM state not priced",
    )


def plan(model: Model, nodes: list[Node], context_tokens: int,
         workspace: float = WORKSPACE_PER_STAGE) -> dict:
    stages: list[Stage] = []
    layer = 0
    for node in nodes:
        if layer >= model.layers:
            break
        if workspace > node.usable_system_bytes:
            continue
        start = layer
        w = model.embed_bytes if start == 0 else 0.0
        kv = 0.0
        while layer < model.layers:
            lw = model.layer_weight_bytes[layer]
            lkv = model.kv_bytes_per_token_per_layer[layer] * context_tokens
            tail = model.head_bytes if layer == model.layers - 1 else 0.0
            if w + lw + tail + kv + lkv <= node.usable_ram_bytes:
                w += lw + tail
                kv += lkv
                layer += 1
            else:
                break
        if layer > start:
            stages.append(Stage(node.name, start, layer - 1, w, kv, workspace))
    placed = layer >= model.layers
    return {
        "model": model.name, "context_tokens": context_tokens,
        "nodes": [n.name for n in nodes],
        "result": "placed" if placed else "Unplaceable",
        "layers_placed": layer, "layers_total": model.layers,
        "stages": [asdict(s) for s in stages] if placed else [],
        "total_weight_bytes": sum(model.layer_weight_bytes) + model.embed_bytes + model.head_bytes,
    }


def mk_nodes(classes: list[str], frac: float) -> list[Node]:
    return [Node(f"{c}-{i}", CLASS_FLOORS[c] * frac, CLASS_FLOORS[c] * SYSTEM_BUDGET_FRACTION)
            for i, c in enumerate(classes)]


def main() -> int:
    models = {"qwen05b": qwen_geometry(), "phi4mini": phi4mini_geometry(), "demo27b": demo27b_geometry()}
    scenarios = []
    for frac in USABLE_FRACTIONS:
        for ctx in [2048, 8192, 32768]:
            scenarios.append(("A: 0.5B on one Air", plan(models["qwen05b"], mk_nodes(["Air"], frac), ctx), frac))
            scenarios.append(("B1: Phi4Mini on one Air", plan(models["phi4mini"], mk_nodes(["Air"], frac), ctx), frac))
            scenarios.append(("B2: Phi4Mini on one Mini", plan(models["phi4mini"], mk_nodes(["Mini"], frac), ctx), frac))
            scenarios.append(("B3: Phi4Mini on Air+Mini", plan(models["phi4mini"], mk_nodes(["Mini", "Air"], frac), ctx), frac))
            scenarios.append(("C1: 27B demo on Mini+Clip+Air trio", plan(models["demo27b"], mk_nodes(["Mini", "Clip", "Air"], frac), ctx), frac))
            scenarios.append(("C2: 27B demo on Mini+Clip+Air+16GB hub",
                              plan(models["demo27b"], mk_nodes(["Mini", "Clip", "Air"], frac)
                                   + [Node("Hub16-3", 16 * GB * frac, 16 * GB * SYSTEM_BUDGET_FRACTION)], ctx), frac))
    # How many Clip-class nodes does the 27B demo geometry need at each fraction?
    clip_counts = []
    for frac in USABLE_FRACTIONS:
        for ctx in [2048, 8192]:
            n = 1
            while n <= 24:
                p = plan(models["demo27b"], mk_nodes(["Clip"] * n, frac), ctx)
                if p["result"] == "placed":
                    break
                n += 1
            clip_counts.append({"usable_fraction": frac, "context_tokens": ctx,
                                "clip_nodes_needed": n if n <= 24 else None})
    out = {
        "evidence_label": "calculated from public class floors, real or published model geometry, and stated assumptions; not a measurement",
        "assumptions": {
            "class_floors_bytes": CLASS_FLOORS, "usable_fractions": USABLE_FRACTIONS,
            "workspace_per_stage_bytes": WORKSPACE_PER_STAGE, "system_budget_fraction": SYSTEM_BUDGET_FRACTION,
            "placement": "first-fit contiguous in node order, anchor first; not optimal",
        },
        "models": {k: {"name": m.name, "layers": m.layers, "total_weight_bytes": sum(m.layer_weight_bytes) + m.embed_bytes + m.head_bytes,
                       "kv_bytes_per_token": sum(m.kv_bytes_per_token_per_layer), "source": m.source} for k, m in models.items()},
        "scenarios": [{"label": lab, "usable_fraction": frac, **p} for lab, p, frac in scenarios],
        "clip_nodes_needed_for_27b": clip_counts,
    }
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(out, indent=2))
    for lab, p, frac in scenarios:
        print(f"{frac:.2f} ctx={p['context_tokens']:6d} {lab:40s} {p['result']:12s} {p['layers_placed']}/{p['layers_total']}")
    print(clip_counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
