"""Build site/index.html from maps/*.json and the prediction ledger.

    .venv/bin/python lab/build_site.py

Phone first (390 wide), decision first: what we didn't know, then the gaps, then the
segments side by side with every line's verbatim source one tap away. Analytics: Vercel
Web Analytics tag + the shared PostHog block (lab/posthog.html), both written here in the
generator so a rebuild never drops them.

Privacy: replies to our own emails are shown by role only ("Purchasing Manager, a public
water utility"), never by name, and their source is labelled private.
"""
import html
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import MAPS, ROOT  # noqa: E402
from outcomes import joined, POSITIVE  # noqa: E402

ORDER = ["obsolete-parts", "pt-rates", "salon-rates"]


def calibration_rows():
    rows = [r for r in joined() if r["outcome"] is not None]
    rows.sort(key=lambda r: -r["p_reply"])
    n = len(rows)
    out = []
    for name, lo, hi in (("Top 10%", 0, .1), ("Next 15%", .1, .25), ("Next 25%", .25, .5), ("Bottom half", .5, 1)):
        b = rows[int(lo * n):int(hi * n)]
        out.append({"name": name, "n": len(b), "pred": sum(r["p_reply"] for r in b) / len(b),
                    "act": sum(r["outcome"] in POSITIVE for r in b) / len(b),
                    "k": sum(r["outcome"] in POSITIVE for r in b)})
    live = sum(1 for r in joined() if r["source"] == "screen")
    return {"n": n, "k": sum(r["outcome"] in POSITIVE for r in rows), "buckets": out, "live": live}


def public(m):
    """Strip private ledger paths; keep roles."""
    for s in m["segments"]:
        for f in ("jobs", "pains", "workarounds", "wants", "words", "vouchers", "questions"):
            for it in s.get(f, []):
                for c in it.get("cites", []):
                    if c["url"].startswith("private:"):
                        c["url"] = ""
    if m.get("surprise"):
        for c in m["surprise"]["cites"]:
            if c["url"].startswith("private:"):
                c["url"] = ""
    return m


def main():
    maps = [public(json.load((MAPS / f"{p}.json").open())) for p in ORDER if (MAPS / f"{p}.json").exists()]
    data = {"maps": maps, "cal": calibration_rows()}
    ph = (ROOT / "lab/posthog.html").read_text()
    page = TEMPLATE.replace("__POSTHOG__", ph).replace(
        "__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    out = ROOT / "site/index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page)
    (ROOT / "site/vercel.json").write_text(json.dumps({"buildCommand": "echo build", "outputDirectory": "."}))
    print(f"wrote {out.relative_to(ROOT)} ({len(page):,} bytes), {len(maps)} products")


