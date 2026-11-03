# Agent Handoff — thox-meshstack-paper

Status: PUBLISHED. Public repository `ttracx/thox-meshstack-paper`,
edition v1.0.1 released 2026-11-03 under CTO order (Tommy Xaypanya).
Push route: host `gh` CLI, per the standing GitHub no-card route.
Description: "THOX MeshStack research paper (v1.0.1 public edition):
priced pipeline sharding, grant-gated KV transfer, and lease-fenced
device roles for a private household mesh — paper, companion demo,
and full reproducibility artifact." Topics: `meshstack, thox,
distributed-inference, kv-cache, research-paper`. Collaborators:
sadiethox + cross80127 (push, the platform maximum on personal repos).
Formal release `v1.0.1` carries the three `paper/` files as assets.

## What is done

- Full tree per THOX Repository Creation Standard v1.0: README
  (badges, citation block, governance, license), LICENSE (CC BY 4.0,
  canonical text), NOTICE.md, CITATION.cff, docs/USER_GUIDE.md +
  QUICKSTART.md + DEVELOPMENT.md + previews (renders of the shipped
  HTML edition), .gitignore, this handoff.
- Paper files are byte-identical to the edition of record:
  PDF SHA-256
  `d071cf7102994cd698201e384672012b442d5fda26302a77f8690d4ad025d0ff`,
  HTML `a4c9b3768ab71532e2ee4a4a5bd953fc99f75f6651b9d32fff3bd70c241393b8`,
  demo `57519e4978897c7374425fff828143c36a63c22706304fe794c4381a4e664b13`.
- Artifact source: the v1.0.1 build tree (exp/ + wp/, node_modules
  and intermediate render files excluded).

## Key files and their roles

- `paper/` — the edition of record; never edit in place.
- `artifact/exp/results/summary.json` — single source for every
  number in the paper.

## Conventions

- Any paper byte change = new edition + new consent; never overwrite
  an edition here or in the HF dataset.
- No internal host names or network detail in any public file.
- Identifiers (DOI, arXiv ID) are added only from live readback,
  never anticipated.

## Blockers and open questions

- Zenodo deposit: prepared; on completion, add the DOI to README,
  CITATION.cff, the HF dataset card, and the Model Factory listing
  in one pass.
- arXiv: endorsement gate expected (ThoxOS draft precedent); TeX
  staging derives from `artifact/wp/build.py` output.

## Last verified

2026-11-03, by the GitHub publication lane (Sadie fleet): tree
contents hashed at staging; HF dataset edition verified by
anonymous download, byte-identical.
