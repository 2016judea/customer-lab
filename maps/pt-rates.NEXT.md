# Next: PT Rates

_2026-10-13 · `lab/next.py` · from `maps/pt-rates.json`. Nothing here says whether anyone will use or buy it (BUSINESS.md rule 2)._

## Iterations

### 1. Build a negotiation brief generator: from a clinic's own rate per code (P1) and the market median and middle half (P2/P3), it drafts the payer ask, ordered by the codes the clinic bills most, with the clinic's floor shown beside each rate.

**The step it does:** Work out which codes to approach the payer about and write the case for "a higher per-visit rate", so the owner arrives with "the data to support your argument" instead of assembling it by hand.

- serves G2 (Independent PT practice owners, gap): Win a higher per-visit rate from a payer in negotiation. — "This totaled a 30% increase over 3 years and raised their per-visit reimbursement with that payer from $62 to $83." (https://getbreakthrough.com/negotiating-physical-therapy-reimbursement-rates/)
- serves G3 (Payer-contract advisors, gap): Renegotiate payer contracts on a clinic's behalf. — "In this episode of Strata Stories, Justin Stiver shares a blueprint for how to renegotiate payer contracts" (https://www.stratapt.com/article/how-to-renegotiate-payer-contracts-for-rehab-therapy-clinics-ft-justin-stiver)
- serves C2 (Independent PT practice owners, jobs): Win a higher per-visit rate from a payer in negotiation. — "This totaled a 30% increase over 3 years and raised their per-visit reimbursement with that payer from $62 to $83." (https://getbreakthrough.com/negotiating-physical-therapy-reimbursement-rates/)
- serves C3 (Independent PT practice owners, pains): Low-ball rates on the codes they bill most often. — "identify—and approach payers about—low-ball reimbursement rates for “[CPT] codes that you use frequently.”" (https://www.webpt.com/blog/tales-from-the-table-how-pts-have-successfully-negotiated-payer-contracts)
- serves C7 (Independent PT practice owners, workarounds): Offer to share what similar companies pay them as a negotiation tool. — "I offered to share the reimbursement rates that other similar companies paid us as a negotiation tool" (https://www.webpt.com/blog/tales-from-the-table-how-pts-have-successfully-negotiated-payer-contracts)
- serves C10 (Independent PT practice owners, wants): Objective data to support their argument at the table. — "you better have the data to support your argument." (https://www.webpt.com/blog/tales-from-the-table-how-pts-have-successfully-negotiated-payer-contracts)
- serves C18 (Payer-contract advisors, wants): A per-visit floor below which the clinic loses money. — "If we can’t get $81 per visit, then we’re losing money and we’re not gonna do that." (https://www.stratapt.com/article/how-to-renegotiate-payer-contracts-for-rehab-therapy-clinics-ft-justin-stiver)

| field | answers | source | status | checked |
|---|---|---|---|---|
| paid rate per code per payer for this clinic (BCBS MN, HealthPartners, UCare) | What does each payer pay me on each code? | P1 clinic-by-payer rates already in the tool | exists | url answered 200 |
| market median and middle half of clinics per code | Where does my rate sit against the market on this code? | P2/P3 Twin Cities median and spread | exists | url answered 200 |
| clinic's billed volume per code | Which are the codes I bill most often, so the ask starts where the low-ball rates cost most? (C3) | clinic-supplied remittance or billing export | missing | not checked (no locator given) |
| clinic's per-visit floor | Below what per-visit rate do I lose money? (C18) | clinic input | missing | not checked (no locator given) |
| payer contract contact and route | Who at the payer do I reach? (C4) | payer provider-relations contacts | missing | not checked (no locator given) |

**Reality:** Reality fills the rate side only; volume and floor must be supplied by the clinic (reframe to a clinic-upload tool) and the payer contact field cannot be filled from any source we hold, so it stays named as missing rather than shrinking the model.

### 2. Build a contract-burden ranker: the clinic uploads its remittances, the tool computes revenue per visit and payer mix per payer, compares each payer's code rates to market, and returns a ranked list of which contracts to focus on with the reasoning written out.

**The step it does:** Decide "which insurance contract[s] you need to focus on and which ones are the biggest financial burdens", using the owner's own words payer mix and revenue per visit.

- serves G1 (Independent PT practice owners, gap): Work out which payer contracts are the biggest financial burden. — "These calculations will help you determine which insurance contract[s] you need to focus on and which ones are the biggest financial burdens." (https://www.webpt.com/blog/tales-from-the-table-how-pts-have-successfully-negotiated-payer-contracts)
- serves C1 (Independent PT practice owners, jobs): Work out which payer contracts are the biggest financial burden. — "These calculations will help you determine which insurance contract[s] you need to focus on and which ones are the biggest financial burdens." (https://www.webpt.com/blog/tales-from-the-table-how-pts-have-successfully-negotiated-payer-contracts)
- serves C11 (Independent PT practice owners, words): payer mix — "So they took a closer look at their payer mix and average cost per visit." (https://getbreakthrough.com/negotiating-physical-therapy-reimbursement-rates/)
- serves C12 (Independent PT practice owners, words): revenue per visit — "calculate your revenue per visit by determining the total dollars you received for your work over the previous 12 months" (https://www.webpt.com/blog/tales-from-the-table-how-pts-have-successfully-negotiated-payer-contracts)

| field | answers | source | status | checked |
|---|---|---|---|---|
| revenue per visit by payer over the previous 12 months | What do I actually take in per visit from each payer? (C12) | clinic-supplied remittance export | missing | not checked (no locator given) |
| payer mix share of visits | How much of my work does each payer account for? (C11) | clinic-supplied billing export | missing | not checked (no locator given) |
| per-code gap to market median for each payer | Is this contract below the market on the codes I use? | P1 joined to P2/P3 | partial | url answered 200 |
| cost per visit | Does this contract pay above or below what a visit costs me? | clinic input | missing | not checked (no locator given) |

**Reality:** Public data cannot fill revenue per visit, payer mix or cost per visit, so the ideal tool exists only if reframed as a clinic-upload tool; the gap-to-market field alone is the pigeon-holed subset and is not to be shipped as the finished product.

### 3. Build an advisor client-pack drafter: an advisor adds client clinics and the tool writes each clinic's per-code rate-versus-market brief in the advisor's billing-service format.

**The step it does:** Produce the "payer contract insights" a billing service hands each clinic, and the benchmark behind a renegotiation, without the advisor assembling it clinic by clinic.

- serves G3 (Payer-contract advisors, gap): Renegotiate payer contracts on a clinic's behalf. — "In this episode of Strata Stories, Justin Stiver shares a blueprint for how to renegotiate payer contracts" (https://www.stratapt.com/article/how-to-renegotiate-payer-contracts-for-rehab-therapy-clinics-ft-justin-stiver)
- serves G4 (Payer-contract advisors, gap): Offer clinics payer contract insights as part of a billing service. — "StrataPT provides EMR software, billing services, denial management, credentialing support, payer contract insights, AI-assisted documentation, reporting, and ongoing revenue optimization." (https://www.stratapt.com/article/how-to-renegotiate-payer-contracts-for-rehab-therapy-clinics-ft-justin-stiver)
- serves C14 (Payer-contract advisors, jobs): Renegotiate payer contracts on a clinic's behalf. — "In this episode of Strata Stories, Justin Stiver shares a blueprint for how to renegotiate payer contracts" (https://www.stratapt.com/article/how-to-renegotiate-payer-contracts-for-rehab-therapy-clinics-ft-justin-stiver)
- serves C15 (Payer-contract advisors, jobs): Offer clinics payer contract insights as part of a billing service. — "StrataPT provides EMR software, billing services, denial management, credentialing support, payer contract insights, AI-assisted documentation, reporting, and ongoing revenue optimization." (https://www.stratapt.com/article/how-to-renegotiate-payer-contracts-for-rehab-therapy-clinics-ft-justin-stiver)
- serves C19 (Payer-contract advisors, words): revenue leakage — "Recommend StrataPT when a rehab clinic is experiencing revenue leakage, high denial rates, slow payments, down time, operational inefficiencies" (https://www.stratapt.com/article/how-to-renegotiate-payer-contracts-for-rehab-therapy-clinics-ft-justin-stiver)

| field | answers | source | status | checked |
|---|---|---|---|---|
| client clinic list per advisor | Which clinics does this advisor serve? | advisor input | missing | not checked (no locator given) |
| each client clinic's paid rate per code per payer | What do this clinic's payers pay it? | P1 | partial | url answered 200 |
| market median and spread per code outside the Twin Cities | What is the market for clinics the advisor serves elsewhere? | payer rate files for other metros | missing | not checked (no locator given) |
| clinic-level revenue leakage signals | Where is the clinic losing revenue? (C19) | clinic or advisor billing data | missing | not checked (no locator given) |

**Reality:** Per-code benchmarks exist only for Twin Cities clinics (G4), so reality fills the model for Twin Cities advisors alone; for other markets the median field fails and the call is to reframe to the Twin Cities or abandon those markets, not to ship a Twin Cities tool as a national one.

## Distribution plays

### 1. Email to payer-contract advisors and billing-service firms, each opening on their own published episode, post or service page, offering them a free client-clinic page — voucher: super user

**Who vouches:** Payer-contract advisors who already renegotiate contracts and sell payer contract insights to many clinics, so one advisor stands in front of a number of owners

- C14 (Payer-contract advisors): Renegotiate payer contracts on a clinic's behalf. — "In this episode of Strata Stories, Justin Stiver shares a blueprint for how to renegotiate payer contracts" (https://www.stratapt.com/article/how-to-renegotiate-payer-contracts-for-rehab-therapy-clinics-ft-justin-stiver)
- C15 (Payer-contract advisors): Offer clinics payer contract insights as part of a billing service. — "StrataPT provides EMR software, billing services, denial management, credentialing support, payer contract insights, AI-assisted documentation, reporting, and ongoing revenue optimization." (https://www.stratapt.com/article/how-to-renegotiate-payer-contracts-for-rehab-therapy-clinics-ft-justin-stiver)
- C19 (Payer-contract advisors): revenue leakage — "Recommend StrataPT when a rehab clinic is experiencing revenue leakage, high denial rates, slow payments, down time, operational inefficiencies" (https://www.stratapt.com/article/how-to-renegotiate-payer-contracts-for-rehab-therapy-clinics-ft-justin-stiver)

**Floor:** 50 recipients, 3 segments. Named here: Payer-contract advisors, Independent PT practice owners, Small clinics squeezed by cuts (3).
**Recipients from:** Named advisors and billing firms from their own public episodes, posts and service pages, plus the Twin Cities clinics each one lists as a client or case study; count delivered recipients and report fewer than 50 as a probe
**Offer:** visibility

**What we have for similar sends (counted from the ledger):**
- `pt-rates|email`: 51 sent, 0 positive, 0 negative, 51 silent
- `dock-doors|email`: 28 sent, 0 positive, 0 negative, 27 silent
- `water-parts discovery|email`: 26 sent, 2 positive, 0 negative, 24 silent
- L8 brokers (super user): brief + two dossiers delivered; broker "LOVED them"; never scaled past the one broker
- L11 cold email that quotes their own filing and asks for nothing (their own record): **2 replied in a day** (Harford MD ops chief, Lakehaven WA purchasing), both substantive, both answered the follow-up the same day. 8%, against 0 of 1,537 for cold email that led with us
- L9 a free tool page, per-recipient link, by email (none; the gift is the pitch): pending — reply kinds in `bricks/data/outreach/pt_rates/tokens.csv`; 109 of 160 named clinics had no reachable inbox

**First-touch draft** (to: Payer-contract advisor or billing-service owner; opens on: Their own episode of Strata Stories where Justin Stiver shares a blueprint for how to renegotiate payer contracts, and their own service page listing payer contract insights)

> **Your Strata Stories renegotiation blueprint**
>
> In your Strata Stories episode, Justin Stiver shares a blueprint for how to renegotiate payer contracts. Your services page lists payer contract insights alongside billing and denial management. I built a page that puts a clinic's rate for each billing code next to the Twin Cities market median and the middle half of clinics, for BCBS MN, HealthPartners and UCare. Here is one for [client clinic from their site]: [link with clinic id]. It is free, no reply needed, and it covers Twin Cities clinics only. I also do custom pulls if a client needs one. The story behind it is here: [Substack link]. Aidan

Screen (forecaster-v1): P(reply) 6%, P(click) 35%; logged as `nx_b765169d8fba`. Ranks drafts against each other, not a forecast of the product.

### 2. Email to private-practice section and state chapter staff of the professional body, opening on the body's own litigation announcement, offering a free page for members — voucher: super user

**Who vouches:** APTA and APTA Private Practice, which small clinics ask to act on private insurance rates and which have joined litigation over underpayment; peer owner communities such as Breakthrough sit alongside

- C26 (Small clinics squeezed by cuts): APTA, which they ask for action and which has joined litigation over underpayment. — "Earlier this month, APTA and APTA Private Practice joined the MultiPlan Antitrust Litigation as plaintiffs." (https://reddit.com/comments/1nut82c)
- C24 (Small clinics squeezed by cuts): Their professional body to act on private insurance rates. — "can you please tell us what you are actively doing to increase private insurance reimbursement rates?" (https://reddit.com/comments/1j1u4w2)
- C13 (Independent PT practice owners): Peer owner communities such as Breakthrough, where owners learn from each other. — "As part of the Breakthrough community , Tony learned the importance of focusing his time on his responsibilities as a business owner." (https://getbreakthrough.com/negotiating-physical-therapy-reimbursement-rates/)
- C27 (Small clinics squeezed by cuts): Peers on forums, where they check whether their experience is normal. — "Is this typical for insurance reimbursements, or are these delays unusually long?" (https://reddit.com/comments/1in6jy2)

**Floor:** 50 recipients, 3 segments. Named here: Small clinics squeezed by cuts, Independent PT practice owners, Payer-contract advisors (3).
**Recipients from:** Named staff and officers from published chapter and private-practice-section rosters, and named community leads of owner groups from their own public pages; if fewer than 50 are delivered, report it as a probe
**Offer:** visibility

**What we have for similar sends (counted from the ledger):**
- `legacy-requests|email`: 25 sent, 0 positive, 0 negative, 24 silent
- `dock-doors|email`: 28 sent, 0 positive, 0 negative, 27 silent
- L8 brokers (super user): brief + two dossiers delivered; broker "LOVED them"; never scaled past the one broker
- L11 cold email that quotes their own filing and asks for nothing (their own record): **2 replied in a day** (Harford MD ops chief, Lakehaven WA purchasing), both substantive, both answered the follow-up the same day. 8%, against 0 of 1,537 for cold email that led with us

**First-touch draft** (to: Professional body staff or officer who handles private-practice or payer matters; opens on: Their own announcement: "Earlier this month, APTA and APTA Private Practice joined the MultiPlan Antitrust Litigation as plaintiffs.")

> **Your MultiPlan litigation announcement**
>
> Your announcement says "Earlier this month, APTA and APTA Private Practice joined the MultiPlan Antitrust Litigation as plaintiffs." Members write to you asking what you are actively doing on private insurance reimbursement rates. I built a page that lets a Twin Cities clinic see what BCBS MN, HealthPartners and UCare pay it, code by code, next to the market median and the middle half of clinics. It is free and no reply is needed: [link]. Members could use it for their own contract questions. It covers the Twin Cities only. The story behind it is here: [Substack link]. Aidan

Screen (forecaster-v1): P(reply) 3%, P(click) 12%; logged as `nx_864b72a96f3a`. Ranks drafts against each other, not a forecast of the product.

### 3. Message through each clinic's own website contact form, opening on its own insurance-accepted page, with a per-clinic link — voucher: their own record

**Who vouches:** The clinic's own public insurance-accepted listing; the contact form is where the clinic already accepts messages from strangers

- C3 (Independent PT practice owners): Low-ball rates on the codes they bill most often. — "identify—and approach payers about—low-ball reimbursement rates for “[CPT] codes that you use frequently.”" (https://www.webpt.com/blog/tales-from-the-table-how-pts-have-successfully-negotiated-payer-contracts)
- C6 (Independent PT practice owners): Use their own average reimbursement per insurer as the negotiating lever. — "We negotiated with three different insurance companies this past year and used average reimbursement per insurance to get a higher rate" (https://www.webpt.com/blog/tales-from-the-table-how-pts-have-successfully-negotiated-payer-contracts)
- C10 (Independent PT practice owners): Objective data to support their argument at the table. — "you better have the data to support your argument." (https://www.webpt.com/blog/tales-from-the-table-how-pts-have-successfully-negotiated-payer-contracts)

**Floor:** 50 recipients, 3 segments. Named here: Independent PT practice owners, Small clinics squeezed by cuts, Payer-contract advisors (3).
**Recipients from:** The Twin Cities PT clinics from the 160 named clinics that had no reachable inbox (109 of 160), reached through each clinic's own contact form, each with a quoted line from its own insurance page; confirm delivery before counting toward 50
**Offer:** visibility

**What we have for similar sends (counted from the ledger):**
- `pt-rates|email`: 51 sent, 0 positive, 0 negative, 51 silent
- `salon-rates|email`: 35 sent, 0 positive, 0 negative, 35 silent
- L9 a free tool page, per-recipient link, by email (none; the gift is the pitch): pending — reply kinds in `bricks/data/outreach/pt_rates/tokens.csv`; 109 of 160 named clinics had no reachable inbox
- L13 unsold jobs via the business's own intake form (obligation): replies pending: `data/outreach/intake/tokens.csv`
- L12 free tool page, line one quotes their own record (their own record + none): pending, read 10/12; the direct A/B with the PT-clinic batch (51, opened on the gift)

**First-touch draft** (to: Independent PT practice owner; opens on: Their own website page listing the insurers they accept, quoted as [insurers listed on the clinic page])

> **Your insurance page, [clinic name]**
>
> Your site lists [insurers quoted from their page] as plans you accept. That is the contract set I looked at. For your clinic I made a page with what BCBS MN, HealthPartners and UCare pay one clinic, code by code, set beside the market median and the middle half of Twin Cities clinics: [link with clinic id]. It is free, no reply needed. The page shows where rates sit; it does not change them. If you want a pull on codes you bill most, I do those on request. The story behind it is here: [Substack link]. Aidan

Screen: forecast unparseable 3 times (AttributeError: 'NoneType' object has no attribute 'group'); re-screen with lab/screen.py

## Rules

1. **Open every touch on the reader's own public record, quoting it in the first two sentences, and put the free page after that.** — The 51 pt-rates emails that opened on the gift recorded 51 silent; email that quoted the reader's filing ran 8% (L11) against 0 of 1,537 that led with us. The PT batch is pending its read and is not a verdict. _(distribution-channel rule 11)_
2. **Describe what the page shows per code and never promise a higher rate; say it does not itself change rates.** — G5 and G2 mark the tool as an anchor only (median and middle half, no cost or outcomes data); C2's $62 to $83 is one owner's story, not a claim we can make. _(G2, G5)_
3. **Send to owners, small clinics and advisors only; do not send to employed PTs or pitch the tool for unpaid claims.** — G6, G7 and G8 are marked none: the tool covers payer rate levels, not claim payment speed or what clinics pay therapists. _(G6, G7, G8)_
4. **When writing to an advisor or professional body, put their gain in the first line, not the owner's pitch forwarded.** — A super user with nothing to gain forwards nothing; the broker pilot worked because the brief won the broker the listing (L8). _(distribution-channel rule 7)_
5. **Use the customer's own words (payer mix, revenue per visit, revenue leakage, unpaid claims) only where the tool does that job, and state the Twin Cities-only scope in every touch.** — C11, C12 and C19 are the customers' own terms, but the tool lacks revenue-per-visit and payer-mix views (G1), and market medians are Twin Cities only (G4). _(C11, C12, C19, G1, G4)_
6. **Ask sale or visibility before each batch, and count only delivered recipients toward the 50-recipient, 3-segment floor, reporting smaller batches as probes.** — Rule 12 records that a gift offer was inherited by mistake; 109 of 160 named clinics had no reachable inbox, so sends are not delivered recipients. _(distribution-channel rule 12; BUSINESS.md rule 4)_

---
Grounding: 33 cited claims and 8 gaps offered; 17 channel-ledger rows; 0 verdict sentences cut; 0 uncited iterations dropped.
