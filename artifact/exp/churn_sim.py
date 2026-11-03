"""Lease fencing and consumption-time validity under churn (simulation).

This is a discrete-event simulation with stated distributions. It evaluates
protocol logic only: it says nothing about real device behaviour, radio links
or engine timing, and every number it produces is labeled simulation.

Model. N nodes alternate between up and down. Up durations are exponential
with mean U, down durations exponential with mean 60 s. Sessions arrive as a
Poisson process (mean inter-arrival 20 s) and each needs one worker for an
exponential service time (mean 30 s). The coordinator grants a lease with TTL T
to an up node; the node heartbeats every H seconds. If the node goes down
mid-session the coordinator detects the loss when the TTL expires without a
heartbeat and re-leases the session to another up node with a fresh epoch.

Two completion policies are compared on identical event streams:

  unfenced  a worker that comes back up finishes any session it was holding
            and the coordinator accepts the completion if the session is still
            open (a permanent role field, no epoch);
  fenced    every completion carries the lease epoch; a completion whose epoch
            is older than the session's current epoch is rejected.

Two authority policies are compared for a grant whose path runs through a
node: cached validity with a decision cache of C seconds, versus validity
re-evaluated against the live graph at every consumption. We count accesses
authorized after the path node left.

Outputs exp/results/churn.json with medians and quartiles over 30 seeds.
"""
from __future__ import annotations

import heapq
import json
import random
import statistics
from pathlib import Path

import numpy as np

RESULTS = Path(__file__).with_name("results") / "churn.json"
SEEDS = 30
SIM_SECONDS = 2 * 3600
N_NODES = 6
MEAN_DOWN = 60.0
ARRIVAL_MEAN = 20.0
SERVICE_MEAN = 30.0
HEARTBEAT = 5.0
CONSUMPTION_INTERVAL = 2.0  # how often a session consumes its grant


def run(seed: int, mean_up: float, ttl: float, cache_ttl: float) -> dict:
    rng = random.Random(seed)
    up = [True] * N_NODES
    events: list[tuple[float, int, str, dict]] = []
    counter = 0

    def push(t: float, kind: str, **kw):
        nonlocal counter
        counter += 1
        heapq.heappush(events, (t, counter, kind, kw))

    for n in range(N_NODES):
        push(rng.expovariate(1 / mean_up), "node_down", node=n)
    push(rng.expovariate(1 / ARRIVAL_MEAN), "arrive")
    sessions: dict[int, dict] = {}
    sid = 0
    stats = {"sessions": 0, "completed": 0, "replans": 0, "stale_completions_unfenced_accepted": 0,
             "stale_completions_fenced_rejected": 0, "detect_latencies": [],
             "stale_auth_cached": 0, "stale_auth_live": 0, "lost_unreplannable": 0,
             "max_stale_auth_per_session": 0, "fail_closed_on_dead_path": 0}
    while events:
        t, _, kind, kw = heapq.heappop(events)
        if t > SIM_SECONDS:
            break
        if kind == "node_down":
            n = kw["node"]
            up[n] = False
            push(t + rng.expovariate(1 / MEAN_DOWN), "node_up", node=n)
            for s in sessions.values():
                if s["node"] == n and s["open"]:
                    s["holder_down_at"] = t
                    # coordinator notices when TTL since last heartbeat lapses
                    last_hb = t - (t % HEARTBEAT)
                    push(last_hb + ttl, "lease_expired", sid=s["id"], epoch=s["epoch"])
                if s["grant_path_node"] == n and s["open"]:
                    s["path_broken_at"] = t
        elif kind == "node_up":
            n = kw["node"]
            up[n] = True
            push(t + rng.expovariate(1 / mean_up), "node_down", node=n)
            # a returning holder finishes what it held (unfenced hazard)
            for s in sessions.values():
                if s.get("orig_holder") == n and s["open"] and s.get("orig_epoch") is not None:
                    push(t + max(0.0, s["remaining_at_down"]), "stale_complete", sid=s["id"], epoch=s["orig_epoch"], node=n)
                    s["orig_holder"] = None
        elif kind == "arrive":
            push(t + rng.expovariate(1 / ARRIVAL_MEAN), "arrive")
            ups = [i for i in range(N_NODES) if up[i]]
            if not ups:
                continue
            sid += 1
            stats["sessions"] += 1
            node = rng.choice(ups)
            others = [i for i in ups if i != node] or ups
            svc = rng.expovariate(1 / SERVICE_MEAN)
            sessions[sid] = {"id": sid, "node": node, "epoch": 1, "open": True, "service": svc,
                             "started": t, "grant_path_node": rng.choice(others),
                             "path_broken_at": None, "holder_down_at": None,
                             "orig_holder": None, "orig_epoch": None, "remaining_at_down": 0.0}
            push(t + svc, "complete", sid=sid, epoch=1, node=node)
            push(t + CONSUMPTION_INTERVAL, "consume", sid=sid, cache_until=t + cache_ttl)
        elif kind == "consume":
            s = sessions[kw["sid"]]
            if not s["open"]:
                continue
            if s["path_broken_at"] is not None:
                if t <= kw["cache_until"]:
                    # a cached positive decision still says yes: stale authorisation
                    stats["stale_auth_cached"] += 1
                    s["stale_auth_count"] = s.get("stale_auth_count", 0) + 1
                    stats["max_stale_auth_per_session"] = max(stats["max_stale_auth_per_session"], s["stale_auth_count"])
                else:
                    # cache expired or no cache: live evaluation sees the dead path and
                    # the session fails closed (R5, R8); nothing is authorised
                    s["open"] = False
                    stats["fail_closed_on_dead_path"] += 1
                    continue
            # a positive decision is cached only while the path is live
            cache_until = kw["cache_until"] if t <= kw["cache_until"] else (t + cache_ttl if s["path_broken_at"] is None else kw["cache_until"])
            push(t + CONSUMPTION_INTERVAL, "consume", sid=s["id"], cache_until=cache_until)
        elif kind == "lease_expired":
            s = sessions[kw["sid"]]
            if not s["open"] or kw["epoch"] != s["epoch"]:
                continue
            stats["detect_latencies"].append(t - s["holder_down_at"])
            ups = [i for i in range(N_NODES) if up[i]]
            s["orig_holder"] = s["node"]
            s["orig_epoch"] = s["epoch"]
            s["remaining_at_down"] = max(0.0, s["started"] + s["service"] - s["holder_down_at"])
            if not ups:
                s["open"] = False
                stats["lost_unreplannable"] += 1
                continue
            s["epoch"] += 1
            s["node"] = rng.choice(ups)
            s["started"] = t
            stats["replans"] += 1
            push(t + s["service"], "complete", sid=s["id"], epoch=s["epoch"], node=s["node"])
        elif kind == "complete":
            s = sessions[kw["sid"]]
            if s["open"] and kw["epoch"] == s["epoch"] and up[kw["node"]]:
                s["open"] = False
                stats["completed"] += 1
        elif kind == "stale_complete":
            s = sessions[kw["sid"]]
            if s["open"]:
                stats["stale_completions_unfenced_accepted"] += 1   # unfenced would accept
                stats["stale_completions_fenced_rejected"] += 1     # fenced rejects by epoch
    stats["detect_latency_median"] = statistics.median(stats["detect_latencies"]) if stats["detect_latencies"] else None
    del stats["detect_latencies"]
    return stats


