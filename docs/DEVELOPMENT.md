# Development — THOX MeshStack Research Paper

## Architecture

This is a paper repository. There are three layers:

1. **Experiments** (`artifact/exp/`): standalone Python scripts. Each
   writes raw JSON to `artifact/exp/results/`; `analyze.py` folds them
   into `summary.json`, the single source for every number in the
   paper. The paper build reads no other results file.
2. **Paper build** (`artifact/wp/`): `build.py` holds the full text and
   layout and typesets numbers from `summary.json`; `figures.py`
   renders the SVG figures from the same summary; `katex_render.cjs`
   renders math and inlines fonts into a single HTML file; `pdf.cjs`
   prints the Letter PDF (cover + body) and `merge_pdf.py` merges it;
   `build_demo.py` embeds `summary.json` into the demo page.
3. **QA** (`artifact/wp/qa.cjs`, `qa_pdf.py`): viewport checks at 1280
   and 390 px in light and dark themes, console-error capture, the
   demo's known-answer tests, a PDF contact sheet, and text checks
   (em dashes, TODO, placeholders). A QA pass is required before any
   edition is called final; the rendered-output text scan for
   unresolved template placeholders is part of it (added after the
   v1.0.0 internal draft shipped a placeholder defect that viewport QA
   alone missed).

## Dev environment

- Python 3.12+: torch (CPU wheel), transformers, safetensors,
  zstandard, numpy, matplotlib, pypdf, pillow.
- Node 20+: `cd artifact/wp && npm install` (KaTeX, fonts, Playwright
  for `pdf.cjs` / `qa.cjs`).
- Commands: see `docs/QUICKSTART.md` (reproduce + rebuild sequences).

## Conventions

- Numbers change only by re-running experiments and rebuilding; never
  hand-edit a typeset number or a results JSON.
- Edition bumps: any byte change to the paper is a new edition
  (v1.0.x), gets its own versioned filenames, and author consent
  attaches to the new exact bytes. Earlier editions are never
  overwritten, in this repo or in the THOX Whitepapers dataset.
- Internal host names, network detail, and lane internals never appear
  in public text; the pre-publication security scan is part of the
  edition checklist.
- Commit style: short imperative subject, edition or section named.

## Work log

- 2026-11-03: v1.0.0 internal draft produced and independently
  verified; four publication blockers found (one rendering placeholder
  defect in Section 6.6, confidential marking, one internal host name,
  unsettled author roster).
- 2026-11-03: v1.0.1 public edition built from source with all four
  fixed, author roster printed (Craig Ross; Tommy Xaypanya,
  corresponding), QA re-run including the placeholder text scan.
  PDF SHA-256
  `d071cf7102994cd698201e384672012b442d5fda26302a77f8690d4ad025d0ff`.
- 2026-11-03: v1.0.1 served from the THOX Whitepapers dataset on
  Hugging Face and indexed on its card.

## Known limitations

- No DOI or arXiv ID yet. Zenodo deposit is in preparation and waits on
  the co-author consent of record; when it completes, update the
  README, `CITATION.cff`, this file, and the dataset card in one pass.
- The paper's evidence classes stand as printed: the engine spike and
  cross-host transfer measurements named in its Section 9 were not run
  for this edition.
- References to the MeshStack v2 design paper and the lineage A report
  are citations of internal documents, labelled as such in the paper.

## Roadmap

- v1.1.0 evidence edition (measured engine spike, real-KV codec runs,
  cross-host transfer validation, live fencing drill) is being produced
  by the MeshStack virtual-lab program; it publishes as its own edition
  with its own consent round, never as an edit to v1.0.1.
