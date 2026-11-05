# THOX MeshStack Research Paper

![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-05A451)
![Status: Preprint](https://img.shields.io/badge/Status-Preprint-05A451)
![Publisher: THOX.ai Research](https://img.shields.io/badge/Publisher-THOX.ai%20Research-05A451)

**THOX MeshStack: Capacity-Priced Pipeline Sharding, Grant-Gated KV Transfer and Lease-Fenced Device Roles for a Private Household Mesh**

THOX.ai Research technical report v1.1.0 (evidence edition), 4 November 2026. Preprint, not peer reviewed.

Edition v1.1.0 supersedes v1.0.1: it folds the four Virtual Lab evidence lanes (codec, transfer, roles, engine) into the paper and corrects the KV codec figure to the measured real-GGUF 1.17x to 1.20x (the v1.0.1 edition's 1.51x was a bfloat16-tensor result and is restated in Section 6.1).

Authors: **Craig Ross** and **Tommy Xaypanya** (corresponding author), THOX.ai LLC.
Tommy Xaypanya ORCID: [0009-0000-4425-9565](https://orcid.org/0009-0000-4425-9565).

This repository is the paper edition of record for the MeshStack research paper: the paper itself (PDF and HTML), its interactive companion demo, and the complete reproducibility artifact (experiment code, raw results, paper build pipeline) that produced every number in it. The paper reconciles the two MeshStack design lineages — storage-aware parallelism and the MeshStack v2 pipeline-sharding design — with the Auto Device Role Mode lease design folded in. Pipeline stage placement is priced against each node's storage and memory floors; KV cache moves between nodes only under an explicit grant; device roles are held under epoch-bearing leases so a departed holder cannot act on a stale authorisation. Results are classed honestly as measured (general host), calculated (public device floors), or simulated (protocol logic). No physical-device measurement is claimed; the v1.1.0 evidence edition adds measured cross-host KV transfer and a two-host engine split (n = 1, transport caveats stated in the paper).

![Rendered preview of the paper (light theme, 1280 px render of the shipped HTML edition)](docs/previews/paper-render-1280-light.png)

## Quick start

Read the paper: [`paper/THOX_MeshStack_Research_Paper_v1.1.0.pdf`](paper/THOX_MeshStack_Research_Paper_v1.1.0.pdf)
(PDF, 30 pages, SHA-256 `7349a6bc6a1ea89cdcd89aad87385fd5155bf645060d064dbdad85e30d4afbaf`)
or [`paper/THOX_MeshStack_Research_Paper_v1.1.0.html`](paper/THOX_MeshStack_Research_Paper_v1.1.0.html)
(single-file HTML edition).

Run the companion demo: open [`paper/MeshStack_Demo_v1.1.0.html`](paper/MeshStack_Demo_v1.1.0.html)
in any browser. It is a single self-contained file; its SHA-256/HMAC
known-answer tests run in-page.

Reproduce the numbers: see [`docs/QUICKSTART.md`](docs/QUICKSTART.md) and
[`artifact/README.md`](artifact/README.md).

## Repository layout

| Path | What it is |
|---|---|
| `paper/` | The paper of record: PDF, single-file HTML, and the companion demo, current edition v1.1.0, with the v1.0.1 files retained alongside. |
| `artifact/` | Reproducibility artifact: `exp/` experiment code and raw results (`exp/results/summary.json` is the single source for every number in the paper), `wp/` paper build pipeline (text, figures, render, QA). |
| `docs/` | `USER_GUIDE.md`, `QUICKSTART.md`, `DEVELOPMENT.md`, and rendered previews under `docs/previews/`. |
| `CITATION.cff` | Citation metadata for this paper. |
| `.agents/HANDOFF.md` | Agent handoff: status, key files, conventions, blockers. |

## Documentation map

- User guide: [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md)
- Quick start / reproduction: [`docs/QUICKSTART.md`](docs/QUICKSTART.md)
- Development and build notes: [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)
- Agent handoff: [`.agents/HANDOFF.md`](.agents/HANDOFF.md)

## Citation

```bibtex
@techreport{thox-meshstack-2026,
  title     = {THOX MeshStack: Capacity-Priced Pipeline Sharding, Grant-Gated
               KV Transfer and Lease-Fenced Device Roles for a Private
               Household Mesh},
  author    = {Ross, Craig and Xaypanya, Tommy},
  institution = {THOX.ai Research, THOX.ai LLC},
  number    = {v1.1.0},
  doi       = {10.5281/zenodo.23969070},
  year      = {2026},
  month     = nov,
  note      = {Preprint, not peer reviewed},
  url       = {https://huggingface.co/datasets/Thox-ai/thox-whitepapers}
}
```

Machine-readable citation metadata: [`CITATION.cff`](CITATION.cff).

Status identifiers, stated plainly: the current edition's DOI is
[10.5281/zenodo.23969070](https://doi.org/10.5281/zenodo.23969070)
(Zenodo record: https://zenodo.org/records/23969070), recorded in
`CITATION.cff`. The all-versions concept DOI is
[10.5281/zenodo.23919579](https://doi.org/10.5281/zenodo.23919579);
the superseded v1.0.1 edition's DOI is 10.5281/zenodo.23919580.
It has **no arXiv ID**. The paper is also served from the
[THOX Whitepapers dataset](https://huggingface.co/datasets/Thox-ai/thox-whitepapers)
on Hugging Face (`meshstack/THOX_MeshStack_Research_Paper_v1.1.0.pdf`).

## Releases

Formal releases are cut in this repository per edition, with the paper
files attached as release assets. See the Releases page. Edition v1.0.0
was an internal confidential draft and was never published; v1.0.1 was
the first public edition. Edition v1.1.0 (evidence edition) was
published 4 November 2026; its reproducibility artifact ships as the
v1.1.0 release ZIP asset.

## Agent handoff pointer

Agents resuming work on this repository start at
[`.agents/HANDOFF.md`](.agents/HANDOFF.md).

## Governance note

Public publishing (social posts, website changes, store listings, public
repository visibility changes, registries, campaigns) requires Craig
Ross's explicit approval via craig@thox.ai, CC tommy@thox.ai. This
repository's public release follows the THOX research-release process:
author consent attaches to the exact edition bytes (SHA-256 above).

## License

The paper, demo, and documentation in this repository are licensed under
the Creative Commons Attribution 4.0 International License
([CC BY 4.0](LICENSE)). The experiment and build code under `artifact/`
is included as the paper's reproducibility artifact under the same
license. See [`NOTICE.md`](NOTICE.md) for attribution and third-party
notices.
