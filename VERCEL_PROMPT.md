# Vercel prompt for iMessage4Me

Build a complete static marketing website for iMessage4Me.

iMessage4Me is a local Mac app that helps people search, preserve, browse, export, and analyze their iMessage history. It reads the Apple Messages database on the user Mac. The actual product does not upload messages. It does not use cloud processing. It does not use API keys. It does not require technical setup.

The site must feel human made. It should not look like a Claude generated website, a Codex generated website, a generic AI landing page, or a template with predictable cards and vague gradient decoration.

The design should feel like a careful product designer made it for a private Mac utility. It should be quiet, premium, practical, emotionally aware, and trustworthy.

Primary message

Your messages are stored locally and Apple makes them nearly impossible to access. iMessage4Me gives you your history back.

Core product truth

The website is only the public marketing site. The actual product is a local Mac app. Do not imply that the website can read, process, upload, or search messages.

Hard privacy promise

Everything stays on your Mac.

Reads from your local Messages database.

No cloud.

No API keys.

No message uploads.

No network access for message processing.

Visual direction

Make it look like a real Mac product site, not a startup template.

Use a warm neutral background.

Use deep ink text.

Use restrained blue for primary actions.

Use green only for privacy and safety status.

Use subtle borders, soft shadows, generous spacing, and a real product mockup.

Avoid purple gradients.

Avoid floating gradient blobs.

Avoid fake glass panels everywhere.

Avoid rows of generic feature cards as the main design.

Avoid overly shiny AI style visuals.

Avoid cartoon illustrations.

Avoid bland SaaS icons unless they are small and useful.

Avoid a hero that looks like every other AI tool page.

This should feel closer to an Apple utility, Things, Linear, Rewind, Raycast, CleanMyMac, or Arc style product page than a generic AI app launch page.

Human design requirements

The page should have a clear editorial rhythm, not just stacked sections.

Use asymmetry where it helps.

Use small details that feel hand placed.

Use real product interface language.

Use fewer decorative elements and more meaningful product details.

Use mockups with believable fake messages, not abstract screenshots.

Use specific copy instead of generic claims.

Do not use phrases like unlock your potential, supercharge your workflow, seamless experience, or powered by AI.

Do not use a fake testimonial section unless it is clearly marked as coming soon or omitted.

Do not claim App Store availability unless the page says coming soon.

Page structure

1. Hero

Brand name:
iMessage4Me

Headline:
Your iMessage history, finally yours again.

Supporting copy:
Apple stores your messages locally, but makes them hard to search, preserve, and export. iMessage4Me gives you a private Mac app for finding the messages that matter and saving the conversations you cannot lose.

Primary button:
Join the waitlist

Secondary button:
How privacy works

Hero mockup:
Create a realistic app interface mockup in HTML and CSS. The mockup should look like the current iMessage4Me product.

Mockup labels:
iMessage4Me
Private archive workspace
Search
Memories
Show SMS
Private Archive
Local only
Keyword
Contact
From
To
Attachment
Search
Clear
CSV
Reading from ~/Library/Messages/chat.db · no network access.

Fake result cards:
Maya Chen · iMessage · Today
Dinner plans moved to seven. I saved the address in Maps.

Mom · iMessage · May 9, 2022
Found the old photos. I will send them later tonight.

Bank Alert · SMS · Jun 14
Your verification code is ready.

Add a subtle conversation preview panel with fake bubbles. It should feel like a real product surface, not a decorative illustration.

2. Problem

Title:
Messages is where life happened. It should not be this hard to search.

Copy:
Native Messages search can return partial results, show only a few matches at a time, and miss messages people know exist. Exporting a full thread is awkward. Most people discover the problem when they urgently need to find or preserve something important.

3. Preservation

Title:
Built for conversations you cannot replace.

Copy:
Some message threads are not just data. They are a record of a parent, a partner, a close friend, a family moment, or a relationship that changed your life. iMessage4Me helps you preserve those conversations in a format you can actually read and keep.

Use four quiet feature blocks:
Preserve a full conversation
Search by memory, phrase, date, or person
Export a readable copy
Keep the archive on your own Mac

4. Search

Title:
Full text search across your local message history.

Copy:
Search by keyword. Filter by contact. Narrow by date range. Filter by attachment type. Open full conversation context from any result.

Show a compact fake filter strip:
Keyword
Contact
From
To
Attachment
Any
Images
Videos
Audio
Files

5. Export

Title:
Export should be core, not an afterthought.

Copy:
Save a full thread as PDF, HTML, CSV, or plain text. Export search results to CSV. Create readable archives for personal records, family history, or important memories.

Show format chips:
PDF
HTML
CSV
Text

6. Privacy

Title:
Private by design because messages are private by default.

Use this exact status line:
Reading from ~/Library/Messages/chat.db · no network access.

Copy:
The Mac app reads a temporary local copy of the Messages database. Your original database is not modified. Message contents are not uploaded. Processing happens locally.

Trust blocks:
Local Mac processing
Read only access
No cloud storage
No message uploads

7. How it works

Three steps:
Install the Mac app.
Grant Full Disk Access so macOS allows the app to read the local Messages database.
Search, browse, and export your history.

Explain that Full Disk Access is required by macOS because Apple protects the Messages database.

8. Waitlist

Title:
Get early access to iMessage4Me.

Copy:
Join the waitlist for the local Mac app that helps you search and preserve your message history.

Form fields:
Email
What do you most want to preserve or search

Button:
Join the waitlist

Privacy note:
We will only use your email for iMessage4Me updates.

Use Vercel friendly form structure. If there is no backend, make the form visually complete and include a clear placeholder action. Do not add external services.

9. Footer

Include:
iMessage4Me
Local Mac app for searching and preserving iMessage history.
Privacy
Waitlist
Contact

Color palette

Background: #f4f1ea

Surface: #fffdf8

Ink: #1a1d24

Muted text: #69707d

Line: #e4dfd5

Primary blue: #2364d2

Soft blue: #e9f0ff

Privacy green: #14855f

Dark panel: #111827

Typography

Use the Apple system font stack.

Do not use oversized dramatic typography everywhere.

Use one strong hero headline and then calmer section titles.

Keep line lengths readable.

Layout guidance

Build as a responsive one page site.

Desktop should have a strong hero, product mockup, and clear sections.

Mobile should stack cleanly and keep the mockup readable.

Do not hide the privacy message on mobile.

Do not put every section in a card.

Use full width bands or open layouts where possible.

Functional requirements

Static website suitable for Vercel.

No backend required.

No external API calls.

No analytics by default.

No cookies.

No fake message processing.

No real message data.

Use only fake sample messages.

Final output

Create a complete responsive landing page for iMessage4Me.

Make it look like a public website for a real Mac utility that protects private memories.

The final page should feel designed by a thoughtful human, not generated by an AI agent.
