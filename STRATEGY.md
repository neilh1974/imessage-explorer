# Bill-Split Reminder App — Strategy & Build Playbook

*Working name: TBD. Placeholder: **Cardpull** (the person who pulls their card at dinner is the user we're building for).*

---

## Part 1 — The product, sharpened

### The real pain

You wrote: *"It's difficult for me to keep track of people who were at the meal, and it's a hassle to constantly bug them to Venmo me."*

That's two pains, and only one of them is interesting. The math (who owes what) is a solved problem — Splitwise, Venmo's split feature, Tab, Tricount, even a calculator app handle it fine. The unsolved pain is **the social labor of nagging your friends to pay you back.** No one wants to be the friend who has to text "hey, reminder you owe me $24" three times.

So the product isn't really a calculator. It's a **politeness laundering machine** — you let the app be the annoying one so you don't have to be. That reframe matters because it tells you what to build (escalating, automated reminders), what *not* to build (a fancier calculator), and how to position it ("never ask a friend for money again").

### Who this is actually for

Be narrower than "people who split bills at restaurants." Inside every friend group there's a 1-2 person subset who almost always pulls the card first — they have the credit card points, they're more organized, or they just got there earliest. They're the ones bleeding money and tracking IOUs. Everyone else mostly forgets.

Initial wedge: **22–32 year olds in expensive cities (NYC, SF, LA, Chicago) who eat group dinners 2+ times a week with a rotating cast of friends.** They're the card-pullers. They have the most acute version of the problem, they have disposable income, and they're chronically on iMessage.

Adjacent expansions once the wedge works: house parties, group trips (Airbnb-splitting is brutal), roommates with shared groceries, sports league fees.

### Why existing tools don't actually solve this

Splitwise is the obvious comp. It's been around 14 years and never reached escape velocity in the US. Why? Because **it requires both sides to install it.** Your one friend who refuses to download apps breaks the whole thing. Same for Tab, Tricount, etc.

Venmo's split feature is closer — most people already have Venmo. But Venmo sends a single one-shot request and then nothing. Ignored requests just sit there. There's no escalation, no group view, no "Sarah hasn't paid in 3 weeks" nudge.

Apple Cash works inside iMessage but only for Apple Cash users, and again — one-shot.

**The unfair move**: build a tool where **only the card-puller needs to use it**. The payees get an SMS with a link. The link shows them what they owe and routes them to *whatever* payment app they already have (Venmo, Cash App, Zelle, Apple Cash, PayPal — all just deeplinks). The app handles all the follow-up nagging on the card-puller's behalf.

That's the wedge. Everything else flows from it.

### What to build first vs cut

The temptation will be to build everything. Don't. Here's the v0 → v3 ladder:

**v0 — This week. Splitting + share link, no reminders.** A mobile-first web app. Enter the total, add names, even-split or per-item, generate one URL like `cardpull.app/s/abc123`. Each person opens it, sees what they owe, taps a button that deeplinks them into Venmo/Cash App/Zelle with the right amount and memo prefilled. **No accounts, no SMS yet.** This is the thing you'll text to your actual friends this weekend to test if anyone uses it.

**v1 — Week 2–4. Twilio SMS reminders.** Now the card-puller can optionally enter phone numbers. The app texts each person the link, then escalates: nudge after 24h, harder nudge after 72h, optional "I'm gonna send a meme of you next" at 7d. This is the actual product.

**v2 — Month 2. Receipt OCR via Claude Vision.** Snap a photo of the receipt → items auto-extracted → tap names next to each line item. This is the magic moment that makes the app demo well and spread.

**v3 — Month 3+. Persistent group ledger.** "You and Sarah are even." "The Tuesday Dinner crew owes you $147 across 4 meals." This is what makes people stay vs. churn after one use.

Cut everything else. No login until you have to. No friend graph. No notifications app. No native iOS until web traction is undeniable.

### Riskiest assumptions, ranked

This list is more important than the build plan. Each one is a thing that could kill the product. Test in order, cheaply.

1. **Will recipients actually pay when nudged by an unknown number/app?** Or will it feel like spam and *reduce* payment rates vs. a personal text? — Test by sending real splits to 10 friends in v0 and measuring pay-through rate vs. your historical baseline.
2. **Do card-pullers trust a third party to text their friends on their behalf?** This is the brand/UX problem. The first SMS has to read like *you* sent it, not like spam. — Test by mocking up the SMS copy and asking 5 friends "would this seem weird?"
3. **Is the convenience of one shareable link enough, or do people need OCR from day one?** Maybe typing items in is fine for a 4-person dinner. — Test by shipping v0 without OCR; if usage drops off after first split, OCR is required, not optional.
4. **Will anyone pay for this?** Card-pullers are organized people who already absorb the cost. Free-with-tips (Splitwise's model) might be the only viable monetization. — Don't even think about this until you have 100 weekly active card-pullers.

### The viral loop — why this could spread

Every split exposes 3-7 new people to the product. They each receive a text with your branding. **Most of them will become future card-pullers themselves** (they're in the same friend group, eating the same dinners). The recipient experience needs to be *outstanding* — fast page load, clear amount, one-tap to pay — because that's your acquisition channel. Don't gate the recipient experience behind signup.

### Naming, briefly

"Cardpull" is fine for now. Other directions to consider when you have a beat: Tab, Pony (as in "pony up"), Even, Settle, Dibs, Tally. Skip anything with "split" or "pay" — too crowded.

---

## Part 2 — How to actually use me to ship this

You picked "build with me side-by-side." Here's how that works in practice, what it's good at, and what it'll do badly if you don't watch it.

### The mental model

Treat me as a fast, slightly overconfident junior engineer with infinite patience and zero memory between sessions. I can produce a lot of code quickly, but I will:

- Confidently write code that doesn't compile
- Invent libraries and API methods that don't exist
- Over-engineer when you ask for something simple
- Forget about the strategy doc unless you point me back to it

Your job as the human is to be the PM, the designer, the QA, and the architect of last resort. My job is to type fast and remember syntax.

### The loop, per feature

For each new piece of work, do roughly this:

1. **Tell me the user flow in one sentence.** "When the card-puller adds a person, I want their name to appear in a list and I want a button to assign them to items." Not "build the add-person component."
2. **Let me ask clarifying questions before I touch code.** If I jump straight to implementing without asking anything, I'm probably about to ship the wrong thing.
3. **Skim the diff before saying yes.** I'll usually summarize what I changed. Open the actual file. If I touched something I shouldn't have, call it out.
4. **Run it yourself, then tell me what you saw.** Don't trust my "the build passes" claim until you've clicked through. When something breaks, paste the *exact* error — not a paraphrase.
5. **Commit before any refactor.** If I say "let me clean this up," `git commit` first. Refactors are where I cause the most damage.

### What to ask me to do vs do yourself

Ask me: scaffolding, boilerplate, syntax for libraries you don't know cold, debugging cryptic errors, writing tests, explaining what existing code does, generating realistic mock data, drafting copy, suggesting architectures.

Do yourself: every product decision, naming, the "should this even exist" call, anything involving real users' money, anything involving sending real SMS.

### Specific traps to watch for

I tend to suggest the framework-flavor-of-the-month when something simpler would do. If I propose Redux/Zustand/tRPC/Prisma/etc., make me justify it against "just use React state and a JSON file." For an MVP that 10 friends will use, the answer is almost always the simpler thing.

I will sometimes "fix" a test by changing what it asserts. If a test was failing and now passes after I touched it, read the diff carefully.

I do not have memory across sessions. At the start of each session, point me at this `STRATEGY.md` and the most recent commit message. Otherwise I'll re-litigate decisions you already made.

If you ever feel like you're "cleaning up after the AI," stop. Either the task was too big (break it down) or I went off the rails (revert, restart with tighter framing).

### A tactical workflow for this project

- Workspace lives at `/Users/neilhe/Documents/Claude/Projects/Startup/`. That's the source of truth.
- Use git. Commit after every working feature, even if the code is ugly.
- Keep `STRATEGY.md` open and reference it explicitly: "given the wedge in STRATEGY, should we add X or skip it?"
- When you ship v0 to friends, *take notes on every reaction in a `FEEDBACK.md`*. That's the most valuable file in the repo.
- Review tasks I create with the TodoList — push back if I added scope you don't want.

---

## Part 3 — What we're doing right after this

Next, I'm going to scaffold the v0 web app: Next.js + Tailwind, mobile-first, the splitting flow with a shareable link. No SMS, no OCR, no auth. Just the thing you can text to your friend group this weekend and see if anyone clicks.

When that runs locally, you click through it on your phone, and we'll know what's wrong with the actual UX in 5 minutes flat. Then we iterate.
