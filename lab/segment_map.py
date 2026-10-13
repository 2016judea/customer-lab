"""Build a product's evidence-cited segment map + jobs->tool-step map.

    .venv/bin/python lab/segment_map.py salon-rates|pt-rates|obsolete-parts [--max-rows 260]

The model (claude-sonnet-5-5) READS evidence and proposes structure. It is never the source
of a claim: every trait it returns must quote an evidence row, and the quote is checked here
as a literal (whitespace/quote-normalised) substring of that row. Claims whose quotes fail
are dropped and counted. Numbers on the page come from data (facts()), never from the model.

Output maps/<product>.json.
"""
import argparse
import collections
import json
import pathlib
import random
import sqlite3
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import EVIDENCE, MAPS, ROOT, SONNET, claude, first_json, norm, read_jsonl  # noqa: E402

HOME = pathlib.Path.home()
PRODUCTS = json.load((ROOT / "data/products.json").open())
DATASET = HOME / "Desktop/panel-backtest/dataset.jsonl"

SYSTEM = """You map customers from evidence. You never invent. You never predict whether anyone
will use, buy, reply to or like a product — that is forbidden here; understanding only shapes
WHAT gets built and WHAT gets said."""

PROMPT = """PRODUCT: {name} — {one_liner}
Live: {url}
What the tool does today (tool steps):
{steps}

MEASURED FACTS (counted from data, safe to cite as numbers):
{facts}

EVIDENCE ROWS (id | speaker kind | source | text). These are the ONLY facts you may use.
{rows}

TASK
1. Find 3-5 SEGMENTS of people this product serves or could serve, chosen so they DIFFER
   from each other (different job, pain, workaround, words, or who they trust). A segment
   must be visible in the evidence; prefer segments whose own words appear.
2. For each segment give: name (plain, 2-5 words), who (one line), and lists of
   jobs, pains, workarounds, wants, words, vouchers. Each list item is
   {{"text": "<your one-line claim, plain language>", "cites": [{{"id": "<evidence id>", "quote": "<EXACT words copied from that row, 6-30 words>"}}]}}.
   - "words": text = a phrase they use themselves (copy it), cite it.
   - "vouchers": who/what they already trust or ask (an association, a vendor, peers, a forum, a broker).
   - quotes must be copied character-for-character from the cited row. If you cannot cite it, leave it out.
   - No quantities in claims ("most", "many", percentages, counts) unless copied from MEASURED FACTS.
   - Skip any list you can't evidence rather than padding it.
   - Someone's response to OUR offer (a decline, a forward, silence) is never a trait of theirs.
     Only what they said about their own work counts.
3. questions: 2-4 questions this segment would ask a stranger offering this tool, each
   {{"text": ..., "cites": [...]}} if evidenced, else {{"text": ..., "hypothesis": true}}.
4. job_map: for EVERY job of every segment: {{"segment": name, "job": job text, "step": "<step id or null>",
   "fit": "full|partial|none", "why": "<at most 15 words>"}}. null/none = a GAP: a job our tool does not do.
5. surprise: the single finding in this evidence most likely to change what we build or say,
   one sentence, with cites.

Return JSON only: {{"segments": [...], "job_map": [...], "surprise": {{"text": ..., "cites": [...]}}}}"""


def facts(product):
    """Numbers from data, never from the model."""
    out = []
    rows = [json.loads(l) for l in DATASET.open()]
    mine = [r for r in rows if r["product"] in PRODUCTS[product]["dataset_products"]]
    by = collections.defaultdict(collections.Counter)
    for r in mine:
        by[r["recipient_kind"]][r["outcome"]] += 1
    for kind, c in sorted(by.items(), key=lambda kv: -sum(kv[1].values())):
        n = sum(c.values())
        out.append({"kind": "sends", "segment_hint": kind, "n": n, "positive": c["positive_reply"],
                    "text": f"{kind}: we emailed {n}, {c['positive_reply']} replied with substance",
                    "source": "panel-backtest/dataset.jsonl"})
    if product == "salon-rates":
        db = sqlite3.connect(f"file:{HOME}/Desktop/salon-rates/pipeline/salon.db?mode=ro", uri=True)
        q = """select b.business_type, count(distinct b.business_id),
                      sum(l.price_type='fixed'), sum(l.price_type='from'), sum(l.price_type in ('range','consult')), count(*)
               from business b join service_listing l using(business_id) group by 1 order by 2 desc"""
        for bt, shops, fixed, frm, rng, n in db.execute(q):
            out.append({"kind": "menus", "segment_hint": bt, "n": shops,
                        "text": f"{bt}: {shops} shops publish menus; of their {n} prices, "
                                f"{fixed/n:.0%} fixed, {frm/n:.0%} 'from', {rng/n:.0%} a range or 'consult'",
                        "source": "salon-rates DB (shops' own published menus, 2026-10-05)"})
    return out