TEMPLATE = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Customer Lab</title>
<meta name="description" content="Who our customers are, how they differ, and what our tools do for them — built only from what they have said in public. Every line cites its source.">
<script>window.va=window.va||function(){(window.vaq=window.vaq||[]).push(arguments)}</script><script defer src="/_vercel/insights/script.js"></script>
__POSTHOG__
<style>
:root{--bg:#f6f4ef;--card:#fff;--ink:#1c1b19;--mute:#6b675f;--line:#e2ddd3;--accent:#1f5f8b;--gap:#b4441f;--ok:#2f7a4a;--quote:#f1ede4}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#151514;--card:#1f1e1c;--ink:#ece8e0;--mute:#a19c92;--line:#34322e;--accent:#79b4dc;--gap:#f08a64;--ok:#7cc79a;--quote:#2a2825}}
:root[data-theme=dark]{--bg:#151514;--card:#1f1e1c;--ink:#ece8e0;--mute:#a19c92;--line:#34322e;--accent:#79b4dc;--gap:#f08a64;--ok:#7cc79a;--quote:#2a2825}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif}
main{max-width:1180px;margin:0 auto;padding:20px 16px 60px}
h1{font-size:26px;margin:0 0 4px;letter-spacing:-.01em}
.sub{color:var(--mute);margin:0 0 18px;font-size:15px}
.tabs{display:flex;gap:8px;overflow-x:auto;padding-bottom:4px;margin:0 0 18px;scrollbar-width:none}
.tabs button{flex:0 0 auto;font:inherit;font-size:15px;padding:10px 14px;min-height:44px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
.tabs button[aria-selected=true]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.lead{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:10px;padding:14px 16px;margin:0 0 14px}
.lead h2,.blk h2{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute);margin:0 0 6px;font-weight:600}
.lead p{margin:0;font-size:18px;line-height:1.4}
.blk{margin:22px 0 0}
.gaps{display:grid;gap:8px;grid-template-columns:1fr}
.gap{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px;font-size:15px}
.gap b{color:var(--gap);font-weight:600}
.gap .seg{color:var(--mute);font-size:13px}
.segs{display:flex;gap:12px;overflow-x:auto;scroll-snap-type:x mandatory;padding:2px 2px 10px;margin:0 -16px;padding-left:16px;padding-right:16px;scroll-padding-left:16px}
.seg-card{flex:0 0 86%;scroll-snap-align:start;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.seg-card h3{margin:0 0 2px;font-size:18px}
.seg-card .who{color:var(--mute);font-size:14px;margin:0 0 10px}
.row{border-top:1px solid var(--line);padding:8px 0}
.row h4{margin:0 0 4px;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute);font-weight:600}
.row ul{margin:0;padding:0;list-style:none}
.row li{margin:0 0 6px;font-size:15px}
.words li{font-style:italic}
.c{font:inherit;font-size:12px;border:1px solid var(--line);background:transparent;color:var(--accent);border-radius:6px;padding:3px 9px;margin-left:4px;cursor:pointer;vertical-align:1px;min-height:30px;min-width:30px}
.q{display:none;background:var(--quote);border-radius:8px;padding:8px 10px;margin:6px 0 2px;font-size:14px}
.q.open{display:block}
.q .src{display:block;color:var(--mute);font-size:12px;margin-top:4px;word-break:break-word}
.q a{color:var(--accent)}
.hyp{color:var(--mute);font-size:12px;border:1px dashed var(--line);border-radius:6px;padding:0 5px;margin-left:4px}
.hint{color:var(--mute);font-size:13px;margin:6px 0 0}
table{border-collapse:collapse;width:100%;font-size:15px;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
td,th{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left}
th{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--mute);font-weight:600}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.facts li{margin:0 0 6px;font-size:15px}
.facts{padding-left:18px;margin:0}
code{font-size:13px;background:var(--quote);padding:2px 5px;border-radius:5px;word-break:break-word}
footer{color:var(--mute);font-size:13px;margin-top:30px;border-top:1px solid var(--line);padding-top:12px}
a{color:var(--accent)}
@media (min-width:900px){
 main{padding:32px 24px 80px}
 h1{font-size:32px}
 .segs{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));overflow:visible;margin:0;padding:0}
 .seg-card{flex:none}
 .gaps{grid-template-columns:1fr 1fr}
}
</style></head>
<body><main>
<h1>Customer Lab</h1>
<p class="sub">Who our customers are and how they differ, built only from what they've said in public. Tap any <span class="c" style="cursor:default">1</span> for the exact words and the source.</p>
<div class="tabs" role="tablist" id="tabs"></div>
<div id="view"></div>
<section class="blk" id="cal"></section>
<footer id="foot"></footer>
</main>
<script id="data" type="application/json">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let qid=0;
function cites(cs){
  if(!cs||!cs.length)return '';
  return cs.map((c,i)=>{const id='q'+(qid++);
    const src=c.url?`<a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.source_kind.replace('_',' '))}${c.date?' · '+esc(c.date):''}</a>`:`${esc(c.source_kind.replace('_',' '))}${c.date?' · '+esc(c.date):''} · private ledger`;
    return `<button class="c" aria-expanded="false" data-q="${id}">${i+1}</button><span class="q" id="${id}">“${esc(c.quote)}”<span class="src">${esc(c.speaker_kind)} — ${src}</span></span>`}).join('');
}
function list(items,cls){
  if(!items||!items.length)return '<p class="hint">Nothing in the evidence.</p>';
  return `<ul class="${cls||''}">`+items.map(it=>`<li>${esc(it.text)}${it.hypothesis?'<span class="hyp">hypothesis</span>':''}${cites(it.cites)}</li>`).join('')+'</ul>';
}
const ROWS=[['jobs','Trying to get done'],['pains','Where it hurts'],['workarounds','What they do today'],['words','Their words','words'],['vouchers','Who they trust'],['wants','What they ask for'],['questions',"They'd ask us"]];
function render(i){
  qid=0;const m=D.maps[i];
  document.querySelectorAll('#tabs button').forEach((b,j)=>b.setAttribute('aria-selected',j===i));
  const gaps=m.job_map.filter(j=>!j.step||j.fit==='none');
  const part=m.job_map.filter(j=>j.step&&j.fit==='partial');
  let h='';
  if(m.surprise)h+=`<div class="lead"><h2>What we didn't know</h2><p>${esc(m.surprise.text)}${cites(m.surprise.cites)}</p></div>`;
  h+=`<p class="hint" style="margin:0 0 4px"><a href="${esc(m.live_url)}" target="_blank" rel="noopener">${esc(m.name)}</a> — ${esc(m.one_liner)}</p>`;
  h+=`<section class="blk"><h2>How they differ · ${m.segments.length} kinds of customer</h2><div class="segs">`+m.segments.map(s=>
    `<article class="seg-card"><h3>${esc(s.name)}</h3><p class="who">${esc(s.who)}</p>`+
    ROWS.filter(([k])=>s[k]&&s[k].length).map(([k,label,cls])=>`<div class="row"><h4>${label}</h4>${list(s[k],cls)}</div>`).join('')+'</article>').join('')+
    `</div><p class="hint">Swipe for the next kind of customer.</p></section>`;
  h+=`<section class="blk"><h2>Jobs our tool doesn't do · ${gaps.length} of ${m.job_map.length}</h2><div class="gaps">`+
    gaps.map(g=>`<div class="gap"><b>Gap</b> · ${esc(g.job)}<div class="seg">${esc(g.segment)} — ${esc(g.why)}</div></div>`).join('')+
    `</div>`+(part.length?`<details class="blk"><summary class="hint" style="cursor:pointer;min-height:44px;display:flex;align-items:center">${part.length} more jobs it does only partly</summary><div class="gaps">`:'')+part.map(g=>`<div class="gap"><b style="color:var(--accent)">Partly</b> · ${esc(g.job)}<div class="seg">${esc(g.segment)} — step ${esc(g.step)}: ${esc(g.why)}</div></div>`).join('')+
    (part.length?`</div></details>`:'')+`</section>`;
  h+=`<section class="blk"><h2>Measured, not modelled</h2><ul class="facts">`+m.facts.map(f=>`<li>${esc(f.text)} <span class="hint">(${esc(f.source)})</span></li>`).join('')+`</ul></section>`;
  document.getElementById('view').innerHTML=h;
  const v=m.verification;
  document.getElementById('foot').innerHTML=`${esc(m.name)}: read ${m.evidence.rows_read} of ${m.evidence.rows_available} evidence rows (${Object.entries(m.evidence.by_source).map(([k,n])=>n+' '+k.replace('_',' ')).join(', ')}). ${v.claims} claims proposed by ${esc(m.model)}; every kept line quotes its source word for word, checked by script — ${v.dropped_claims||0} claims and ${v.bad_cites||0} citations failed and were dropped. Nothing here says whether anyone will use or buy; it says who they are and what they need.`;
  try{localStorage.setItem('cl_tab',i)}catch(e){}
  if(window.va)va('event',{name:'tab',data:{product:m.product}});
}
document.getElementById('tabs').innerHTML=D.maps.map((m,i)=>`<button role="tab" data-i="${i}">${esc(m.name.split(' (')[0])}</button>`).join('');
document.getElementById('tabs').addEventListener('click',e=>{const b=e.target.closest('button');if(b)render(+b.dataset.i)});
document.addEventListener('click',e=>{const b=e.target.closest('button.c[data-q]');if(!b)return;const q=document.getElementById(b.dataset.q);const o=q.classList.toggle('open');b.setAttribute('aria-expanded',o)});
const C=D.cal;
document.getElementById('cal').innerHTML=`<h2>Before any send: the screen</h2>
<p style="margin:0 0 10px">Persona role-play could not tell who would reply (AUC ≈ 0.5). An outside-view forecaster could. Here it is on our ${C.n} real sends, ranked by its prediction:</p>
<table><tr><th>Forecast rank</th><th class="n">Sends</th><th class="n">Predicted</th><th class="n">Replied</th></tr>`+
C.buckets.map(b=>`<tr><td>${b.name}</td><td class="n">${b.n}</td><td class="n">${(b.pred*100).toFixed(1)}%</td><td class="n">${b.k} (${(b.act*100).toFixed(1)}%)</td></tr>`).join('')+
`</table><p class="hint">${C.k} replies so far, so this ranks drafts; it does not decide what to build. Every new draft is scored and logged before it goes (${C.live} so far), and scored again when the inbox answers.</p>`;
let start=0;try{start=+(localStorage.getItem('cl_tab')||0)}catch(e){}
render(Math.min(start,D.maps.length-1));
</script>
</body></html>
"""

if __name__ == "__main__":
    main()
