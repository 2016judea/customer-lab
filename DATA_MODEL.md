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

## Reality check (2026-10-13, after the first pull)

Field by field, for the three products in the first slice. **Filled** = a source exists and
the build fills it. **Partial** = fillable for some products or some rows. **Can't** = no
source we can reach today.

| entity.field | status | why |
|---|---|---|
| Product, ToolStep | filled | read off each live tool, step cites its URL |
| Segment.name / who | filled | proposed by the model from evidence, each claim quote-checked |
| Segment.how_many | **can't (yet)** | needs a register per segment (SDWIS for water systems, NPPES for PT clinics, licence lists for salons). Not pulled; a model may not guess it. The page shows only our own counts (menus read, sends made). |
| Job / Pain / Workaround / Want / words | filled | Reddit, own menus, filings, replies to us; every kept line quotes its source verbatim |
| Segment.vouchers (Channel) | **partial, thin** | people rarely say in public who they trust; most segments carry 0-1 evidenced voucher |
| Segment.questions | partial | mostly hypothesis — only a few are in the evidence |
| Evidence.verified | filled | substring check in `segment_map.py`; failures dropped and counted |
| Evidence.speaker_kind | partial | Reddit speakers are often employees (PT clinicians, salon renters), not the owner who decides; labelled per row, never assumed |
| Person.public_record | partial | exists as `recipient_context` in the send ledgers; not yet joined into Person rows |
| Draft | partial | the screen hashes the body; drafts stay in each product's outreach folder |
| Prediction | filled | 417 backfilled (scored blind, *after* the send) + every new screen, logged before send |
| Outcome.replied | filled for email | Mail.app's local index of the Zoho inbox, exact sender address. LinkedIn/InMail replies **can't** be read. |
| Outcome.delivered | **can't** | Mailgun's event log expires; only Zoho hard failures are visible |
| Outcome.opened | **can't** | no open tracking, by design |
| Outcome.visited | partial | PostHog per-recipient link, only for sends after 2026-10-12 (when PostHog went on) |

The fields that fail (how_many, delivered, opened, most vouchers) do not change the thesis:
the map still answers *who, how they differ, what they need, what our tool does*. how_many is
the one to fill next, from registers, never from a model.

## Next steps (added 2026-10-13, `lab/next.py`)

Aidan, 10/13: *"What im looking for is new iterations of a given product. And different
distributions and rules surrounding sales and marketing."* Written from that need:

| entity | fields | question it answers |
|---|---|---|
| Iteration | change, the_step, serves[] → Job/Gap claim (quote+url), ideal_fields[] {field, answers, source, locator, status, checked}, reality | what do we build next, which cited job does it close, can reality fill it |
| Play | channel, voucher, who_vouches, vouch_evidence[] → claim, segments[] (floor 3), recipient_source, offer_mode, past_runs[] → channel ledger row, past_sends{} (counted), draft, screen → Prediction | where does a stranger read us, who vouches, what happened the last times we ran it |
| SalesRule | rule, why, source | what we must always / never do selling this product |

Reality check: claims and gaps come from the verified map; channel runs from the
distribution-channel ledger table (parsed, not retyped); send counts from
`panel-backtest/dataset.jsonl` + live screens. What reality can't fill: whether a field the
model names actually holds the data — only that its path exists or URL answers is checked.