def summarize(rows: list[dict]) -> dict:
    out = {}
    for k in rows[0]:
        vals = [r[k] for r in rows if r[k] is not None]
        if not vals:
            out[k] = None
            continue
        out[k] = {"median": float(np.median(vals)), "q1": float(np.percentile(vals, 25)),
                  "q3": float(np.percentile(vals, 75)), "n": len(vals)}
    return out


def main() -> int:
    configs = []
    for mean_up in [600.0, 3600.0]:
        for ttl in [10.0, 20.0, 60.0]:
            for cache_ttl in [0.0, 30.0, 300.0]:
                rows = [run(seed, mean_up, ttl, cache_ttl) for seed in range(SEEDS)]
                configs.append({"mean_up_s": mean_up, "lease_ttl_s": ttl, "decision_cache_s": cache_ttl,
                                "heartbeat_s": HEARTBEAT, "seeds": SEEDS, "summary": summarize(rows)})
                s = configs[-1]["summary"]
                print(f"up={mean_up:6.0f} ttl={ttl:4.0f} cache={cache_ttl:4.0f} sessions={s['sessions']['median']:.0f} "
                      f"replans={s['replans']['median']:.0f} stale_unfenced={s['stale_completions_unfenced_accepted']['median']:.0f} "
                      f"stale_auth_cached={s['stale_auth_cached']['median']:.0f} detect={s['detect_latency_median']['median'] if s['detect_latency_median'] else None}")
    out = {"evidence_label": "discrete-event simulation of protocol logic with stated distributions; not device behaviour",
           "model": {"nodes": N_NODES, "sim_seconds": SIM_SECONDS, "mean_down_s": MEAN_DOWN, "arrival_mean_s": ARRIVAL_MEAN,
                     "service_mean_s": SERVICE_MEAN, "heartbeat_s": HEARTBEAT, "consumption_interval_s": CONSUMPTION_INTERVAL},
           "configs": configs}
    RESULTS.write_text(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
