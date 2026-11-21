# Julia's Dedicated Plugin: product decisions

One add-on for one student, with a dedicated maintainer. It replaces a pile of
single-purpose add-ons with one coherent, configurable suite, and it keeps
working across Anki releases.

## Principles

- **One add-on, many modules.** Every feature is a module that can be turned
  on/off and configured from a single settings screen with one visual design.
- **Settings follow her.** Stored in the collection config so they sync via
  AnkiWeb between her computers.
- **Never broken by Anki updates.** Tested against each Anki release and beta
  (seeded dev collection + screenshot tooling) before she updates.
- **Direct line to the maintainer.** An in-app feedback button files a GitHub
  issue with context (Anki version, current screen). Fixes ship as AnkiWeb
  updates.
- **Beautiful and hers to customize.** UI/UX polish is a first-class goal,
  not a pass at the end. Every screen she sees daily gets one coherent design
  system, and she can make it her own (see Theme below). A feature isn't done
  until it looks finished in light and dark mode, on desktop and (for card
  styling) on mobile.
- **Nothing subject- or exam-specific.** No MCAT assumptions; she defines her
  own exams and topics.
- **No gimmicks.** No pets, puppies or photo albums; features that Anki now
  ships natively (FSRS helpers, load balancer) are left to Anki.

## Modules

| Module | Replaces | Summary | Default |
| --- | --- | --- | --- |
| Theme | — | One design system across every web-based Anki screen: deck list, overview, reviewer and its answer bar, toolbars, congrats screen, and our own screens. Presets plus customization (accent color, background, fonts, card text size, density, corner roundness, light/dark), with live preview in settings. Settings sync, so it looks the same on all her computers. | on |
| Readable cards | — | Injected card styling: answer first, collapsible extra fields, zoomable images, better tables, proper dark mode. Template-level, so it also shows on mobile. | on |
| Session display | — | Progress, cards left, estimated finish time from her own pace. | on |
| Fatigue signal | — | Gentle notice when accuracy and speed drop late in a session. **Toggleable.** | off |
| Pacing timer | Life Drain, Speed Focus | Per-card time pressure. **Toggleable.** | off |
| Morning briefing | Review Heatmap, More Overview Stats, True Retention | Home-screen summary: today's estimated time, 7-day forecast, retention, streak (no guilt), upcoming exams. | on |
| Edit while reviewing | Edit Field During Review | Fix a card's text in place during review. | on |
| Trouble-card workshop | Advanced Browser (partly) | Cards she keeps failing, surfaced before Anki suspends them, with history and quick rewrite/split/mnemonic tools. | on |
| Exam planner | — | See below. | on |
| Shortcuts | Customize Keyboard Shortcuts | Key bindings in the shared settings screen. | on |

## Exam planner

How students plan today: exam dates in a calendar, a syllabus spreadsheet of
chapters to cover by when, manual math for new cards per day, unsuspending
cards lecture by lecture, and a filtered deck to cram the week before. The
planner puts all of that in one place.

- **Exam** = name, date, and a scope made of **topics**.
- **Topic** = her own name for a chunk of material (chapter, lecture, unit…)
  plus what it covers in Anki: a deck, a tag, or any Anki search. Optional
  "covered by" date per topic for syllabus pacing.
- **Plan:** cards still new in scope ÷ study days left before a review buffer
  (default: last week before the exam) → recommended new cards per day, with
  projected daily review load and warnings when exams collide.
- **By-topic insights:** learned/total, recent retention, predicted recall on
  exam day, trouble cards, and ahead / on track / behind against the plan.
- **Actions:** unsuspend a topic (for "unsuspend as you go" workflows),
  apply the recommended new-cards/day, and build a pre-exam review deck of
  in-scope cards with the lowest predicted exam-day recall.

Open technical question: predicted recall needs a memory model. Anki's FSRS
can compute memory state from review history even for SM-2 users; confirm the
26.09 backend APIs for memory state, retrievability at a future date and the
workload simulator.

## Release plan

- **v1 (birthday):** module framework, shared settings + sync, feedback
  button, theme, readable cards, session display, morning briefing.
- **Then roughly monthly:** exam planner → trouble-card workshop → anything
  her feedback asks for.
