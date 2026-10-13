"""Collect EVIDENCE for a product: verbatim text, a URL, a date, who said it.

    .venv/bin/python lab/evidence.py salon-rates|pt-rates|obsolete-parts

Writes data/evidence/<product>.jsonl. Each row is a unit of real public exhaust (a Reddit
post or comment, a paragraph of a web page, a line of a business's own menu, an agency's own
filing, a reply to us). Segment claims later must quote one of these rows verbatim — that
is the whole point of the lab: customers are built from evidence, never invented.

Sources and why each is trusted:
  reddit   Arctic Shift archive via the reddit-mining skill (data/raw/reddit/<p>.json)
  web      a page fetched with curl into data/raw/web/ (list in WEB below)
  own_site the stylist's own service descriptions (salon-rates DB, scraped from their menus)
  filing   an agency's own sole-source/obsolescence filing, reason checked against the PDF text
  our_reply a human reply to one of our emails (parts repo outreach/README.md, verbatim)
"""
import gzip
import hashlib
import html
import json
import pathlib
import random
import re
import sqlite3
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import EVIDENCE, ROOT, norm  # noqa: E402

HOME = pathlib.Path.home()
RAW = ROOT / "data" / "raw"
PARTS = HOME / "Desktop/the-google-of-obsolete-infrastructure-parts"
SALON_DB = HOME / "Desktop/salon-rates/pipeline/salon.db"

REDDIT = {"salon-rates": "salon", "pt-rates": "pt", "obsolete-parts": "water"}
WEB = {
    "pt-rates": {
        "https://www.webpt.com/blog/tales-from-the-table-how-pts-have-successfully-negotiated-payer-contracts": "PT clinic owners quoted by WebPT",
        "https://www.stratapt.com/article/how-to-renegotiate-payer-contracts-for-rehab-therapy-clinics-ft-justin-stiver": "rehab clinic payer-contracting consultant",
        "https://getbreakthrough.com/negotiating-physical-therapy-reimbursement-rates/": "PT practice owner case study (Breakthrough)",
    },
    "obsolete-parts": {
        "https://www.mroelectric.com/about-us": "industrial surplus / legacy parts dealer (own site)",
        "https://www.wiautomation.com/": "industrial automation spares dealer (own site)",
        "https://www.ruralwater.org/": "National Rural Water Association (circuit riders' body)",
    },
}
KEYWORDS = {
    "salon-rates": r"price|pric|charg|raise|increase|undercharg|worth|competit|deposit|consult|client",
    "pt-rates": r"rate|reimburs|payer|contract|negotiat|fee schedule|cash|insur|network|bcbs|underpa",
    "obsolete-parts": r"obsolete|discontinu|legacy|end of life|surplus|spare|ebay|sole source|lead time|"
                      r"hard.to.find|replacement|no longer|unsupported|repair|circuit rider",
}
SPEAKER = {
    "hairstylist": "stylist", "Hairdresser": "stylist", "salonowners": "salon owner", "Esthetics": "esthetician",
    "physicaltherapy": "physical therapist", "PrivatePractice": "private-practice clinician",
    "WaterTreatment": "water/wastewater operator", "Wastewater": "water/wastewater operator",
    "PLC": "controls/automation tech", "SCADA": "controls/automation tech", "PublicWorks": "public works staff",
}


def eid(*parts):
    return "e_" + hashlib.sha1("|".join(parts).encode()).hexdigest()[:10]


def row(text, url, date, kind, speaker, extra=None):
    text = " ".join((text or "").split())
    return {"id": eid(url, text[:200]), "url": url, "date": date, "source_kind": kind,
            "speaker_kind": speaker, "text": text, **(extra or {})}


def from_reddit(product, rx):
    posts = []
    for p in sorted((RAW / "reddit").glob(f"{REDDIT[product]}_*.json")):
        if p.stat().st_size == 0:
            print(f"  empty reddit pull {p.name}")
            continue
        data = json.load(p.open())
        posts += data if isinstance(data, list) else data.get("posts") or data.get("results") or []
    out = []
    for post in posts:
        sp = SPEAKER.get(post.get("subreddit"), "reddit user")
        url, date = post["permalink"], (post.get("created") or "")[:10]
        body = f"{post.get('title') or ''}. {post.get('selftext') or ''}"
        if re.search(rx, body, re.I):
            out.append(row(body[:2500], url, date, "reddit", sp, {"sub": post.get("subreddit")}))
        for c in post.get("comments") or []:
            if len(c.get("body") or "") > 60 and re.search(rx, c["body"], re.I):
                out.append(row(c["body"], url, date, "reddit_comment", sp, {"sub": post.get("subreddit")}))
    return out


def html_text(raw):
    raw = re.sub(r"(?is)<(script|style|noscript|svg).*?</\1>", " ", raw)
    raw = re.sub(r"(?i)</(p|div|li|h\d|br|section|blockquote)>|<br\s*/?>", "\n", raw)
    return html.unescape(re.sub(r"<[^>]+>", " ", raw))


