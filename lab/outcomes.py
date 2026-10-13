"""Outcome reader: score every logged prediction against what actually happened.

    .venv/bin/python lab/outcomes.py backfill      # once: today's 419 blind forecasts + their outcomes
    .venv/bin/python lab/outcomes.py pull          # read replies (Mail.app's copy of Zoho) + visits (PostHog)
    .venv/bin/python lab/outcomes.py label <prediction-id|email> positive_reply [--note "..."]
    .venv/bin/python lab/outcomes.py calibration   # predicted vs actual, AUC as positives accrue

Replies come from Mail.app's local Envelope Index (the Zoho account is attached over IMAP,
business-inbox skill), opened read-only. A reply is counted only from the exact recipient
address after the send; an out-of-office is recognised by subject; every other human reply
lands as `reply_unlabelled` until `label` says positive or negative — a model never labels
an outcome. Visits come from PostHog (site-analytics skill) on the recipient's own link.
"""
import argparse
import csv
import datetime as dt
import json
import os
import pathlib
import random
import re
import sqlite3
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import OUTCOMES, PREDICTIONS, append_jsonl, auc, load_env, read_jsonl  # noqa: E402

HOME = pathlib.Path.home()
BACKTEST = HOME / "Desktop/panel-backtest"
MAIL = HOME / "Library/Mail/V10/MailData/Envelope Index"
LEDGER_GLOBS = [HOME / "Desktop/bricks/data/outreach", HOME / "Desktop/the-google-of-obsolete-infrastructure-parts/outreach",
                HOME / "Desktop/msp-house-index/outreach"]
AUTO = re.compile(r"automatic reply|auto(-| )?reply|out of (the )?office|ooo|away from|vacation|"
                  r"we received your|ticket|delivery status|undeliverable|returned mail", re.I)
POSITIVE = {"positive_reply", "reply_unlabelled"}  # an unlabelled human reply counts until labelled


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# ---------- backfill ----------

def ledger_emails():
    """slug -> email from every tokens.csv ledger on disk."""
    out = {}
    for root in LEDGER_GLOBS:
        for p in root.rglob("tokens.csv") if root.exists() else []:
            try:
                for r in csv.DictReader(p.open()):
                    if r.get("slug") and r.get("email"):
                        out[r["slug"]] = r["email"].strip().lower()
            except Exception:
                pass
    return out


def mail_db():
    return sqlite3.connect(f"file:{MAIL}?mode=ro", uri=True) if MAIL.exists() else None


def sent_recipient_by_subject(db, subject):
    if not db or not subject:
        return None
    q = """select a.address from messages m join subjects s on m.subject=s.ROWID
           join mailboxes b on m.mailbox=b.ROWID join recipients r on r.message=m.ROWID
           join addresses a on r.address=a.ROWID
           where s.subject=? and b.url like '%Sent%' and r.type=0"""
    rows = {x[0].lower() for x in db.execute(q, (subject,))}
    return rows.pop() if len(rows) == 1 else None


def backfill():
    have = {r["id"] for r in read_jsonl(PREDICTIONS)}
    rows = {json.loads(l)["id"]: json.loads(l) for l in open(BACKTEST / "dataset.jsonl")}
    scored = json.load(open(BACKTEST / "results/individual_scored.json"))
    emails, db = ledger_emails(), mail_db()
    added = found = 0
    for s in scored:
        if s.get("p_fc_reply") is None:
            continue
        pid = "bt_" + s["id"]
        if pid in have:
            continue
        r = rows[s["id"]]
        email = emails.get(s["id"].split(":", 1)[1]) or sent_recipient_by_subject(db, r["subject"])
        found += bool(email)
        append_jsonl(PREDICTIONS, {
            "id": pid, "made_at": "2026-10-13T00:00:00+00:00", "source": "backfill-blind",
            "method": "forecaster-v1", "model": "claude-sonnet-5-5", "product": r["product"],
            "email": email, "name": r.get("recipient_person"), "kind": r["recipient_kind"],
            "org": r["recipient_org"], "subject": r["subject"], "link": r.get("link") or "",
            "channel": r["channel"], "sent_on": r["sent_on"],
            "p_reply": s["p_fc_reply"], "p_click": s["p_fc_click"],
            "note": "scored blind on 2026-10-13, after the send; panel-backtest/individual.py"})
        append_jsonl(OUTCOMES, {"prediction_id": pid, "observed_at": "2026-10-13T00:00:00+00:00",
                                "outcome": r["outcome"], "source": "panel-backtest/dataset.jsonl",
                                "verified": r.get("outcome_verified"), "note": r.get("outcome_note", "")[:300]})
        added += 1
    print(f"backfilled {added} predictions; {found} carry a recipient address for future inbox reads")


