# THOX MeshStack research paper v1.0.0: reproducibility artifact

Technical report: *THOX MeshStack: Capacity-Priced Pipeline Sharding, Grant-Gated KV Transfer and Lease-Fenced Device Roles for a Private Household Mesh*. THOX.ai Research, 2026-11-03. Preprint, not peer reviewed. Edition v1.0.1 is the public preprint edition authorised by the founders (v1.0.0 was an internal confidential draft).

## Layout

| Path | What it is |
|---|---|
| `exp/*_experiments.py`, `exp/churn_sim.py` | Experiments. Each writes raw JSON to `exp/results/`. |
| `exp/analyze.py` | Writes `exp/results/summary.json`, the single source for every number in the paper. |
| `exp/results/*.json` | Raw results and summary as produced for this edition. |
| `wp/refs_fetch.py`, `wp/refs_raw.json` | Live arXiv metadata fetch for every cited preprint (2026-11-03). |
| `wp/figures.py` | SVG figures from summary.json. |
| `wp/build.py` | Paper text and layout; `[@key]` citations numbered by first use. |
| `wp/katex_render.cjs`, `wp/pdf.cjs`, `wp/merge_pdf.py` | Render math, embed fonts, print Letter PDF with cover and running header. |
| `wp/demo_template.html`, `wp/build_demo.py` | Standalone demo page (pure-JS SHA-256/HMAC with known-answer tests). |
| `wp/qa.cjs`, `wp/qa_pdf.py`, `wp/qa/` | QA: viewport checks, contact sheet, text checks. |
| `dist/` | Built outputs: PDF, HTML, demo. |

## Reproduce

```
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers safetensors zstandard numpy matplotlib pypdf pillow
cd wp && npm install && cd ..
python3 exp/compression_experiments.py
python3 exp/keying_experiments.py
python3 exp/admission_experiments.py
python3 exp/place_experiments.py
python3 exp/lora_experiments.py
python3 exp/churn_sim.py
python3 exp/analyze.py
python3 wp/figures.py && python3 wp/build.py
node wp/katex_render.cjs wp/paper.src.html wp/paper.html
node wp/pdf.cjs wp/paper.html wp/cover.pdf wp/body.pdf && python3 wp/merge_pdf.py
python3 wp/build_demo.py && node wp/qa.cjs && python3 wp/qa_pdf.py
```

Host used for this edition: Linux container, 2 vCPU, 7 GB RAM, no accelerator. Timing numbers are host-specific. Nothing ran on a THOX device.

## Evidence classes

- measured: ran on the authoring host, 30 repetitions, medians with IQR, bit-exact checks where applicable.
- calculated: closed-form or deterministic planner over public floors and stated assumptions.
- simulated: discrete-event protocol simulation with stated distributions, 30 seeds.

No engine throughput, cross-host run or device measurement is claimed anywhere.
