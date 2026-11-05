"""Shared paths, keys and the Claude client. Keys come from ~/Desktop/workspace/bricks/.env (the keyring)."""
import json
import os
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER = ROOT / "ledger"
PREDICTIONS = LEDGER / "predictions.jsonl"
OUTCOMES = LEDGER / "outcomes.jsonl"
EVIDENCE = ROOT / "data" / "evidence"
MAPS = ROOT / "maps"
SPEND = LEDGER / "model_spend.jsonl"

ENV = pathlib.Path.home() / "Desktop/workspace/bricks/.env"

SONNET = "claude-sonnet-5-5"
HAIKU = "claude-haiku-5-5"
# $ per million tokens (input, output) — used only to log spend, never shown as a finding.
PRICE = {SONNET: (3.0, 15.0), HAIKU: (1.0, 5.0)}


def load_env():
    if ENV.exists():
        for line in ENV.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_client = None


def claude(model, system, user, max_tokens=1000, tag=""):
    """One Messages call; logs tokens and dollars to ledger/model_spend.jsonl."""
    global _client
    if _client is None:
        load_env()
        import anthropic
        _client = anthropic.Anthropic()
    r = _client.messages.create(model=model, max_tokens=max_tokens, system=system,
                                messages=[{"role": "user", "content": user}])
    pi, po = PRICE.get(model, (3.0, 15.0))
    cost = (r.usage.input_tokens * pi + r.usage.output_tokens * po) / 1e6
    with open(SPEND, "a") as f:
        f.write(json.dumps({"tag": tag, "model": model, "in": r.usage.input_tokens,
                            "out": r.usage.output_tokens, "usd": round(cost, 5)}) + "\n")
    return "".join(b.text for b in r.content if b.type == "text").strip()


def read_jsonl(p):
    p = pathlib.Path(p)
    return [json.loads(l) for l in p.open() if l.strip()] if p.exists() else []


def append_jsonl(p, row):
    with open(p, "a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def norm(s):
    """Whitespace/quote-insensitive form for verbatim checks."""
    s = (s or "").lower().replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"').replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", s).strip()


def first_json(text):
    m = re.search(r"[\{\[].*[\}\]]", text, re.S)
    return json.loads(m.group(0))


def auc(y, s):
    pos = [b for a, b in zip(y, s) if a]
    neg = [b for a, b in zip(y, s) if not a]
    if not pos or not neg:
        return None
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))
