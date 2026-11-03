# Quickstart — THOX MeshStack Research Paper

## Read the paper (30 seconds)

```bash
git clone <this-repo-url> thox-meshstack-paper
cd thox-meshstack-paper
open paper/THOX_MeshStack_Research_Paper_v1.0.1.pdf      # macOS
xdg-open paper/THOX_MeshStack_Research_Paper_v1.0.1.pdf  # Linux
```

Verify the edition of record:

```bash
shasum -a 256 paper/THOX_MeshStack_Research_Paper_v1.0.1.pdf
# d071cf7102994cd698201e384672012b442d5fda26302a77f8690d4ad025d0ff
```

## Run the demo (30 seconds)

Open `paper/MeshStack_Demo_v1.0.1.html` in any browser. No server, no
install; the known-answer tests run in-page.

## Reproduce the numbers (about 15 minutes)

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers safetensors zstandard numpy matplotlib pypdf pillow
cd artifact/wp && npm install && cd ../..
python3 artifact/exp/compression_experiments.py
python3 artifact/exp/keying_experiments.py
python3 artifact/exp/admission_experiments.py
python3 artifact/exp/place_experiments.py
python3 artifact/exp/lora_experiments.py
python3 artifact/exp/churn_sim.py
python3 artifact/exp/analyze.py   # rewrites exp/results/summary.json
```

Every number in the paper is typeset from
`artifact/exp/results/summary.json`.

## Rebuild the paper

```bash
python3 artifact/wp/figures.py
python3 artifact/wp/build.py
node artifact/wp/katex_render.cjs artifact/wp/paper.src.html artifact/wp/paper.html
node artifact/wp/pdf.cjs artifact/wp/paper.html artifact/wp/cover.pdf artifact/wp/body.pdf
python3 artifact/wp/merge_pdf.py
python3 artifact/wp/build_demo.py
node artifact/wp/qa.cjs && python3 artifact/wp/qa_pdf.py
```

Full detail: `artifact/README.md` and `docs/DEVELOPMENT.md`.
