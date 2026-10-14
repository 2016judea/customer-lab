# Next: Demolition Notice

_2026-10-13 · `lab/next.py` · from `maps/demolition-permit-scrap-leads.json`. Nothing here says whether anyone will use or buy it (BUSINESS.md rule 2)._

## Iterations

### 1. For each new permit, the tool drafts a scrap-removal note to the winning contractor's scrap contact. The note opens on that contractor's own permit and names the building's likely recoverable materials.

**The step it does:** Find scrap sources by driving around neighborhoods, then work out who to talk to and what to say to get 'scrap removal for house clean outs' and 'form relationships' started.

- serves G10 (Scrap route builders, gap): Find scrap sources by driving around neighborhoods — "I started picking a bit in September, just driving around the neighborhood." (https://reddit.com/comments/1pk4yoc)
- serves G11 (Scrap route builders, gap): Offer scrap removal for house clean-outs and form relationships with local businesses — "Have expanded to doing some scrap removal for house clean outs and beginning to form relationships" (https://reddit.com/comments/1pk4yoc)
- serves C21 (Scrap route builders, jobs): Find scrap sources by driving around neighborhoods — "I started picking a bit in September, just driving around the neighborhood." (https://reddit.com/comments/1pk4yoc)
- serves C22 (Scrap route builders, jobs): Offer scrap removal for house clean-outs and form relationships with local businesses — "Have expanded to doing some scrap removal for house clean outs and beginning to form relationships" (https://reddit.com/comments/1pk4yoc)
- serves C24 (Scrap route builders, workarounds): They find material by driving around and picking, not from any list — "I started picking a bit in September, just driving around the neighborhood." (https://reddit.com/comments/1pk4yoc)
- serves C25 (Scrap route builders, words): scrap removal for house clean outs — "Have expanded to doing some scrap removal for house clean outs and beginning to form relationships" (https://reddit.com/comments/1pk4yoc)

| field | answers | source | status | checked |
|---|---|---|---|---|
| permit address, issue date and permit type | Which building is actually coming down, and when? | Minneapolis and Saint Paul demolition permit records (N1) | exists | url answered 200 |
| winning demolition contractor per permit | Who holds the job, so I know whose scrap I am asking about? | Permit record contractor field (N3) | partial | url answered 200 |
| scrap and salvage contact name, role, email or phone | Who do I contact about scrap on this job? | Contractor websites, state business filings, and the contractor's own published salvage or recycling statements | partial | not checked (no locator given) |
| recoverable materials estimate with the building age, size and use it came from | What is probably inside, so my note is specific to this building? | Tool step N2 from permit and assessor attributes | partial | url answered 200 |
| drafted opener quoting the contractor's own permit, plus a reader-supplied line about the sender's own scrap work | What do I say so the message is plainly about their job? | Model drafting over the permit row and the user's own text; the model supplies no numbers | exists | not checked (no locator given) |

**Reality:** Permits and estimates can fill most of the model, but the scrap contact per contractor is only partly fillable and residential clean-out leads are missing entirely, so reframe the goal to contractor scrap relationships and do not claim house clean-out leads.

### 2. A neighborhood teardown digest: the user picks an address or landmark in Saint Paul, and the tool reads new permits nearby and writes a plain-language summary of the teardown wave. It lists each building, its age, who is taking it down, and what changed since the last digest.

**The step it does:** Keep track of the wave of teardowns happening around the neighborhood, so the reader no longer has to scan permit lists.

- serves G1 (Saint Paul teardown neighbors, gap): Keep track of the wave of teardowns happening around their neighborhood — "How a teardown blitz is reshaping the neighborhood around the University of St. Thomas." (https://reddit.com/comments/1sklf7b)
- serves C1 (Saint Paul teardown neighbors, jobs): Keep track of the wave of teardowns happening around their neighborhood — "How a teardown blitz is reshaping the neighborhood around the University of St. Thomas." (https://reddit.com/comments/1sklf7b)
- serves C3 (Saint Paul teardown neighbors, pains): Neighbors are worried about the pace of teardowns near the university — "Teardown blitz worries University of St. Thomas neighbors." (https://reddit.com/comments/1sklmct)
- serves C5 (Saint Paul teardown neighbors, words): teardown blitz — "Teardown blitz worries University of St. Thomas neighbors." (https://reddit.com/comments/1sklmct)

| field | answers | source | status | checked |
|---|---|---|---|---|
| permit address geocoded to a neighborhood or distance from a chosen landmark | Which teardowns are near me? | Saint Paul permit records plus city address and neighborhood boundary data | partial | not checked (no locator given) |
| permit issue date history for the area | Is the pace changing around here? | Saint Paul permit records, counted from the data at read time | exists | url answered 200 |
| building age, size and use for each teardown | What is coming down: a house, a garage or a commercial building? | Tool step N2 inputs | partial | url answered 200 |
| winning contractor per teardown | Who is doing the work next door? | Permit record contractor field | partial | url answered 200 |
| what is planned to replace each building | What is going up in its place? | New-construction permits matched by address | missing | not checked (no locator given) |

**Reality:** Permits, dates and contractors can fill the model, but the replacement-building field is missing and the neighborhood geocode is partial, so reframe the digest around what is coming down until a matching new-construction source is found. Street light copper theft (G2) is outside the tool and is not served.

### 3. The tool reads each building's age, size and use and drafts an item-class salvage walkthrough list for estimators, covering reclaimed building materials and architectural salvage classes typical of that building type.

**The step it does:** Handle reclaimed building materials and architectural salvage: decide which classes to look for in this building and write the list a crew or buyer can walk.

- serves G6 (Demolition contractors and estimators, gap): Handle reclaimed building materials and architectural salvage — "handling reclaimed building materials, architectural salvage and good old fashioned ground dirt" (https://reddit.com/comments/1l8i4gl)
- serves C9 (Demolition contractors and estimators, jobs): Handle reclaimed building materials and architectural salvage — "handling reclaimed building materials, architectural salvage and good old fashioned ground dirt" (https://reddit.com/comments/1l8i4gl)
- serves C12 (Demolition contractors and estimators, words): design for disassembly or deconstruction — "specialize in design for disassembly or deconstruction" (https://reddit.com/comments/1gwuj0w)

| field | answers | source | status | checked |
|---|---|---|---|---|
| year built, gross floor area, use and construction type | What kind of building is this, and what era of material is in it? | County assessor records matched to the permit address | partial | not checked (no locator given) |
| item-level salvage inventory (doors, fixtures, timber, brick, metals) | Which reclaimed items are in this specific building? | On-site walkthrough or photos supplied by the estimator; no public source holds this | missing | not checked (no locator given) |
| salvage class guidance by building era and use | What do buildings like this usually hold that is worth pulling before demolition? | Published deconstruction guides and reuse-center material lists read by the model | partial | not checked (no locator given) |
| buyer or reuse outlet for each class | Where does this material go once it is out? | Local reuse and architectural salvage dealers' own listings | missing | not checked (no locator given) |

**Reality:** Item-level inventory and reuse outlets cannot be filled from public data, so reframe: the tool reasons over the estimator's own walkthrough photos and notes (a customer-supplied input) and does not claim building-level item counts. Hazardous material findings such as suspected asbestos (G5) stay out of scope.

## Distribution plays

### 1. Email to scrap YouTube creators and scrapping-forum moderators, each opening on the video or thread their audience already points to, offering the free permit page as something to cover or link — voucher: super user

**Who vouches:** Scrapping forum peers and YouTube teardown videos are what new scrappers already follow for teardown advice, so the creator's fan-out is the trust.

- C20 (New copper scrappers): Scrapping forum peers and YouTube teardown videos — "I highly recommend scrapitall's YouTube video on it" (https://reddit.com/comments/1ux7clw)
- C18 (New copper scrappers): They watch peer YouTube videos for teardown advice, often after already starting — "I highly recommend scrapitall's YouTube video on it" (https://reddit.com/comments/1ux7clw)
- C13 (New copper scrappers): Take a first load of copper wiring to a scrap yard without embarrassing themselves — "Will they take copper wiring bundled up as in picture or do I need to tie it up a certain way for them to inspect it?" (https://reddit.com/comments/1nh3auj)

**Floor:** 50 recipients, 3 segments. Named here: New copper scrappers, Scrap route builders, Saint Paul teardown neighbors (3).
**Recipients from:** Named creators and moderators found by searching the forums and videos behind the C18 and C20 quotes; Saint Paul neighborhood newsletter editors and district council communicators found on their own posts about teardowns (C3). Hold the batch until at least 50 delivered named recipients, each with a looked-up video, thread or post, are listed.
**Offer:** visibility

**What we have for similar sends (counted from the ledger):**
- `permit-gifts|email`: 8 sent, 1 positive, 0 negative, 7 silent
- `wrecking-permit leads (ScrapWatch precursor)|email`: 3 sent, 0 positive, 0 negative, 3 silent
- `social-calendar|email`: 9 sent, 1 positive, 0 negative, 8 silent
- L8 brokers (super user): brief + two dossiers delivered; broker "LOVED them"; never scaled past the one broker
- L10 free counterparty list by email (their own record + none): **1 of 9 replied**, and it was one of the two whose own post was quoted: Joel Oine, Blue Vector, in 13 hours, "this certainly got my attention… extremely clever". The 7 picked from a database: silence. `~/Desktop/on-the-house/drafts/permits/README.md`
- L11 cold email that quotes their own filing and asks for nothing (their own record): **2 replied in a day** (Harford MD ops chief, Lakehaven WA purchasing), both substantive, both answered the follow-up the same day. 8%, against 0 of 1,537 for cold email that led with us
- L12 free tool page, line one quotes their own record (their own record + none): pending, read 10/12; the direct A/B with the PT-clinic batch (51, opened on the gift)

**First-touch draft** (to: scrap YouTube creator or forum moderator; opens on: Their video that a scrapping-forum poster pointed to with 'I highly recommend scrapitall's YouTube video on it'.)

> **Your video on [video title]**
>
> A scrapping-forum poster pointed to your video '[video title]' with 'I highly recommend scrapitall's YouTube video on it.' I watched it, and the part on [specific moment in the video] is the one I came back to. Minneapolis and Saint Paul issue demolition permits, and I put each new one on one page with an estimate of what materials are inside and who won the job. It's free and no reply is needed: [link]. If it is ever useful for a video or a forum thread, it is yours to use. I also do custom pulls. Story behind it: [Substack link]. Aidan

Screen (forecaster-v1 (max_tokens 400)): P(reply) 7%, P(click) 22%; logged as `nx_4d8ac197a6e9`. Ranks drafts against each other, not a forecast of the product.

### 2. Email quoting each recipient's own public record: the contractor's own issued permit, the route builder's own post, the neighborhood group's own teardown post — voucher: their own record

**Who vouches:** The reader's own permit, post or newsletter line proves the message is theirs alone; the Substack link is the credential.

- C21 (Scrap route builders): Find scrap sources by driving around neighborhoods — "I started picking a bit in September, just driving around the neighborhood." (https://reddit.com/comments/1pk4yoc)
- C22 (Scrap route builders): Offer scrap removal for house clean-outs and form relationships with local businesses — "Have expanded to doing some scrap removal for house clean outs and beginning to form relationships" (https://reddit.com/comments/1pk4yoc)
- C3 (Saint Paul teardown neighbors): Neighbors are worried about the pace of teardowns near the university — "Teardown blitz worries University of St. Thomas neighbors." (https://reddit.com/comments/1sklmct)
- C7 (Demolition contractors and estimators): Meet permit prerequisites before a demolition permit can be pulled — "you must provide a Rat Abatement Certificate before pulling a demolition permit" (https://reddit.com/comments/1ka2fa8)

**Floor:** 50 recipients, 3 segments. Named here: Demolition contractors and estimators, Scrap route builders, Saint Paul teardown neighbors (3).
**Recipients from:** Contractors named on recent Minneapolis and Saint Paul demolition permits (their own permit); route builders found through their own public posts like the one in C21 and C22; Saint Paul neighbors found through their own public posts or newsletters about the teardown blitz (C3, C5). Hold the batch until at least 50 delivered named recipients are listed, each with a quotable record.
**Offer:** visibility

**What we have for similar sends (counted from the ledger):**
- `contractors (permit pullers)|email`: 8 sent, 0 positive, 0 negative, 8 silent
- `permit-gifts|email`: 8 sent, 1 positive, 0 negative, 7 silent
- `wrecking-permit leads (ScrapWatch precursor)|email`: 3 sent, 0 positive, 0 negative, 3 silent
- `water-parts discovery|email`: 26 sent, 2 positive, 0 negative, 24 silent
- L11 cold email that quotes their own filing and asks for nothing (their own record): **2 replied in a day** (Harford MD ops chief, Lakehaven WA purchasing), both substantive, both answered the follow-up the same day. 8%, against 0 of 1,537 for cold email that led with us
- L10 free counterparty list by email (their own record + none): **1 of 9 replied**, and it was one of the two whose own post was quoted: Joel Oine, Blue Vector, in 13 hours, "this certainly got my attention… extremely clever". The 7 picked from a database: silence. `~/Desktop/on-the-house/drafts/permits/README.md`
- Y1 (a yes) Joel Oine, Blue Vector Bookkeeping: reply in 13 h, "extremely clever", asked what the story is
- L14 own-quote cold email + channel pitches (their own record + obligation): pending, readout 10/13
- L15 cold email, their own deed or post + free comp password (their own record; a gift by mistake): **1 positive reply the same day**: Tim Swierczek (TCREI podcast + meetup), a call booked for 10/15. Rest pending, read 10/19

**First-touch draft** (to: demolition contractor named on a recent permit; opens on: Their own issued demolition permit at [address], issued [date].)

> **Your permit at [address]**
>
> The city issued a demolition permit for [address] on [date], with [contractor] named as the contractor. The building is [age, size and use from the permit]. I put new Minneapolis and Saint Paul demolition permits on one page, each with an estimate of the recoverable materials inside and the scrap contact for the winning contractor. Yours is on it, and if the scrap contact shown for [contractor] is wrong, tell me who it should be and I will fix it. It's free, no reply needed: [link]. Not selling anything. Story behind it: [Substack link]. Aidan

Screen (forecaster-v1): P(reply) 4%, P(click) 22%; logged as `nx_5a0586c4dd20`. Ranks drafts against each other, not a forecast of the product.

## Rules

1. **Open every touch on the reader's own record: the contractor's permit, the route builder's post, the neighborhood group's teardown post. Never open on the tool.** — Email quoting the reader's own filing got 2 replies from about 25 sends (L11), and the one post-quoted send of two drew a reply in 13 hours (L10, Y1). The 1,405 uninstrumented sends and the 23 InMails that led with us drew nothing but one 'not interested' (L1, L7). _(distribution-channel rule 11)_
2. **Ask 'sale or visibility' before writing each batch, and do not inherit the offer line from an earlier batch. Put no comp passwords or free-access codes in a paid product's intro.** — The msp-house-index batch carried a free password by mistake after the offer instruction had expired when the price changed (L15). _(distribution-channel rule 12)_
3. **Do not describe the tool as pricing copper, grading wire, giving scrap-yard etiquette, tracking street light theft, or covering permit prerequisites such as the Rat Abatement Certificate.** — The map lists these as jobs the tool does not do (G2, G4, G7, G8, G9), and the Rat Abatement Certificate rule is from King County, not Minneapolis or Saint Paul. _(G2, G4, G7, G8, G9)_
4. **Use each segment's own words in copy: 'teardown blitz' for neighbors, 'scrap removal for house clean outs' for route builders, 'deconstruction' and 'salvage' for contractors.** — These are the phrases the segments use for themselves in the cited quotes, and each segment's copy should read as written for them. _(C5, C25, C12)_
5. **Do not call a channel failed before it has 50 delivered recipients across 3 or more segments and three touches with reply kinds logged. Count only delivered addresses.** — Smaller sends are probes, not verdicts, and in the ledger 109 of 160 named PT clinics had no reachable inbox, so a send that never arrived tests nothing. _(BUSINESS.md rule 4)_
6. **Treat the scrap contact field as unverified until a person has confirmed it. Invite corrections in the message and do not present the contact as confirmed.** — The tool gives the scrap contact at the winning contractor, but G11 and the ideal-field check mark that contact as only partly fillable. _(G11)_

---
Grounding: 25 cited claims and 12 gaps offered; 17 channel-ledger rows; 0 verdict sentences cut; 0 uncited iterations dropped.
