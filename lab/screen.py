"""Pre-send screen: score ONE draft for ONE named recipient, and log the prediction BEFORE send.

    .venv/bin/python lab/screen.py --product salon-rates --email bobbie@example.com \
        --kind "independent hairstylist" --org "BK Hair Co" \
        --context "GlossGenius menu lists Haircut at \$30; nearby middle \$65" \
        --subject 'Your "Haircut" at $30, and $65 nearby' --body-file draft.txt \
        [--link https://salon-rates.vercel.app/#glossgenius:bkhairco]

Method: the outside-view forecaster, prompt copied verbatim from
~/Desktop/panel-backtest/individual.py (AUC 0.86 on 419 real sends, 5 positives —
~/Desktop/panel-backtest/RESULTS.md). Changing the prompt makes it an unvalidated method,
so the method name carries a version and the prompt is pinned here.

This is a screen on a MESSAGE, never a verdict on whether to build (~/.claude/BUSINESS.md
rule 2). It sends nothing.
"""
import argparse
import datetime as dt
import hashlib
import json
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from common import PREDICTIONS, SONNET, append_jsonl, claude, first_json, read_jsonl  # noqa: E402

METHOD = "forecaster-v1"


def email_text(subject, body):
    return f"From: Aidan Jude <aidan@brickandmortar.dev>\nSubject: {subject}\n\n{body}"


def forecast(kind, org, context, subject, body, model=SONNET):
    fc = claude(
        model,
        "You are a calibrated forecaster of cold-outreach outcomes. Base rates matter.",
        "A stranger sent this cold email.\nRecipient: " + json.dumps(
            {"recipient_kind": kind, "recipient_org": org, "recipient_context": context}) +
        "\n\n---\n" + email_text(subject, body) +
        "\n---\nGive P(recipient replies within a week) and P(recipient clicks the link) as "
        'JSON: {"p_reply": 0-1, "p_click": 0-1}. JSON only.', max_tokens=60, tag="screen")
    j = first_json(fc)
    return float(j["p_reply"]), float(j["p_click"])


def base_rate():
    """Mean predicted vs actual on everything already scored — context for one number."""
    from outcomes import joined  # noqa
    rows = [r for r in joined() if r["outcome"] is not None]
    if not rows:
        return None
    pos = sum(r["outcome"] == "positive_reply" for r in rows)
    return len(rows), pos, sum(r["p_reply"] for r in rows) / len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--product", required=True)
    ap.add_argument("--email", required=True, help="recipient address (the join key for outcomes)")
    ap.add_argument("--name", default="")
    ap.add_argument("--kind", required=True, help="e.g. 'independent hairstylist'")
    ap.add_argument("--org", required=True)
    ap.add_argument("--context", default="", help="what is known about them; their public record")
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--link", default="", help="their personal link; outcomes counts visits to it")
    ap.add_argument("--channel", default="email")
    ap.add_argument("--dry", action="store_true", help="score but do not log")
    a = ap.parse_args()

    body = open(a.body_file).read().strip()
    p_reply, p_click = forecast(a.kind, a.org, a.context, a.subject, body)
    pid = "p_" + hashlib.sha1(f"{a.email}|{a.subject}|{body}".encode()).hexdigest()[:12]
    row = {
        "id": pid, "made_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "source": "screen", "method": METHOD, "model": SONNET, "product": a.product,
        "email": a.email.lower(), "name": a.name, "kind": a.kind, "org": a.org,
        "context": a.context, "subject": a.subject,
        "body_sha": hashlib.sha1(body.encode()).hexdigest()[:12], "link": a.link,
        "channel": a.channel, "p_reply": p_reply, "p_click": p_click,
    }
    if not a.dry:
        if any(r["id"] == pid for r in read_jsonl(PREDICTIONS)):
            print(f"already logged {pid} (same recipient, subject and body)")
        else:
            append_jsonl(PREDICTIONS, row)
    br = base_rate()
    print(f"{pid}  P(reply)={p_reply:.0%}  P(click)={p_click:.0%}  [{METHOD}]")
    if br:
        n, pos, mean = br
        print(f"context: {n} scored sends so far, {pos} positive ({pos/n:.1%}); "
              f"mean predicted {mean:.1%}. Rank drafts against each other, not against 50%.")
    print("logged before send" if not a.dry else "dry run, not logged")


if __name__ == "__main__":
    main()
