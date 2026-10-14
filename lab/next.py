r"""Next steps for a product: iterations, distribution plays, and sales/marketing rules.

    .venv/bin/python lab/next.py salon-rates                       # from an existing map (read-only)
    .venv/bin/python lab/next.py --new "<one-line product idea>" [--url https://...]

Reads maps/<product>.json (the cited customer map), the prediction/outcome ledger,
~/Desktop/panel-backtest/dataset.jsonl (every first touch we sent, with its outcome),
~/.claude/skills/distribution-channel/SKILL.md (the measured channel ledger) and
~/.claude/BUSINESS.md. Writes maps/<product>.next.json and maps/<product>.NEXT.md.
Never writes maps/<product>.json for an existing product.

--new first builds the customer map: a model turns the idea into tool steps + where its
customers talk (subreddits, trade pages); reddit-mining pulls them; lab/evidence.py turns them
into evidence rows; lab/segment_map.py builds the verified map. Then the above.

The model proposes; code grounds. Every iteration and play must cite claims from the map by id,
and the quote + URL shown are copied from the map, never from the model. Every number about past
sends is counted here from the ledgers. Data sources the model names are checked (a path exists,
a URL answers). Any sentence that predicts whether customers will use, buy or reply is cut and
logged (BUSINESS.md rule 2). Each play's first-touch draft is scored by the screen
(lab/screen.py forecaster-v1) and logged to ledger/predictions.jsonl as source "next-draft".
"""
import argparse
import collections
import datetime as dt
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import (EVIDENCE, MAPS, PREDICTIONS, PRICE, ROOT, SONNET, SPEND, append_jsonl,  # noqa: E402
                    claude, first_json, load_env, read_jsonl)


def _obj(props, req=None):
    return {"type": "object", "properties": props, "required": req or list(props), "additionalProperties": False}


_S, _A = {"type": "string"}, lambda t: {"type": "array", "items": t}
NEXT_SCHEMA = _obj({
    "iterations": _A(_obj({"rank": {"type": "integer"}, "change": _S, "the_step": _S, "serves": _A(_S),
                           "ideal_fields": _A(_obj({"field": _S, "answers": _S, "source": _S, "locator": _S,
                                                    "status": {"type": "string", "enum": ["exists", "partial", "missing"]}})),
                           "reality": _S})),
    "plays": _A(_obj({"rank": {"type": "integer"}, "channel": _S, "voucher": _S, "who_vouches": _S,
                      "vouch_cites": _A(_S), "segments": _A(_S), "recipient_source": _S, "ledger_refs": _A(_S),
                      "send_refs": _A(_S), "offer_mode": {"type": "string", "enum": ["visibility", "sale"]},
                      "draft": _obj({"recipient_kind": _S, "org_example": _S, "context": _S, "subject": _S, "body": _S})})),
    "rules": _A(_obj({"rule": _S, "why": _S, "source": _S})),
})


def claude_json(model, system, user, schema, max_tokens, tag):
    """One call with a JSON-schema output format, so the API guarantees parseable JSON
    (free-text JSON broke three times in a row on quoted draft bodies, 2026-10-13)."""
    load_env()
    import anthropic
    r = anthropic.Anthropic().messages.create(
        model=model, max_tokens=max_tokens, system=system, messages=[{"role": "user", "content": user}],
        output_config={"format": {"type": "json_schema", "schema": schema}})
    pi, po = PRICE.get(model, (3.0, 15.0))
    append_jsonl(SPEND, {"tag": tag, "model": model, "in": r.usage.input_tokens, "out": r.usage.output_tokens,
                         "usd": round((r.usage.input_tokens * pi + r.usage.output_tokens * po) / 1e6, 5)})
    if r.stop_reason == "max_tokens":
        raise RuntimeError(f"{tag}: reply cut at max_tokens ({max_tokens})")
    return json.loads("".join(b.text for b in r.content if b.type == "text"))

HOME = pathlib.Path.home()
BUSINESS = HOME / ".claude/BUSINESS.md"
CHANNEL = HOME / ".claude/skills/distribution-channel/SKILL.md"
DATASET = HOME / "Desktop/panel-backtest/dataset.jsonl"
REDDIT_PULL = HOME / ".claude/skills/reddit-mining/scripts/reddit_pull.py"
PRODUCTS_JSON = ROOT / "data/products.json"
FLOOR = {"recipients": 50, "segments": 3}  # BUSINESS.md rule 4

