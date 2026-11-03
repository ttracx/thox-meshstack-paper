"""Merge cover.pdf and body.pdf into the final paper PDF and set metadata."""
from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
W = ROOT / "wp"
OUT = ROOT / "dist" / "THOX_MeshStack_Research_Paper_v1.0.1.pdf"
OUT.parent.mkdir(exist_ok=True)

writer = PdfWriter()
cover = PdfReader(W / "cover.pdf")
writer.add_page(cover.pages[0])
for page in PdfReader(W / "body.pdf").pages:
    writer.add_page(page)
writer.add_metadata({
    "/Title": "THOX MeshStack: Capacity-Priced Pipeline Sharding, Grant-Gated KV Transfer and Lease-Fenced Device Roles for a Private Household Mesh",
    "/Author": "Craig Ross and Tommy Xaypanya (corresponding author), THOX.ai Research",
    "/Subject": "Technical report v1.0.1, preprint, not peer reviewed",
    "/Keywords": "MeshStack, ThoxOS, pipeline parallelism, KV cache, HMAC, leases, LoRa, local-first AI",
    "/Creator": "THOX paper pipeline (build.py, katex_render.cjs, pdf.cjs, merge_pdf.py)",
})
with OUT.open("wb") as f:
    writer.write(f)
print("wrote", OUT, "pages", len(writer.pages))