def from_web(product, rx):
    out = []
    for url, speaker in WEB.get(product, {}).items():
        f = RAW / "web" / (hashlib.md5((url + "\n").encode()).hexdigest()[:10] + ".html")
        if not f.exists() or f.stat().st_size < 2000:
            print(f"  skip {url} (not fetched)")
            continue
        raw = f.read_text(errors="ignore")
        if re.search(r"<title>[^<]*(not found|404)", raw, re.I):
            print(f"  skip {url} (404 page)")
            continue
        for para in html_text(raw).split("\n"):
            para = " ".join(para.split())
            if 80 < len(para) < 1500 and re.search(rx, para, re.I):
                out.append(row(para, url, "2026-10-13", "web", speaker))
    return out


def from_salon_db():
    db = sqlite3.connect(f"file:{SALON_DB}?mode=ro", uri=True)
    q = """select b.business_type, b.is_suite, b.url, b.name, l.name_raw, l.description
           from service_listing l join business b using(business_id)
           where l.description is not null and length(l.description) between 60 and 900
             and (l.description like '%price%' or l.description like '%deposit%' or l.description like '%consult%'
                  or l.description like '%starting%' or l.description like '%charge%' or l.description like '%vary%')"""
    rows = db.execute(q).fetchall()
    random.seed(13)
    by = {}
    for r in rows:
        by.setdefault(r[0], []).append(r)
    out = []
    for bt, rs in by.items():
        seen = set()
        for r in random.sample(rs, len(rs)):
            if r[2] in seen:  # one line per shop, so no single shop dominates
                continue
            seen.add(r[2])
            spk = f"{'suite ' if r[1] else ''}{bt} (own menu)"
            out.append(row(f"{r[4]}: {r[5]}", r[2], "2026-10-05", "own_site", spk, {"shop": r[3]}))
            if len(seen) >= 18:
                break
    return out


_PDF_INDEX = None


def pdf_text(url):
    """Text of the agency's own PDF, from the parts repo's cache (keyed by a .url sidecar)."""
    global _PDF_INDEX
    cache = PARTS / "data/cache/pdf"
    if _PDF_INDEX is None:
        _PDF_INDEX = {f.read_text().strip(): f.with_suffix("") for f in cache.glob("*.url")}
    stem = _PDF_INDEX.get(url)
    if not stem:
        return ""
    if stem.with_suffix(".txt").exists():
        return stem.with_suffix(".txt").read_text(errors="ignore")
    try:
        return subprocess.run(["pdftotext", "-layout", str(stem.with_suffix(".pdf")), "-"],
                              capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return ""


def from_filings():
    keep = {"SCADA/controls/software", "instrumentation/calibration", "electrical/switchgear/transformer",
            "motor/drive", "valve", "pipe/fitting", "treatment process (membrane/centrifuge/UV/chemical feed)",
            "other equipment", "communications/radio"}
    recs = [json.loads(l) for l in (PARTS / "data/records.jsonl").open()]
    recs = [r for r in recs if r.get("is_obsolete") and r.get("equipment_class") in keep and r.get("reason")]
    random.seed(5)
    random.shuffle(recs)
    verified, titled = [], []
    for r in recs:
        if len(verified) >= 30:
            break
        txt = pdf_text(r.get("source_url") or "")
        ok = bool(txt) and norm(r["reason"]) in norm(txt)
        (verified if ok else titled).append((r, ok))
    out = []
    for r, ok in verified + titled[: max(0, 45 - len(verified))]:
        quote = r["reason"] if ok else r["title"]
        out.append(row(f"{r['agency']} ({r['state']}), {r['equipment_class']}: {quote}",
                       r.get("legistar_url") or r.get("source_url"), r.get("date") or "", "filing",
                       "public agency (own filing)",
                       {"quote_verified_against": "pdf text" if ok else "agenda title (API)"}))
    return out


def from_our_replies():
    md = (PARTS / "outreach/README.md").read_text()
    out, roles = [], {}
    for line in md.splitlines():
        m = re.match(r"\| (\d+/\d+) \| \*\*([^*]+)\*\*, ([^|]+?) \| \"(.+?)\"", line)
        if m:
            date, _name, who, said = m.groups()
            last = _name.split()[-1]
            role = roles.setdefault(last, who.split(",")[0].strip())  # follow-ups reuse the first role
            out.append(row(said, "private: the-google-of-obsolete-infrastructure-parts/outreach/README.md",
                           "2026-" + date.replace("/", "-").zfill(5), "our_reply",
                           f"{role}, a public water utility (reply to us)"))
    for neg in ("not interested",):
        out.append(row(f"Radwell InMail reply to the $500 buyer-report offer: \"{neg}\"",
                       "private: panel-backtest/dataset.jsonl (parts dealers)", "2026-10-05", "our_reply",
                       "industrial surplus dealer (reply to us)"))
    return out


def main():
    product = sys.argv[1]
    rx = KEYWORDS[product]
    rows = from_reddit(product, rx) + from_web(product, rx)
    if product == "salon-rates":
        rows += from_salon_db()
    if product == "obsolete-parts":
        rows += from_filings() + from_our_replies()
    uniq = {r["id"]: r for r in rows}
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    out = EVIDENCE / f"{product}.jsonl"
    with out.open("w") as f:
        for r in uniq.values():
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    print(f"{product}: {len(uniq)} evidence rows -> {out.relative_to(ROOT)}  {dict(Counter(r['source_kind'] for r in uniq.values()))}")


if __name__ == "__main__":
    main()
