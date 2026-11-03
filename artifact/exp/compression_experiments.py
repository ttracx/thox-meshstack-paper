"""Lossless compression of real KV cache and layer-boundary activations.

What this measures. A real transformer (Qwen/Qwen2.5-0.5B-Instruct, fp32 on
CPU) prefills fixed public-domain prompts at several lengths. From each run we
take (a) the full KV cache and (b) the hidden state at a layer boundary, which
is the tensor a pipeline stage would hand to the next stage. Both are cast to
bfloat16, which is the wire precision a lossless transfer tier would carry, and
compressed with several lossless codecs. We record compression ratio, encode
and decode throughput, and verify the bit-exact round trip for every sample.

What this does not measure. Engine throughput, mesh latency, or anything about
THOX devices. The host is the authoring container (2 vCPU, no accelerator).
Throughput figures are for this host and these codecs only.

Codecs:
  raw-zstd3        zstd level 3 on the bf16 byte stream as laid out in memory
  bytesplit-zstd3  high bytes (sign+exponent) and low bytes (mantissa) planes
                   written as two contiguous streams, then zstd level 3
  bytesplit-zstd9  same planes, zstd level 9
  bytesplit-lzma   same planes, xz/lzma preset 6
  hi-only-zstd3    diagnostic: compress only the high-byte plane (not a codec;
                   reports how much of the total gain comes from exponents)

Outputs exp/results/compression.json. Seeds are fixed; decoding is not used
(prefill only), so there is no sampling randomness.
"""
from __future__ import annotations

import hashlib
import json
import lzma
import statistics
import sys
import time
from pathlib import Path

import numpy as np
import torch
import zstandard as zstd
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
RESULTS = Path(__file__).with_name("results") / "compression.json"
TIMING_REPS = 30
WARMUP = 1
TARGET_LENGTHS = [128, 512, 2048]
LAYER_BOUNDARY = 12  # hidden state after block 12 of 24 (the activation frame)

# Fixed public-domain text (Project Gutenberg, expired copyright). Repeated as
# needed to reach the target token lengths; repetition is itself a realistic
# shared-prefix workload and is recorded in the output.
BASE_TEXT = (
    "It is a truth universally acknowledged, that a single man in possession of a good "
    "fortune, must be in want of a wife. However little known the feelings or views of such "
    "a man may be on his first entering a neighbourhood, this truth is so well fixed in the "
    "minds of the surrounding families, that he is considered the rightful property of some "
    "one or other of their daughters. My dear Mr. Bennet, said his lady to him one day, have "
    "you heard that Netherfield Park is let at last? Mr. Bennet replied that he had not. But "
    "it is, returned she; for Mrs. Long has just been here, and she told me all about it. "
    "Mr. Bennet made no answer. Do you not want to know who has taken it? cried his wife "
    "impatiently. You want to tell me, and I have no objection to hearing it. This was "
    "invitation enough. Why, my dear, you must know, Mrs. Long says that Netherfield is taken "
    "by a young man of large fortune from the north of England; that he came down on Monday "
    "in a chaise and four to see the place, and was so much delighted with it, that he agreed "
    "with Mr. Morris immediately; that he is to take possession before Michaelmas, and some "
    "of his servants are to be in the house by the end of next week. "
)


def bf16_bytes(t: torch.Tensor) -> bytes:
    """Serialize a tensor as contiguous bfloat16 little-endian bytes."""
    b = t.detach().to(torch.bfloat16).contiguous().view(torch.int16).numpy()
    return b.astype("<i2").tobytes()


def byte_split(buf: bytes) -> tuple[bytes, bytes]:
    a = np.frombuffer(buf, dtype=np.uint8).reshape(-1, 2)
    return a[:, 1].tobytes(), a[:, 0].tobytes()  # (high, low) for little-endian


def byte_join(hi: bytes, lo: bytes) -> bytes:
    a = np.empty((len(hi), 2), dtype=np.uint8)
    a[:, 1] = np.frombuffer(hi, dtype=np.uint8)
    a[:, 0] = np.frombuffer(lo, dtype=np.uint8)
    return a.tobytes()


def codec_table() -> dict[str, tuple]:
    def z(level: int):
        c = zstd.ZstdCompressor(level=level)
        d = zstd.ZstdDecompressor()
        return c, d

    c3, d3 = z(3)
    c9, d9 = z(9)

    def enc_raw(buf: bytes) -> bytes:
        return c3.compress(buf)

    def dec_raw(blob: bytes) -> bytes:
        return d3.decompress(blob)

    def make_split(comp, decomp):
        def enc(buf: bytes) -> bytes:
            hi, lo = byte_split(buf)
            h = comp(hi)
            l = comp(lo)
            return len(h).to_bytes(8, "little") + h + l

        def dec(blob: bytes) -> bytes:
            n = int.from_bytes(blob[:8], "little")
            hi = decomp(blob[8:8 + n])
            lo = decomp(blob[8 + n:])
            return byte_join(hi, lo)

        return enc, dec

    split3 = make_split(c3.compress, lambda b: d3.decompress(b))
    split9 = make_split(c9.compress, lambda b: d9.decompress(b))
    splitx = make_split(lambda b: lzma.compress(b, preset=6), lzma.decompress)

    def enc_hi(buf: bytes) -> bytes:
        hi, _ = byte_split(buf)
        return c3.compress(hi)

    return {
        "raw-zstd3": (enc_raw, dec_raw, True),
        "bytesplit-zstd3": (split3[0], split3[1], True),
        "bytesplit-zstd9": (split9[0], split9[1], True),
        "bytesplit-lzma": (splitx[0], splitx[1], True),
        "hi-only-zstd3": (enc_hi, None, False),
    }


