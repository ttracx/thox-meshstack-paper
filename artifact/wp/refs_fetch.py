"""Fetch exact arXiv metadata for every candidate reference and record it.

Writes wp/refs_raw.json with title, authors (in order), published and updated
dates, and the abs URL, straight from the arXiv export API. Nothing is typed
from memory. Entries that fail to resolve are recorded as unresolved.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

CANDIDATES = {
    # lineage A (v1.1.0 paper)
    "flexgen": "2303.06865",
    "flash": "2312.11514",
    "petals": "2209.01188",
    "edge0": "2609.18063",
    "flashmoe": "2601.17063",
    "tutti": "2605.03375",
    "saria": "2610.31169",
    "kafila": "2609.34045",
    "inferslice": "2610.32638",
    "npu": "2605.27435",
    "megatron": "1909.08053",
    "ring": "2310.01889",
    "deepspeedmoe": "2201.05596",
    # lineage B (v2 whitepaper)
    "mooncake": "2407.00079",
    "lmcache": "2510.09665",
    "cacheblend": "2405.16444",
    "cachegen": "2310.07240",
    "pagedattention": "2309.06180",
    "distserve": "2401.09670",
    "sglang": "2312.07104",
    # grok node md
    "cemarouter": "2610.26171",
    "prism": "2508.12851",
    "meshattention": "2512.20968",
    "bloombee": "2604.21072",
    "easybalance": "2608.07964",
    # auto device role md
    "batteryprice": "2609.11940",
    # candidates for closest prior work
    "primacpp": "2504.08791",
    "edgeshard": "2405.14371",
    "petalsinternet": "2312.08361",
    "tpillm": "2410.00531",
    "lingualinked": "2312.00388",
    "galaxy": "2405.17245",
    "hexgen": "2311.11514",
    "gaac": "2610.38210",
    "splitzip": "2605.01708",
    "qwen25": "2412.15115",
}


def fetch(ids: list[str]) -> dict[str, dict]:
    url = "https://export.arxiv.org/api/query?id_list=" + ",".join(ids) + f"&max_results={len(ids)}"
    req = urllib.request.Request(url, headers={"User-Agent": "thox-refs-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    out: dict[str, dict] = {}
    for entry in root.findall("a:entry", NS):
        eid = entry.findtext("a:id", default="", namespaces=NS)
        arxiv_id = eid.rsplit("/abs/", 1)[-1]
        base = arxiv_id.split("v")[0]
        title = " ".join(entry.findtext("a:title", default="", namespaces=NS).split())
        authors = [" ".join(a.findtext("a:name", default="", namespaces=NS).split())
                   for a in entry.findall("a:author", NS)]
        out[base] = {
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors,
            "published": entry.findtext("a:published", default="", namespaces=NS),
            "updated": entry.findtext("a:updated", default="", namespaces=NS),
            "journal_ref": entry.findtext("arxiv:journal_ref", default="", namespaces=NS),
            "doi": entry.findtext("arxiv:doi", default="", namespaces=NS),
            "url": f"https://arxiv.org/abs/{base}",
        }
    return out


def main() -> int:
    ids = list(CANDIDATES.values())
    got: dict[str, dict] = {}
    for i in range(0, len(ids), 10):
        chunk = ids[i:i + 10]
        for attempt in range(3):
            try:
                got.update(fetch(chunk))
                break
            except Exception as exc:  # noqa: BLE001
                print("retry", chunk, exc, file=sys.stderr)
                time.sleep(3)
        time.sleep(3)
    result = {}
    for key, aid in CANDIDATES.items():
        if aid in got and got[aid]["title"]:
            result[key] = got[aid] | {"status": "resolved"}
        else:
            result[key] = {"arxiv_id": aid, "status": "unresolved"}
    Path(__file__).with_name("refs_raw.json").write_text(json.dumps(result, indent=2))
    for key, rec in result.items():
        print(f"{key:14s} {rec['status']:10s} {rec.get('arxiv_id','')}: {rec.get('title','')[:80]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
