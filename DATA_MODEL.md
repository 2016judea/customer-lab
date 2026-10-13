# Data model — the ideal customer lab

Written 2026-10-13 from the need alone, before checking what data exists
(`~/.claude/BUSINESS.md` rule 5). The need, in Aidan's words: *"who they are, how they
differ from one another, what they want, what is truly useful to them"* — learned and
tested before any further distribution.

Two rules shape every entity:

- **Nothing about a customer is invented.** Every claim hangs off an `Evidence` row with
  a URL and a verbatim quote. A claim with no evidence does not exist in this model.
- **No entity holds a verdict on whether they will use, buy or reply.** `Prediction`
  is a screen on a *message*, logged before send and scored after. It never decides
  whether to build.

## Entities

### Product
The tool we built.
| field | question it answers |
|---|---|
| id, name, live_url | which tool, where can I poke it |
| one_liner | what Aidan says it is |
| steps[] → ToolStep | what work it actually does for someone |

### ToolStep
One step of someone's work the tool performs (BUSINESS.md rule 3: build the step).
| field | question |
|---|---|
| id, product_id | |
| verb_object | "compares your payer rates to the market median" |
| evidence_url | where on the live tool this step is visible |

### Segment
A kind of buyer, defined by how it **differs** from the others.
| field | question |
|---|---|
| id, product_id, name | |
| who | role, org type, size — who is this |
| how_many | how many exist in our market (from a register, never from a model) |
| jobs[] → Job | what they are trying to get done |
| pains[] → Pain | what goes wrong now |
| workarounds[] → Workaround | what they do instead of our tool today |
| wants[] → Want | what they ask for in their own words |
| words[] | verbatim phrases they use (so copy uses their words, not ours) |
| vouchers[] → Channel | who they already trust; who stands between us and them |
| questions[] | what they'd ask a stranger before trusting this (hypothesis unless evidenced) |

### Job / Pain / Workaround / Want
Each is `{id, segment_id, text, evidence_ids[]}`. `evidence_ids` must be non-empty.
| entity | question |
|---|---|
| Job | what are they hired to get done, that our tool could touch |
| Pain | where it hurts today, in their words |
| Workaround | what they use now (a spreadsheet, a broker, a phone call) — the real competitor |
| Want | what they explicitly ask for |

### JobStep (the usefulness map)
| field | question |
|---|---|
| job_id, step_id or null | does our tool do this job's step? null = **gap** |
| fit | full / partial / none |
| why | one line, citing the job's evidence and the step's URL |

### Evidence
| field | question |
|---|---|
| id, url, quote (verbatim), date | what was said, where, when |
| source_kind | reddit / review / forum / minutes / filing / job_post / own_site / our_reply |
| speaker_kind | which kind of person said it (maps to a segment) |
| verified | is `quote` a literal substring of the fetched source text |

### Person / Org
A real reachable recipient. `{id, name, org, role, segment_id, public_record[]}` where
`public_record` is Evidence about *them* (their post, filing, minutes, permit) — the
distribution-channel skill found every positive reply opened on it.

### Channel (who vouches)
`{id, segment_id, kind: obligation|person|physical|platform, name, evidence_ids[]}` —
the association, circuit rider, vendor or forum this segment already trusts.

### Draft
`{id, product_id, person_id, subject, body, opens_on_evidence_id}` — a message, never sent
from here.

### Prediction (append-only ledger, written BEFORE send)
`{id, draft_id|send_id, made_at, method, model, p_reply, p_click, inputs_hash}`.
Only the validated method (outside-view forecaster, AUC 0.86 on 419 sends,
`~/Desktop/panel-backtest/RESULTS.md`) may write `p_reply`. Role-play may only add
`questions[]`, labelled hypothesis.

### Outcome
`{prediction_id, observed_at, delivered, opened|visited, replied: positive|negative|auto|silent,
source: inbox|posthog|ledger, evidence}` — scored against Prediction for calibration.

## Joins

Product 1—n ToolStep · Product 1—n Segment · Segment 1—n Job/Pain/Workaround/Want/Channel ·
every claim n—n Evidence · Job n—1 ToolStep via JobStep (null = gap) ·
Segment 1—n Person · Person 1—n Draft · Draft 1—1 Prediction · Prediction 1—n Outcome.

## Reality check

See the section appended below after the first data pull — written after this model, so
the model is the fixed point it is measured against.
