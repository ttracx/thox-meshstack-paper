"""Parent-chained HMAC-SHA256 chunk keying: properties and cost.

Construction (clean-room restatement of the MeshStack KV program's D3/D21
description: an HMAC over a serialization that binds the parent key, the model
fingerprint as raw bytes, the chunk's token sequence as uint32 big-endian
integers, and a length-prefixed extra field):

    key_0      = HMAC(K, b"thox.kv.chunk/v1" || 0x00*32 || fp || tokens_0 || lp(extra))
    key_i      = HMAC(K, b"thox.kv.chunk/v1" || key_{i-1} || fp || tokens_i || lp(extra))

with K the principal-scoped keying secret, fp the 32-byte model fingerprint,
tokens_i the chunk's tokens as 4-byte big-endian unsigned integers and
lp(x) = len(x) as 4-byte big-endian || x.

Properties tested (every test must pass or the script fails):
  P1 prefix sharing: two sessions with the same leading chunks under the same
     principal and model produce identical leading keys.
  P2 divergence: a one-token difference anywhere in chunk j changes key_j and
     every later key, so a divergent prefix can never collide into a hit.
  P3 model binding: the same tokens under a different fingerprint give
     different keys at every position.
  P4 principal binding: a different keying secret gives different keys.
  P5 determinism: repeated computation gives identical keys.

Cost measured on the authoring host: wall time per chunk key for chunk sizes
64 to 4096 tokens, 30 repetitions per size after one warm-up, reported as
median and quartiles, plus the chain cost of keying a 4096-token prefix in
64-token chunks. This is stdlib hmac/hashlib; it bounds nothing about devices.

Outputs exp/results/keying.json.
"""
from __future__ import annotations

import hmac
import hashlib
import json
import os
import statistics
import time
from pathlib import Path

import numpy as np

RESULTS = Path(__file__).with_name("results") / "keying.json"
DOMAIN = b"thox.kv.chunk/v1"
REPS = 30
ZERO32 = bytes(32)


def lp(x: bytes) -> bytes:
    return len(x).to_bytes(4, "big") + x


def tokens_bytes(tokens: list[int]) -> bytes:
    return np.asarray(tokens, dtype=">u4").tobytes()


def chunk_key(secret: bytes, parent: bytes | None, fingerprint: bytes,
              tokens: list[int], extra: bytes = b"") -> bytes:
    if len(fingerprint) != 32:
        raise ValueError("fingerprint must be 32 bytes")
    if parent is not None and len(parent) != 32:
        raise ValueError("parent key must be 32 bytes")
    if not tokens:
        raise ValueError("a chunk must carry at least one token")
    msg = DOMAIN + (parent or ZERO32) + fingerprint + tokens_bytes(tokens) + lp(extra)
    return hmac.new(secret, msg, hashlib.sha256).digest()


def chain(secret: bytes, fingerprint: bytes, chunks: list[list[int]]) -> list[bytes]:
    keys: list[bytes] = []
    parent = None
    for c in chunks:
        parent = chunk_key(secret, parent, fingerprint, c)
        keys.append(parent)
    return keys


def chunked(tokens: list[int], size: int) -> list[list[int]]:
    return [tokens[i:i + size] for i in range(0, len(tokens), size)]


def properties() -> dict:
    rng = np.random.default_rng(0)
    secret_a = bytes(rng.integers(0, 256, 32, dtype=np.uint8))
    secret_b = bytes(rng.integers(0, 256, 32, dtype=np.uint8))
    fp_a = hashlib.sha256(b"model-A").digest()
    fp_b = hashlib.sha256(b"model-B").digest()
    toks = [int(x) for x in rng.integers(0, 150000, 1024)]
    chunks = chunked(toks, 64)
    ka = chain(secret_a, fp_a, chunks)
    # P1 prefix sharing: a session sharing the first 8 chunks then diverging
    toks2 = toks[:512] + [int(x) for x in rng.integers(0, 150000, 512)]
    k2 = chain(secret_a, fp_a, chunked(toks2, 64))
    p1 = all(ka[i] == k2[i] for i in range(8)) and all(ka[i] != k2[i] for i in range(8, 16))
    # P2 divergence at one token in chunk 3
    toks3 = list(toks)
    toks3[3 * 64 + 17] = (toks3[3 * 64 + 17] + 1) % 150000
    k3 = chain(secret_a, fp_a, chunked(toks3, 64))
    p2 = all(ka[i] == k3[i] for i in range(3)) and all(ka[i] != k3[i] for i in range(3, 16))
    # P3 model binding
    kb = chain(secret_a, fp_b, chunks)
    p3 = all(ka[i] != kb[i] for i in range(16))
    # P4 principal binding
    kc = chain(secret_b, fp_a, chunks)
    p4 = all(ka[i] != kc[i] for i in range(16))
    # P5 determinism
    p5 = chain(secret_a, fp_a, chunks) == ka
    # known-answer vector for the demo page (also exercised there)
    kav_secret = bytes(range(32))
    kav_fp = bytes([0xAB] * 32)
    kav_tokens = [1, 2, 3, 4]
    kav_keys = chain(kav_secret, kav_fp, [kav_tokens, [5, 6]])
    res = {"P1_prefix_sharing": p1, "P2_divergence": p2, "P3_model_binding": p3,
           "P4_principal_binding": p4, "P5_determinism": p5,
           "known_answer": {"secret_hex": kav_secret.hex(), "fingerprint_hex": kav_fp.hex(),
                            "chunks": [kav_tokens, [5, 6]],
                            "keys_hex": [k.hex() for k in kav_keys]}}
    if not all(v for k, v in res.items() if k.startswith("P")):
        raise SystemExit(f"keying property failure: {res}")
    return res


def timing() -> dict:
    rng = np.random.default_rng(1)
    secret = bytes(rng.integers(0, 256, 32, dtype=np.uint8))
    fp = hashlib.sha256(b"timing-model").digest()
    per_chunk = []
    for size in [64, 256, 1024, 4096]:
        toks = [int(x) for x in rng.integers(0, 150000, size)]
        chunk_key(secret, None, fp, toks)  # warm-up
        ts = []
        for _ in range(REPS):
            t0 = time.perf_counter()
            chunk_key(secret, None, fp, toks)
            ts.append(time.perf_counter() - t0)
        per_chunk.append({"chunk_tokens": size,
                          "us_median": statistics.median(ts) * 1e6,
                          "us_q1": float(np.percentile(ts, 25)) * 1e6,
                          "us_q3": float(np.percentile(ts, 75)) * 1e6,
                          "reps": REPS})
    toks = [int(x) for x in rng.integers(0, 150000, 4096)]
    chunks = chunked(toks, 64)
    chain(secret, fp, chunks)
    ts = []
    for _ in range(REPS):
        t0 = time.perf_counter()
        chain(secret, fp, chunks)
        ts.append(time.perf_counter() - t0)
    return {"per_chunk": per_chunk,
            "chain_4096_tokens_64_per_chunk": {"chunks": len(chunks),
                                               "us_median": statistics.median(ts) * 1e6,
                                               "us_q1": float(np.percentile(ts, 25)) * 1e6,
                                               "us_q3": float(np.percentile(ts, 75)) * 1e6,
                                               "reps": REPS}}


def main() -> int:
    out = {"evidence_label": "measured on the authoring host (stdlib hmac/hashlib); construction properties are exact tests",
           "host": {"cpu_count": os.cpu_count()},
           "properties": properties(), "timing": timing()}
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(out, indent=2))
    print(json.dumps(out["timing"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
