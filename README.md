# Customer Lab

```bash
.venv/bin/python lab/next.py <product>                    # next iterations, distribution plays, sales rules
.venv/bin/python lab/next.py --new "<one-line idea>"      # idea -> cited customers -> the same, one command
```

**View:** private Claude artifact — https://claude.ai/artifact/DiNgsHUyo7XYtEwjFiRcyY (internal; never deploy this publicly)

Who our customers are, how they differ, what they're trying to get done, and which of those
jobs our tools actually do — built only from what those people have said in public. Then a
screen that scores a draft email before it goes out, and keeps score afterwards.

A better version of synthetic-customer tools (MiroFish, synthetic focus groups), built after
a blind backtest showed persona role-play could not tell who would reply to 419 real emails
(AUC ≈ 0.5), while an outside-view forecaster with no role-play could (AUC 0.86).
See `~/Desktop/panel-backtest/RESULTS.md`.

## The rules it runs on

1. **Customers come from evidence, not invention.** Every job, pain, workaround, phrase and
   voucher quotes a real source (Reddit, a business's own menu, an agency's own filing, a
   reply to us). `lab/segment_map.py` checks each quote is a word-for-word substring of its
   source and drops it if not.
2. **No verdicts on use.** Nothing here says whether anyone will use, buy or reply as a reason
   to build or skip (`~/.claude/BUSINESS.md` rule 2).
3. **Segments are shown by how they differ**, side by side, never averaged.
4. **Useful = a job mapped to a step the tool does.** Unmapped jobs are listed as gaps.
5. **The pre-send screen uses only the validated method**, logs before send, and is scored
   after. Role-play only generates questions, labelled hypothesis.
6. **A model is never the source of a number.** Counts come from the ledgers and databases.

## Next steps — `lab/next.py`

The lab's output is not a map to review; it is what to build and how to sell it next.
From `maps/<product>.json`, every send we have made (`panel-backtest/dataset.jsonl` + the
ledger), the measured channel ledger in the `distribution-channel` skill and `~/.claude/BUSINESS.md`,
it writes `maps/<product>.next.json` and `maps/<product>.NEXT.md`:

- **Iterations** (2–4, ranked): a product change that does a step of the customer's work
  (rule 3), the cited job or gap it closes (quote + URL copied from the map, never from the model),
  and the ideal fields it needs, each checked (path exists / URL answers) with a plain call when
  reality can't fill it (rule 5).
- **Distribution plays** (2–4, ranked by voucher): who already vouches for us to this segment, with
  the map evidence; the 50-recipient / 3-segment floor (rule 4); and the past runs and send counts
  for the closest channels, counted from the ledgers.
- **Rules**: sales and marketing rules for this product, each with its why and source.
- **One first-touch draft per play**, scored by the screen (forecaster-v1) and logged to
  `ledger/predictions.jsonl` as `next-draft` (no recipient yet; re-screen once one is named).

Any sentence forecasting whether people will use, buy or reply is cut and listed under
`grounding.verdicts_cut` (rule 2). `--reuse` re-grounds the last model reply for $0.
`--new` asks a model where the idea's customers talk, pulls those subreddits (reddit-mining) and
trade pages, builds evidence and a verified map, and stops if fewer than 15 evidence rows come back.

## Run it

```bash
uv venv .venv && VIRTUAL_ENV=.venv uv pip install anthropic   # key: ANTHROPIC_API_KEY in ~/Desktop/bricks/.env

# customer maps
.venv/bin/python lab/evidence.py obsolete-parts        # -> data/evidence/<product>.jsonl
.venv/bin/python lab/segment_map.py obsolete-parts     # -> maps/<product>.json (≈$0.2)
.venv/bin/python lab/build_site.py && python3 scripts/deploy.py

# before a send: score the draft, logged to ledger/predictions.jsonl
.venv/bin/python lab/screen.py --product salon-rates --email x@y.com --kind "independent hairstylist" \
  --org "Shop" --context "their public record" --subject "..." --body-file draft.txt --link <their page>

# after: read replies (Mail.app's copy of Zoho) + visits (PostHog), then calibration
.venv/bin/python lab/outcomes.py pull
.venv/bin/python lab/outcomes.py label <email|id> positive_reply
.venv/bin/python lab/outcomes.py calibration
```

Reddit pulls use the `reddit-mining` skill's script into `data/raw/reddit/<product>_<sub>.json`
(gitignored; every quote keeps its permalink).

`DATA_MODEL.md` is the ideal model, written before the data, with the field-by-field reality check.

MIT licence.
