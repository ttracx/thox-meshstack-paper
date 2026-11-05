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

- Zenodo deposit: complete. DOI 10.5281/zenodo.23919580
  (https://zenodo.org/records/23919580), added to README and
  CITATION.cff from live readback on 2026-11-03.
- arXiv: endorsement gate expected (ThoxOS draft precedent); TeX
  staging derives from `artifact/wp/build.py` output.

## Last verified

2026-11-03, by the GitHub publication lane (Sadie fleet): tree
contents hashed at staging; HF dataset edition verified by
anonymous download, byte-identical.

2026-11-03, by the GitHub DOI patch lane: DOI added to README,
CITATION.cff, and the v1.0.1 release notes from the live Zenodo
record.

## v1.1.0 evidence edition published (2026-11-04)

- Zenodo new version of record 23919580: DOI 10.5281/zenodo.23969070
  (concept DOI 10.5281/zenodo.23919579), version field 1.1.0, CC BY
  4.0, both authors with ORCIDs. Served PDF SHA-256 verified against
  the pack: 7349a6bc6a1ea89cdcd89aad87385fd5155bf645060d064dbdad85e30d4afbaf.
- The carried-over record description was corrected in the same pass:
  the KV codec figure now reads 1.17x to 1.20x (the 1.51x sentence was
  the v1.0.1 text; the paper restates it in Section 6.1).
- GitHub: v1.1.0 trio added under paper/, README + CITATION.cff
  updated to the v1.1.0 version DOI, release v1.1.0 cut with the trio
  plus the artifact ZIP (SHA-256
  9245eff36e33f741c90f56eba11773cff79dc174250b3d933d4ade872e65ceea).
- Publication proceeded on Tommy's global paper approval of
  2026-11-04, which covers all THOX papers; per-paper consent is no
  longer a gate.