def pick_rows(ev, cap):
    """Keep every non-reddit row (rarer, closer to the buyer); sample reddit to fill the cap."""
    random.seed(11)
    core = [r for r in ev if not r["source_kind"].startswith("reddit")]
    red = [r for r in ev if r["source_kind"].startswith("reddit")]
    random.shuffle(red)
    return core[:cap] + red[: max(0, cap - len(core))]


def verify(item, by_id, stats):
    good = []
    for c in item.get("cites") or []:
        r = by_id.get(c.get("id"))
        if r and c.get("quote") and len(norm(c["quote"])) >= 12 and norm(c["quote"]) in norm(r["text"]):
            good.append({"id": r["id"], "quote": c["quote"], "url": r["url"], "date": r["date"],
                         "source_kind": r["source_kind"], "speaker_kind": r["speaker_kind"]})
        else:
            stats["bad_cites"] += 1
    stats["cites"] += len(item.get("cites") or [])
    return good


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("product")
    ap.add_argument("--max-rows", type=int, default=260)
    a = ap.parse_args()
    P = PRODUCTS[a.product]
    ev = read_jsonl(EVIDENCE / f"{a.product}.jsonl")
    rows = pick_rows(ev, a.max_rows)
    by_id = {r["id"]: r for r in rows}
    rows_txt = "\n".join(f"{r['id']} | {r['speaker_kind']} | {r['source_kind']} | {r['text'][:700]}" for r in rows)
    steps = "\n".join(f"{s['id']}: {s['verb_object']}" for s in P["steps"])
    prompt = PROMPT.format(name=P["name"], one_liner=P["one_liner"], url=P["live_url"], steps=steps, rows=rows_txt,
                           facts="\n".join("- " + f["text"] for f in facts(a.product)))
    (ROOT / "data/raw").mkdir(parents=True, exist_ok=True)
    for attempt in range(3):  # a malformed JSON reply is retried, never hand-patched
        raw = claude(SONNET, SYSTEM, prompt, max_tokens=20000, tag=f"segment_map:{a.product}")
        (ROOT / f"data/raw/segment_map_{a.product}.txt").write_text(raw)
        try:
            out = first_json(raw)
            break
        except json.JSONDecodeError as e:
            print(f"  attempt {attempt + 1}: bad JSON ({e}); retrying")
    else:
        sys.exit("no parseable JSON after 3 attempts")

    stats = collections.Counter()
    segs = []
    for s in out.get("segments", []):
        seg = {"name": s.get("name"), "who": s.get("who")}
        for field in ("jobs", "pains", "workarounds", "wants", "words", "vouchers"):
            kept = []
            for it in s.get(field) or []:
                stats["claims"] += 1
                g = verify(it, by_id, stats)
                if g:
                    kept.append({"text": it["text"], "cites": g})
                else:
                    stats["dropped_claims"] += 1
            seg[field] = kept
        qs = []
        for q in s.get("questions") or []:
            g = verify(q, by_id, stats) if q.get("cites") else []
            qs.append({"text": q["text"], "cites": g, "hypothesis": not g})
        seg["questions"] = qs
        segs.append(seg)
    kept_jobs = {(s["name"], j["text"]) for s in segs for j in s["jobs"]}
    jm = [j for j in out.get("job_map", []) if (j.get("segment"), j.get("job")) in kept_jobs]
    sur = out.get("surprise") or {}
    sur_c = verify(sur, by_id, stats) if sur else []
    result = {
        "product": a.product, **{k: P[k] for k in ("name", "live_url", "one_liner", "steps")},
        "segments": segs, "job_map": jm,
        "surprise": {"text": sur.get("text"), "cites": sur_c} if sur_c else None,
        "facts": facts(a.product),
        "evidence": {"rows_available": len(ev), "rows_read": len(rows),
                     "by_source": dict(collections.Counter(r["source_kind"] for r in rows))},
        "verification": dict(stats), "model": SONNET,
    }
    MAPS.mkdir(exist_ok=True)
    (MAPS / f"{a.product}.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    print(f"{a.product}: {len(segs)} segments; claims {stats['claims']}, dropped {stats['dropped_claims']}; "
          f"cites {stats['cites']}, failed verbatim check {stats['bad_cites']}; gaps "
          f"{sum(1 for j in jm if not j.get('step') or j.get('fit') == 'none')}/{len(jm)} jobs")


if __name__ == "__main__":
    main()
