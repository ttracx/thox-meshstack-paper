# User Guide — THOX MeshStack Research Paper

## What this is

This repository holds the paper edition of record for "THOX MeshStack:
Capacity-Priced Pipeline Sharding, Grant-Gated KV Transfer and
Lease-Fenced Device Roles for a Private Household Mesh" (THOX.ai
Research technical report v1.0.1, 3 November 2026), its interactive
companion demo, and the full reproducibility artifact behind it.

It is for:

- Readers who want the paper in PDF or HTML.
- Reviewers who want to check any number in the paper against the code
  and raw results that produced it.
- Engineers evaluating MeshStack's design: priced pipeline placement,
  grant-gated KV transfer, and lease-fenced device roles.

## The paper

| File | Format | Notes |
|---|---|---|
| `paper/THOX_MeshStack_Research_Paper_v1.0.1.pdf` | PDF, 27 pages | SHA-256 `d071cf7102994cd698201e384672012b442d5fda26302a77f8690d4ad025d0ff` |
| `paper/THOX_MeshStack_Research_Paper_v1.0.1.html` | Single-file HTML | Same edition; fonts and math embedded, no external requests |
| `paper/MeshStack_Demo_v1.0.1.html` | Single-file HTML demo | Interactive companion; see below |

Status: preprint, not peer reviewed. No DOI or arXiv ID has been issued
yet; a Zenodo deposit is in preparation and identifiers will be added
to the README and `CITATION.cff` when it completes. The paper is also
served from the THOX Whitepapers dataset on Hugging Face.

### How to read the evidence labels

Every quantitative claim in the paper carries one of three classes,
defined in its Section 2 and used consistently:

- **Measured** — produced by running the artifact code on a general
  host (KV compression, HMAC keying, LoRa airtime arithmetic on stated
  parameters).
- **Calculated** — derived from public device parameters and the
  geometry worksheets in the artifact (admission verdicts, KV bytes
  per token).
- **Simulated** — protocol logic under stated distributions (churn and
  fencing results). Simulation says nothing about real departure rates
  or engine behaviour.

No engine throughput, cross-host transfer, or physical-device
measurement is claimed anywhere in the paper.

## The companion demo

Open `paper/MeshStack_Demo_v1.0.1.html` in a browser. It is fully
self-contained (no network calls) and lets you:

- Recompute the PLACE transfer-vs-recompute crossover for a prefix.
- Run the HMAC chunk-keying known-answer tests in-page (pure-JS
  SHA-256/HMAC implementation).
- See the admission worksheet for the reference model at the public
  device floors.

## The reproducibility artifact

`artifact/` contains everything that produced the paper:

- `artifact/exp/` — experiment scripts and their raw JSON results.
  `exp/results/summary.json` is the single source from which every
  number in the paper is typeset.
- `artifact/wp/` — the paper build: text and layout (`build.py`),
  figures (`figures.py`), math and PDF rendering, the demo builder,
  and the QA harness (`qa.cjs`, `qa_pdf.py`, with the QA report and
  renders under `wp/qa/`).

See `artifact/README.md` for the artifact's own layout and reproduction
commands, and `docs/QUICKSTART.md` for the short path.

## Citing

Use `CITATION.cff` (machine-readable) or the BibTeX block in the
README. Please cite edition v1.0.1; v1.0.0 was an internal draft and
was never published.

## Troubleshooting / FAQ

**The HTML edition looks unstyled or the math is boxes.** You are
viewing the raw file through a tool that strips embedded CSS/fonts.
Download the file and open it directly in a browser.

**A number in the paper does not match summary.json.** That is a
defect; the paper's build typesets numbers from `summary.json` only.
Open an issue with the section number.

**Where is the implementation?** This repository is the paper and its
evidence artifact, not the MeshStack product implementation. The paper
cites its design sources honestly as internal documents; the MeshStack
v2 design paper is served in the THOX Whitepapers dataset.

**Can I reuse the text or figures?** Yes, under CC BY 4.0 with
attribution (see `LICENSE` and `NOTICE.md`).