def time_fn(fn, arg, reps: int) -> list[float]:
    for _ in range(WARMUP):
        fn(arg)
    out = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn(arg)
        out.append(time.perf_counter() - t0)
    return out


def measure(name: str, buf: bytes, codecs) -> list[dict]:
    rows = []
    sha = hashlib.sha256(buf).hexdigest()
    for cname, (enc, dec, roundtrip) in codecs.items():
        blob = enc(buf)
        ok = None
        if roundtrip:
            back = dec(blob)
            ok = hashlib.sha256(back).hexdigest() == sha
            if not ok:
                raise RuntimeError(f"round trip failed for {cname} on {name}")
        enc_t = time_fn(enc, buf, TIMING_REPS)
        dec_t = time_fn(dec, blob, TIMING_REPS) if roundtrip else []
        mb = len(buf) / 1e6
        rows.append({
            "sample": name,
            "codec": cname,
            "raw_bytes": len(buf),
            "compressed_bytes": len(blob),
            "ratio": len(buf) / len(blob),
            "bit_exact": ok,
            "encode_MBps_median": mb / statistics.median(enc_t),
            "encode_MBps_q1": mb / np.percentile(enc_t, 75),
            "encode_MBps_q3": mb / np.percentile(enc_t, 25),
            "decode_MBps_median": (mb / statistics.median(dec_t)) if dec_t else None,
            "decode_MBps_q1": (mb / np.percentile(dec_t, 75)) if dec_t else None,
            "decode_MBps_q3": (mb / np.percentile(dec_t, 25)) if dec_t else None,
            "timing_reps": TIMING_REPS,
        })
        print(f"  {cname:16s} ratio={len(buf)/len(blob):6.3f} enc={mb/statistics.median(enc_t):8.1f} MB/s", flush=True)
    return rows


def main() -> int:
    torch.manual_seed(0)
    torch.set_num_threads(2)
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype=torch.float32)
    model.eval()
    cfg = model.config
    geometry = {
        "model_id": MODEL_ID,
        "num_hidden_layers": cfg.num_hidden_layers,
        "num_attention_heads": cfg.num_attention_heads,
        "num_key_value_heads": cfg.num_key_value_heads,
        "hidden_size": cfg.hidden_size,
        "head_dim": cfg.hidden_size // cfg.num_attention_heads,
        "kv_bytes_per_token_bf16": 2 * cfg.num_hidden_layers * cfg.num_key_value_heads
        * (cfg.hidden_size // cfg.num_attention_heads) * 2,
        "activation_bytes_per_token_bf16": cfg.hidden_size * 2,
    }
    print("geometry", geometry, flush=True)
    codecs = codec_table()
    rows: list[dict] = []
    samples: list[dict] = []
    captured: dict[str, torch.Tensor] = {}

    def hook(_m, _i, out):
        captured["hidden"] = out[0] if isinstance(out, tuple) else out

    handle = model.model.layers[LAYER_BOUNDARY - 1].register_forward_hook(hook)
    for target in TARGET_LENGTHS:
        text = BASE_TEXT
        while len(tok(text).input_ids) < target:
            text += BASE_TEXT
        ids = tok(text, return_tensors="pt").input_ids[:, :target]
        t0 = time.perf_counter()
        with torch.no_grad():
            out = model(ids, use_cache=True)
        prefill_s = time.perf_counter() - t0
        pkv = out.past_key_values
        layers = []
        for i in range(cfg.num_hidden_layers):
            try:
                k, v = pkv.layers[i].keys, pkv.layers[i].values
            except AttributeError:
                k, v = pkv[i]
            layers.append(torch.cat([k.flatten(), v.flatten()]))
        kv_buf = bf16_bytes(torch.cat(layers))
        act_buf = bf16_bytes(captured["hidden"])
        samples.append({
            "tokens": int(ids.shape[1]),
            "prefill_seconds_host": prefill_s,
            "kv_bytes_bf16": len(kv_buf),
            "activation_bytes_bf16": len(act_buf),
            "activation_layer_boundary": LAYER_BOUNDARY,
            "prompt_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "prompt_repeats_of_base": round(len(text) / len(BASE_TEXT), 2),
        })
        print(f"tokens={ids.shape[1]} kv={len(kv_buf)} act={len(act_buf)} prefill={prefill_s:.1f}s", flush=True)
        rows += measure(f"kv-{ids.shape[1]}", kv_buf, codecs)
        rows += measure(f"act-{ids.shape[1]}", act_buf, codecs)
    handle.remove()

    # Synthetic control: Gaussian bf16 with the same byte count as kv-512, to
    # show the codec gains are a property of real activations, not of bf16.
    g = torch.randn(samples[1]["kv_bytes_bf16"] // 2, generator=torch.Generator().manual_seed(0))
    rows += measure("control-gaussian", bf16_bytes(g), codecs)

    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps({
        "evidence_label": "measured on the authoring host; lossless codec behaviour on real model tensors; not device or engine performance",
        "host": {"cpu_count": 2, "torch": torch.__version__, "python": sys.version.split()[0]},
        "geometry": geometry,
        "samples": samples,
        "rows": rows,
    }, indent=2))
    print("wrote", RESULTS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