# Sentences that forecast adoption. Cut, never shown (BUSINESS.md rule 2).
VERDICT = re.compile(
    r"\b(will|would|won't|wouldn't|likely to|unlikely to|are going to|should)\s+(probably\s+|likely\s+|definitely\s+)?"
    r"(use|buy|pay|adopt|switch|sign up|reply|respond|love|want|convert|subscribe|purchase|churn)\b"
    r"|\b(strong|weak|clear|no|high|low|real) (demand|appetite|willingness to pay|product.market fit)\b"
    r"|\bwilling to pay\b|\bwill (resonate|land|convert)\b", re.I)

SYSTEM = """You turn a cited customer map into next steps for a product: product iterations,
distribution plays, and sales/marketing rules. You never predict or judge whether anyone will use,
buy, pay for, switch to or reply to anything — that is forbidden (BUSINESS.md rule 2). Understanding
of the customer shapes WHAT gets built and WHAT gets said, never WHETHER. You never invent a customer
fact: cite claim ids from the map. You never state a number unless it is printed in the input."""

PROMPT = """PRODUCT: {name} — {one_liner}
Live: {url}
Tool steps today:
{steps}

CUSTOMER MAP CLAIMS (id | segment | kind | claim | verbatim quote). Cite these ids; nothing else counts as evidence.
{claims}

GAPS (jobs the tool does not do or only partly does; id | segment | job | fit | why):
{gaps}

SEGMENTS: {segments}

CHANNEL LEDGER (id | channel | run | result) — measured, from the distribution-channel skill:
{ledger}

EVERY POSITIVE REPLY WE EVER GOT (id | to | opening | what came back):
{yeses}

PAST SENDS BY PRODUCT AND CHANNEL, counted from our outcome ledger (key | sends | positive | negative | auto | silent):
{sends}

DISTRIBUTION-CHANNEL RULES (verbatim):
{channel_rules}

BUSINESS RULES (verbatim):
{business}

TASK. Return JSON only:
{{
 "iterations": [  // 2-4, ranked best first. Concrete product changes, AI-native (rule 3): the tool DOES a step of their work (reads, compares, qualifies, decides, drafts) instead of showing information. Each must close a GAP or deepen a cited job.
  {{"rank": 1, "change": "<what we build, one sentence, concrete>",
    "the_step": "<the step of their work the tool now does for them, in their words>",
    "serves": ["<gap id G# and/or claim ids C#>"],
    "ideal_fields": [{{"field": "<a field the ideal version needs>", "answers": "<the customer question it answers>",
                       "source": "<named source that would fill it>", "locator": "<a URL or absolute local path to check, or an empty string>",
                       "status": "exists|partial|missing"}}],
    "reality": "<one plain sentence: can reality fill the ideal model? If not, name the field that fails and say abandon or reframe (rule 5). Never shrink the model to what is easy.>"}}
 ],
 "plays": [  // 2-4 distribution plays, ranked by strength of voucher (distribution-channel axiom), not by guessed response.
  {{"rank": 1, "channel": "<concrete channel>", "voucher": "obligation|super user|person|physical|platform|their own record",
    "who_vouches": "<who already stands in front of this segment, or what record obliges the reader>",
    "vouch_cites": ["<claim ids that show this voucher exists, e.g. a vouchers claim>"],
    "segments": ["<at least 3 segment names from SEGMENTS when the map has 3, so the batch meets the floor>"],
    "recipient_source": "<where 50+ NAMED recipients, each with their own public record, come from>",
    "ledger_refs": ["<L# / Y# rows that are the closest past runs of this channel>"],
    "send_refs": ["<keys from PAST SENDS that are the most similar sends>"],
    "offer_mode": "visibility|sale",
    "draft": {{"recipient_kind": "<who it goes to>", "org_example": "<an example org from the evidence, or a bracketed slot>",
               "context": "<their own public record this opens on>",
               "subject": "<subject>", "body": "<4-7 sentences. Rule 11: the first two sentences quote the reader's own public record (use a real record from the claims when one fits, else a [bracketed slot]). Ask for nothing or only what they owe. Never open on us. Plain words, signed Aidan.>"}}}}
 ],
 "rules": [  // 3-6 sales/marketing rules specific to THIS product and its segments
  {{"rule": "<imperative>", "why": "<the reason, with the measured fact it rests on>", "source": "<'BUSINESS.md rule N' | 'distribution-channel rule N' | ledger id | claim id>"}}
 ]
}}"""