# ---------- pull ----------

def inbox_replies(db, email, after_ts):
    q = """select datetime(m.date_received,'unixepoch'), s.subject from messages m
           join addresses a on m.sender=a.ROWID join subjects s on m.subject=s.ROWID
           where lower(a.address)=? and m.date_received>? order by m.date_received"""
    return db.execute(q, (email, after_ts)).fetchall()


def posthog_visits(link, after_iso):
    load_env()
    key, proj = os.environ.get("POSTHOG_PERSONAL_API_KEY"), os.environ.get("POSTHOG_PROJECT_ID")
    if not (key and proj and link):
        return None
    m = re.match(r"https?://([^/]+)(.*)", link)
    host, path = m.group(1), m.group(2) or "/"
    frag = path.split("#", 1)[1] if "#" in path else None
    needle = frag or path.split("?", 1)[-1] if ("?" in path or frag) else path
    q = (f"select count(), count(distinct person_id) from events where event='$pageview' "
         f"and properties.$host='{host}' and timestamp > toDateTime('{after_iso[:19].replace('T', ' ')}') "
         f"and properties.$current_url like '%{needle.replace(chr(39), '')}%' and {{filters}}")
    body = {"query": {"kind": "HogQLQuery", "query": q, "filters": {"filterTestAccounts": True}}}
    req = urllib.request.Request(
        f"{os.environ.get('POSTHOG_HOST', 'https://us.posthog.com').rstrip('/')}/api/projects/{proj}/query/",
        data=json.dumps(body).encode(), headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        res = json.load(urllib.request.urlopen(req, timeout=60)).get("results", [[0, 0]])
        return {"pageviews": res[0][0], "persons": res[0][1]}
    except Exception as e:
        return {"error": str(e)[:120]}


def pull(no_visits=False):
    db = mail_db()
    if not db:
        sys.exit(f"no Mail.app index at {MAIL}")
    latest = latest_outcomes()
    preds = [p for p in read_jsonl(PREDICTIONS) if p.get("email")]
    new = 0
    for p in preds:
        since = p.get("sent_on") or p["made_at"][:10]
        ts = dt.datetime.fromisoformat(since[:10]).replace(tzinfo=dt.timezone.utc).timestamp()
        replies = inbox_replies(db, p["email"], ts)
        cur = latest.get(p["id"], {}).get("outcome")
        if replies and cur in (None, "silent"):
            human = [r for r in replies if not AUTO.search(r[1] or "")]
            kind = "reply_unlabelled" if human else "auto_reply"
            append_jsonl(OUTCOMES, {"prediction_id": p["id"], "observed_at": now(), "outcome": kind,
                                    "source": "mail.app", "evidence": replies[:3]})
            new += 1
            print(f"  {kind:17} {p['email']}  {replies[0][0]}  {replies[0][1]}")
        elif not replies and cur is None:
            append_jsonl(OUTCOMES, {"prediction_id": p["id"], "observed_at": now(), "outcome": "silent",
                                    "source": "mail.app"})
        if not no_visits and p.get("link") and p["source"] == "screen":
            v = posthog_visits(p["link"], p["made_at"])
            if v and "error" not in v:
                append_jsonl(OUTCOMES, {"prediction_id": p["id"], "observed_at": now(), "visits": v,
                                        "source": "posthog"})
    print(f"read {len(preds)} addressed predictions against Mail.app; {new} new replies. "
          "Label human replies with `outcomes.py label`.")


def label(key, outcome, note):
    hits = [p for p in read_jsonl(PREDICTIONS) if p["id"] == key or (p.get("email") or "") == key.lower()]
    if not hits:
        sys.exit(f"no prediction {key}")
    for p in hits:
        append_jsonl(OUTCOMES, {"prediction_id": p["id"], "observed_at": now(), "outcome": outcome,
                                "source": "label", "note": note})
        print(f"{p['id']} -> {outcome}")


# ---------- calibration ----------

def latest_outcomes():
    out = {}
    for o in read_jsonl(OUTCOMES):
        if "outcome" in o:
            out[o["prediction_id"]] = o
    return out


def joined():
    lo = latest_outcomes()
    return [{**p, "outcome": lo.get(p["id"], {}).get("outcome")} for p in read_jsonl(PREDICTIONS)]


def boot_ci(y, s, n=2000):
    random.seed(7)
    idx, vals = list(range(len(y))), []
    for _ in range(n):
        b = [random.choice(idx) for _ in idx]
        a = auc([y[i] for i in b], [s[i] for i in b])
        if a is not None:
            vals.append(a)
    vals.sort()
    return vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]


