"""Embed summary.json into the demo page and write dist/MeshStack_Demo_v1.0.0.html."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
summary = json.loads((ROOT / "exp" / "results" / "summary.json").read_text())
# keep the demo small: drop bulky grids the page does not use
slim = {
    "compression": {k: v for k, v in summary["compression"].items() if k.startswith("kpi")},
    "keying": {"known_answer": summary["keying"]["known_answer"], "kpi_us_per_64_token_chunk": summary["keying"]["kpi_us_per_64_token_chunk"]},
    "admission": {"models": summary["admission"]["models"], "kpi_trio_27b_at_floors": summary["admission"]["kpi_trio_27b_at_floors"]},
    "churn": {k: v for k, v in summary["churn"].items() if k.startswith("kpi")},
    "lora": {"presets": summary["lora"]["presets"], "kpi_longfast_heartbeat_ms": summary["lora"]["kpi_longfast_heartbeat_ms"]},
}
tpl = (ROOT / "wp" / "demo_template.html").read_text()
out = tpl.replace("/*__SUMMARY__*/", json.dumps(slim).replace("</", "<\\/"))
dist = ROOT / "dist"
dist.mkdir(exist_ok=True)
(dist / "MeshStack_Demo_v1.0.1.html").write_text(out)
print("wrote demo", len(out) / 1e3, "KB")