# ---------- inputs ----------

def section(md, start, stop="\n## "):
    i = md.find(start)
    if i < 0:
        return ""
    j = md.find(stop, i + len(start))
    return md[i:j if j > 0 else None]


def md_table(text):
    rows = []
    for line in text.splitlines():
        if line.startswith("|") and not re.match(r"^\|[\s\-|]+\|$", line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(cells)
    return rows[1:]  # drop header


def channel_ledger():
    md = CHANNEL.read_text()
    led = [{"id": f"L{i+1}", "channel": r[0], "run": r[1], "result": r[2], "source": r[3] if len(r) > 3 else ""}
           for i, r in enumerate(md_table(section(md, "## The ledger")))]
    yes = [{"id": f"Y{i+1}", "sent": r[0], "to": r[1], "opening": r[2], "came_back": r[3]}
           for i, r in enumerate(md_table(section(md, "## What every yes had in common")))]
    rules = section(md, "## Rules, each with its why")
    return led, yes, rules


def past_sends():
    """(product|channel) -> outcome counts, from every first touch we ever sent + live screens."""
    c = collections.defaultdict(collections.Counter)
    for r in read_jsonl(DATASET):
        c[f"{r['product']}|{r['channel']}"][r["outcome"]] += 1
    from outcomes import latest_outcomes
    lo = latest_outcomes()
    for p in read_jsonl(PREDICTIONS):
        if p.get("source") == "screen" and p["id"] in lo:
            c[f"{p['product']}|{p.get('channel', 'email')} (screened)"][lo[p["id"]]["outcome"]] += 1
    return {k: {"sends": sum(v.values()), "positive": v["positive_reply"] + v["reply_unlabelled"],
                "negative": v["negative_reply"], "auto": v["auto_reply"], "silent": v["silent"]}
            for k, v in c.items()}


def map_claims(m):
    claims, gaps = {}, {}
    n = 0
    for s in m["segments"]:
        for kind in ("jobs", "pains", "workarounds", "wants", "words", "vouchers"):
            for it in s.get(kind) or []:
                n += 1
                claims[f"C{n}"] = {"segment": s["name"], "kind": kind, "text": it["text"], "cites": it["cites"]}
    jobs = {(c["segment"], c["text"]): cid for cid, c in claims.items() if c["kind"] == "jobs"}
    for i, j in enumerate([j for j in m["job_map"] if not j.get("step") or j.get("fit") in ("none", "partial")]):
        gaps[f"G{i+1}"] = {**j, "claim": jobs.get((j["segment"], j["job"]))}
    return claims, gaps


# ---------- grounding ----------

def cite_view(cid, claims, gaps):
    if cid in claims:
        c = claims[cid]
        q = c["cites"][0]
        return {"id": cid, "segment": c["segment"], "kind": c["kind"], "claim": c["text"],
                "quote": q["quote"], "url": q["url"], "date": q.get("date")}
    if cid in gaps:
        g = gaps[cid]
        out = {"id": cid, "segment": g["segment"], "kind": "gap", "claim": g["job"], "fit": g.get("fit"),
               "why": g.get("why")}
        if g.get("claim") in claims:
            q = claims[g["claim"]]["cites"][0]
            out.update(quote=q["quote"], url=q["url"], date=q.get("date"))
        return out
    return None


def check_locator(loc):
    if not loc or not isinstance(loc, str):
        return "not checked (no locator given)"
    if loc.startswith("/") or loc.startswith("~"):
        p = pathlib.Path(loc).expanduser()
        return f"path exists ({p.stat().st_size:,} bytes)" if p.exists() else "path MISSING"
    if loc.startswith("http"):
        try:
            req = urllib.request.Request(loc, method="GET", headers={"User-Agent": "Mozilla/5.0 customer-lab"})
            with urllib.request.urlopen(req, timeout=12) as r:
                return f"url answered {r.status}"
        except urllib.error.HTTPError as e:
            return f"url answered {e.code}"
        except Exception as e:
            return f"url unreachable ({type(e).__name__})"
    return "not checked (not a path or URL)"


def strip_verdicts(obj, flags, where=""):
    """Cut any sentence that forecasts adoption; record what was cut."""
    if isinstance(obj, dict):
        return {k: strip_verdicts(v, flags, f"{where}.{k}") for k, v in obj.items()}
    if isinstance(obj, list):
        return [strip_verdicts(v, flags, f"{where}[{i}]") for i, v in enumerate(obj)]
    if isinstance(obj, str) and VERDICT.search(obj) and ".draft." not in where:
        kept = []
        for sent in re.split(r"(?<=[.!?])\s+", obj):
            if VERDICT.search(sent):
                flags.append({"where": where, "cut": sent})
            else:
                kept.append(sent)
        return " ".join(kept) or "[cut: verdict on use, BUSINESS.md rule 2]"
    return obj


# ---------- the run ----------

def run_next(product, P=None, screen=True, reuse=False):
    m = json.loads((MAPS / f"{product}.json").read_text())
    P = P or {k: m[k] for k in ("name", "live_url", "one_liner", "steps")}
    claims, gaps = map_claims(m)
    led, yes, ch_rules = channel_ledger()
    sends = past_sends()
    seg_names = [s["name"] for s in m["segments"]]
    prompt = PROMPT.format(
        name=P["name"], one_liner=P["one_liner"], url=P.get("live_url") or "(not built yet)",
        steps="\n".join(f"{s['id']}: {s['verb_object']}" for s in P["steps"]),
        claims="\n".join(f"{cid} | {c['segment']} | {c['kind']} | {c['text']} | \"{c['cites'][0]['quote']}\""
                         for cid, c in claims.items()),
        gaps="\n".join(f"{gid} | {g['segment']} | {g['job']} | {g.get('fit')} | {g.get('why')}"
                       for gid, g in gaps.items()) or "(none recorded)",
        segments=json.dumps(seg_names),
        ledger="\n".join(f"{r['id']} | {r['channel']} | {r['run'][:300]} | {r['result'][:300]}" for r in led),
        yeses="\n".join(f"{r['id']} | {r['to']} | {r['opening'][:250]} | {r['came_back']}" for r in yes),
        sends="\n".join(f"{k} | {v['sends']} | {v['positive']} | {v['negative']} | {v['auto']} | {v['silent']}"
                        for k, v in sorted(sends.items())),
        channel_rules=ch_rules, business=BUSINESS.read_text())
    (ROOT / "data/raw").mkdir(parents=True, exist_ok=True)
    cached = ROOT / f"data/raw/next_{product}.json"
    if reuse and cached.exists():
        out = json.loads(cached.read_text())
    else:
        out = claude_json(SONNET, SYSTEM, prompt, NEXT_SCHEMA, max_tokens=12000, tag=f"next:{product}")
        cached.write_text(json.dumps(out, indent=1, ensure_ascii=False))

    flags, stats = [], collections.Counter()
    out = strip_verdicts(out, flags)

    iters = []
    for it in sorted(out.get("iterations", []), key=lambda x: x.get("rank", 9)):
        serves = [v for v in (cite_view(c, claims, gaps) for c in it.get("serves") or []) if v]
        stats["iter_refs_bad"] += len(it.get("serves") or []) - len(serves)
        if not serves:
            stats["iterations_dropped_uncited"] += 1
            continue
        for f in it.get("ideal_fields") or []:
            f["checked"] = check_locator(f.get("locator"))
            if f.get("status") == "exists" and ("MISSING" in f["checked"] or re.search(r"answered [45]|unreachable", f["checked"])):
                f["status"] = "claimed exists; check failed"
        iters.append({**it, "serves": serves, "rank": len(iters) + 1})

    plays = []
    led_by = {r["id"]: r for r in led + yes}
    for pl in sorted(out.get("plays", []), key=lambda x: x.get("rank", 9)):
        vc = [v for v in (cite_view(c, claims, gaps) for c in pl.get("vouch_cites") or []) if v]
        segs = [s for s in pl.get("segments") or [] if s in seg_names]
        past = {k: sends[k] for k in pl.get("send_refs") or [] if k in sends}
        tot = collections.Counter()
        for v in past.values():
            tot.update(v)
        plays.append({
            **{k: pl.get(k) for k in ("channel", "voucher", "who_vouches", "recipient_source", "offer_mode")},
            "rank": len(plays) + 1,
            "vouch_evidence": vc,
            "segments": segs,
            "floor": {"recipients": FLOOR["recipients"], "segments_required": FLOOR["segments"],
                      "segments_named": len(segs),
                      "meets_segment_floor": len(segs) >= FLOOR["segments"],
                      "note": "BUSINESS.md rule 4: 50 delivered recipients from 3+ segments; fewer is a probe."},
            "past_runs": [led_by[r] for r in pl.get("ledger_refs") or [] if r in led_by],
            "past_sends": past,
            "past_sends_total": dict(tot) if past else None,
            "draft": pl.get("draft") or {},
        })

    rules = out.get("rules", [])

    if screen:
        from screen import METHOD, forecast
        for pl in plays:
            d = pl["draft"]
            if not d.get("body"):
                continue
            method = METHOD
            for attempt in range(3):  # a non-JSON forecast reply is retried, never guessed
                try:
                    # Same pinned prompt. The 60-token cap of the backtest sometimes returns an empty
                    # reply (seen 2026-10-13); the last try lifts the cap and says so in the method name.
                    mt = 60 if attempt < 2 else 400
                    p_reply, p_click = forecast(d.get("recipient_kind", ""), d.get("org_example", ""),
                                                d.get("context", ""), d.get("subject", ""), d["body"], max_tokens=mt)
                    method = METHOD if mt == 60 else METHOD + " (max_tokens 400)"
                    break
                except (AttributeError, ValueError, KeyError) as e:
                    err = f"{type(e).__name__}: {e}"
            else:
                pl["screen"] = {"error": f"forecast unparseable 3 times ({err}); re-screen with lab/screen.py"}
                continue
            pid = "nx_" + hashlib.sha1(f"{product}|{d.get('subject')}|{d['body']}".encode()).hexdigest()[:12]
            pl["screen"] = {"prediction_id": pid, "p_reply": p_reply, "p_click": p_click, "method": method}
            if not any(r["id"] == pid for r in read_jsonl(PREDICTIONS)):
                append_jsonl(PREDICTIONS, {
                    "id": pid, "made_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                    "source": "next-draft", "method": method, "model": SONNET, "product": product,
                    "email": "", "name": "", "kind": d.get("recipient_kind"), "org": d.get("org_example"),
                    "context": d.get("context"), "subject": d.get("subject"),
                    "body_sha": hashlib.sha1(d["body"].encode()).hexdigest()[:12], "link": "",
                    "channel": pl.get("channel"), "p_reply": p_reply, "p_click": p_click,
                    "note": "draft from lab/next.py; no recipient yet. Re-screen with lab/screen.py once a named "
                            "recipient and their own record are filled in."})

    result = {
        "product": product, "name": P["name"], "made_at": dt.date.today().isoformat(),
        "iterations": iters, "plays": plays, "rules": rules,
        "grounding": {"map": f"maps/{product}.json", "claims_offered": len(claims), "gaps_offered": len(gaps),
                      "channel_ledger_rows": len(led), "positive_reply_rows": len(yes),
                      "past_send_keys": len(sends), **stats,
                      "verdicts_cut": flags, "model": SONNET},
        "never": "No line here says whether anyone will use, buy or reply (BUSINESS.md rule 2). "
                 "Screen scores rank drafts against each other; they are not a forecast of the product.",
    }
    (MAPS / f"{product}.next.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    (MAPS / f"{product}.NEXT.md").write_text(render_md(result))
    return result


def render_md(r):
    L = [f"# Next: {r['name']}", "", f"_{r['made_at']} · `lab/next.py` · from `{r['grounding']['map']}`. "
         "Nothing here says whether anyone will use or buy it (BUSINESS.md rule 2)._", "", "## Iterations", ""]
    for it in r["iterations"]:
        L += [f"### {it['rank']}. {it['change']}", "", f"**The step it does:** {it.get('the_step', '')}", ""]
        for s in it["serves"]:
            q = f" — \"{s['quote']}\" ({s['url']})" if s.get("quote") else ""
            L.append(f"- serves {s['id']} ({s['segment']}, {s['kind']}): {s['claim']}{q}")
        L += ["", "| field | answers | source | status | checked |", "|---|---|---|---|---|"]
        for f in it.get("ideal_fields") or []:
            L.append(f"| {f.get('field')} | {f.get('answers')} | {f.get('source')} | {f.get('status')} | {f.get('checked')} |")
        L += ["", f"**Reality:** {it.get('reality', '')}", ""]
    L += ["## Distribution plays", ""]
    for p in r["plays"]:
        L += [f"### {p['rank']}. {p['channel']} — voucher: {p['voucher']}", "",
              f"**Who vouches:** {p['who_vouches']}", ""]
        for v in p["vouch_evidence"]:
            q = f" — \"{v['quote']}\" ({v['url']})" if v.get("quote") else ""
            L.append(f"- {v['id']} ({v['segment']}): {v['claim']}{q}")
        fl = p["floor"]
        L += ["", f"**Floor:** {fl['recipients']} recipients, {fl['segments_required']} segments. Named here: "
              f"{', '.join(p['segments']) or 'none'} ({fl['segments_named']}){'' if fl['meets_segment_floor'] else ' — UNDER the floor; a batch from these is a probe'}.",
              f"**Recipients from:** {p['recipient_source']}", f"**Offer:** {p['offer_mode']}", "",
              "**What we have for similar sends (counted from the ledger):**"]
        for k, v in p["past_sends"].items():
            L.append(f"- `{k}`: {v['sends']} sent, {v['positive']} positive, {v['negative']} negative, {v['silent']} silent")
        for run in p["past_runs"]:
            if "channel" in run:
                L.append(f"- {run['id']} {run['channel']}: {run['result']}")
            else:
                L.append(f"- {run['id']} (a yes) {run['to']}: {run['came_back']}")
        if not p["past_sends"] and not p["past_runs"]:
            L.append("- none: this channel has never been run")
        d = p["draft"]
        L += ["", f"**First-touch draft** (to: {d.get('recipient_kind')}; opens on: {d.get('context')})", "",
              f"> **{d.get('subject', '')}**", ">"] + [f"> {ln}" for ln in (d.get("body") or "").splitlines()] + [""]
        if p.get("screen", {}).get("error"):
            L += [f"Screen: {p['screen']['error']}", ""]
        elif p.get("screen"):
            s = p["screen"]
            L += [f"Screen ({s['method']}): P(reply) {s['p_reply']:.0%}, P(click) {s['p_click']:.0%}; logged as "
                  f"`{s['prediction_id']}`. Ranks drafts against each other, not a forecast of the product.", ""]
    L += ["## Rules", ""]
    for i, ru in enumerate(r["rules"], 1):
        L += [f"{i}. **{ru.get('rule')}** — {ru.get('why')} _({ru.get('source')})_"]
    g = r["grounding"]
    L += ["", "---", f"Grounding: {g['claims_offered']} cited claims and {g['gaps_offered']} gaps offered; "
          f"{g['channel_ledger_rows']} channel-ledger rows; {len(g['verdicts_cut'])} verdict sentences cut; "
          f"{g.get('iterations_dropped_uncited', 0)} uncited iterations dropped."]
    return "\n".join(L) + "\n"


# ---------- --new: idea -> evidence -> map ----------

NEW_PROMPT = """A product idea: "{idea}"{url}

Return JSON only:
{{"slug": "<kebab-case, 2-4 words>", "name": "<short name>", "one_liner": "<the idea, one line, plain>",
  "steps": [{{"id": "N1", "verb_object": "<a step of the customer's work the tool does>"}}],  // 2-4
  "subreddits": [{{"sub": "<exact subreddit name, no r/>", "speaker": "<who posts there, e.g. 'scrap metal dealer'>"}}],  // 4-6 real, active subs where the BUYERS and the people who already serve them talk shop
  "keywords": ["<lowercase words/phrases their posts would contain when they talk about this job>"],  // 8-15
  "web": [{{"url": "<a real public page written by a buyer, a trade association or a super user of this buyer>", "speaker": "<who wrote it>"}}]  // 0-3
}}"""


def reddit_pull(slug, subs, keywords, after):
    procs = []
    out_dir = ROOT / "data/raw/reddit"
    out_dir.mkdir(parents=True, exist_ok=True)
    for s in subs:
        f = out_dir / f"{slug}_{s}.json"
        if f.exists() and f.stat().st_size > 2:
            continue
        cmd = [sys.executable, str(REDDIT_PULL), "--subreddits", s, "--queries", *keywords,
               "--after", after, "--top", "40", "--comments", "5"]
        procs.append((s, f, subprocess.Popen(cmd, stdout=open(f, "w"), stderr=open(out_dir / f"{slug}_{s}.log", "w"))))
    for s, f, p in procs:
        try:
            p.wait(timeout=900)
        except subprocess.TimeoutExpired:
            p.kill()
            print(f"  r/{s}: timed out")
        print(f"  r/{s}: {f.stat().st_size:,} bytes")


def fetch_web(pages):
    d = ROOT / "data/raw/web"
    d.mkdir(parents=True, exist_ok=True)
    for url in pages:
        f = d / (hashlib.md5((url + "\n").encode()).hexdigest()[:10] + ".html")
        if not f.exists():
            subprocess.run(["curl", "-sL", "-m", "25", "-A", "Mozilla/5.0", "-o", str(f), url])


def new_product(idea, url, after):
    raw = claude(SONNET, "You scope a product idea into where its customers talk. JSON only.",
                 NEW_PROMPT.format(idea=idea, url=f"\nLive: {url}" if url else ""), max_tokens=1500, tag="next:new")
    spec = first_json(raw)
    slug = re.sub(r"[^a-z0-9-]+", "-", spec["slug"].lower()).strip("-")
    products = json.loads(PRODUCTS_JSON.read_text())
    if slug in products and (MAPS / f"{slug}.json").exists():
        print(f"{slug}: map exists, reusing it (delete maps/{slug}.json to rebuild)")
        return slug, products[slug]
    P = {"name": spec["name"], "live_url": url or "", "one_liner": spec["one_liner"], "idea": idea,
         "dataset_products": [], "steps": [{**s, "url": url or ""} for s in spec["steps"]],
         "sources": {"subreddits": spec["subreddits"], "keywords": spec["keywords"], "web": spec.get("web") or []}}
    products[slug] = P
    PRODUCTS_JSON.write_text(json.dumps(products, indent=2, ensure_ascii=False) + "\n")
    print(f"{slug}: {P['name']} — pulling r/{', r/'.join(s['sub'] for s in spec['subreddits'])}")

    import evidence
    subs = [s["sub"] for s in spec["subreddits"]]
    reddit_pull(slug, subs, spec["keywords"], after)
    fetch_web([w["url"] for w in P["sources"]["web"]])
    rx = "|".join(re.escape(k) for k in spec["keywords"])
    evidence.REDDIT[slug] = slug
    evidence.KEYWORDS[slug] = rx
    evidence.SPEAKER.update({s["sub"]: s["speaker"] for s in spec["subreddits"]})
    evidence.WEB[slug] = {w["url"]: w["speaker"] for w in P["sources"]["web"]}
    rows = evidence.from_reddit(slug, rx) + evidence.from_web(slug, rx)
    uniq = {r["id"]: r for r in rows}
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with (EVIDENCE / f"{slug}.jsonl").open("w") as f:
        for r in uniq.values():
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"  {len(uniq)} evidence rows {dict(collections.Counter(r['source_kind'] for r in uniq.values()))}")
    if len(uniq) < 15:
        sys.exit(f"only {len(uniq)} evidence rows: too thin to map customers from. Sources tried are in "
                 f"data/products.json under '{slug}'. Not mapping from nothing.")
    import segment_map
    segment_map.PRODUCTS[slug] = P
    segment_map.build(slug)
    return slug, P


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("product", nargs="?")
    ap.add_argument("--new", help="a one-line product idea: build its customer map first")
    ap.add_argument("--url", default="", help="live URL for a --new idea, if it exists")
    ap.add_argument("--after", default="2024-10-01", help="reddit pull start date for --new")
    ap.add_argument("--no-screen", action="store_true")
    ap.add_argument("--reuse", action="store_true", help="re-ground the last model reply (data/raw/next_<p>.json), $0")
    a = ap.parse_args()
    if a.new:
        product, P = new_product(a.new, a.url, a.after)
    elif a.product:
        product, P = a.product, None
        if not (MAPS / f"{product}.json").exists():
            sys.exit(f"no maps/{product}.json; run lab/segment_map.py {product} or use --new")
    else:
        ap.error("give a product or --new")
    r = run_next(product, P, screen=not a.no_screen, reuse=a.reuse)
    print(f"\n{product}: {len(r['iterations'])} iterations, {len(r['plays'])} plays, {len(r['rules'])} rules; "
          f"{len(r['grounding']['verdicts_cut'])} verdict sentences cut")
    if r["iterations"]:
        print(f"#1 iteration: {r['iterations'][0]['change']}")
    if r["plays"]:
        p = r["plays"][0]
        print(f"#1 play: {p['channel']} (voucher: {p['voucher']})"
              + (f"; draft P(reply) {p['screen']['p_reply']:.0%}" if "p_reply" in p.get("screen", {}) else ""))
    print(f"-> maps/{product}.next.json, maps/{product}.NEXT.md")


if __name__ == "__main__":
    main()