def report(rows, title):
    rows = [r for r in rows if r["outcome"] is not None]
    if not rows:
        print(f"\n{title}: nothing scored yet")
        return
    y = [r["outcome"] in POSITIVE for r in rows]
    s = [r["p_reply"] for r in rows]
    n, k = len(rows), sum(y)
    brier = sum((a - b) ** 2 for a, b in zip(s, y)) / n
    a = auc(y, s)
    print(f"\n{title}: {n} sends, {k} replies ({k/n:.1%}); mean predicted {sum(s)/n:.1%}; Brier {brier:.4f}")
    if a is not None:
        lo, hi = boot_ci(y, s)
        print(f"  AUC {a:.2f} (95% CI {lo:.2f}-{hi:.2f}) — 0.5 is a coin; needs positives to mean much")
    else:
        print("  AUC: needs at least one reply and one silence")
    order = sorted(range(n), key=lambda i: -s[i])
    print("  bucket            n   predicted  actual")
    for name, lo_q, hi_q in (("top 10%", 0, .1), ("10-25%", .1, .25), ("25-50%", .25, .5), ("bottom 50%", .5, 1)):
        ids = order[int(lo_q * n):max(int(hi_q * n), int(lo_q * n) + 1)]
        if ids:
            print(f"  {name:14} {len(ids):5}   {sum(s[i] for i in ids)/len(ids):7.1%}  {sum(y[i] for i in ids)/len(ids):6.1%}")
    unl = [r for r in rows if r["outcome"] == "reply_unlabelled"]
    if unl:
        print(f"  {len(unl)} human replies await a label: " + ", ".join(r["email"] for r in unl))


def calibration():
    rows = joined()
    report(rows, "ALL")
    report([r for r in rows if r["source"] == "backfill-blind"], "Backfill (blind, scored 10/13)")
    report([r for r in rows if r["source"] == "screen"], "Live (logged before send)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("backfill")
    p = sub.add_parser("pull")
    p.add_argument("--no-visits", action="store_true")
    lb = sub.add_parser("label")
    lb.add_argument("key")
    lb.add_argument("outcome", choices=["positive_reply", "negative_reply", "auto_reply", "silent"])
    lb.add_argument("--note", default="")
    sub.add_parser("calibration")
    a = ap.parse_args()
    if a.cmd == "backfill":
        backfill()
    elif a.cmd == "pull":
        pull(a.no_visits)
    elif a.cmd == "label":
        label(a.key, a.outcome, a.note)
    else:
        calibration()


if __name__ == "__main__":
    main()
