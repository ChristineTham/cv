# Chris Tham — CV and portfolio

[![Deploy to GitHub Pages](https://github.com/ChristineTham/cv/actions/workflows/deploy.yml/badge.svg)](https://github.com/ChristineTham/cv/actions/workflows/deploy.yml)

My personal CV and portfolio site, live at **[christham.net/cv](https://christham.net/cv/)**. Two
print-ready PDFs and a browsable site, all generated from one set of Markdown files.

Built on [Spotlite](https://hellotham.com/spotlite/), the MIT-licensed template of the same
codebase. This repository is the primary: Spotlite is produced from it by subtraction — see
[Two repositories](#two-repositories).

## Why it works this way

A CV is a document of record, and the failure mode of keeping one is drift: the PDF you email says
something different from the site you link to, because you updated one and forgot the other.

Here a role exists in exactly one place, `src/content/work/*.md`, and everything else follows from
it — the one-page résumé, the full CV, the work history pages, the career timeline and the search
index. **Curation is deterministic**: recency, seniority and explicit per-entry flags. Nothing in
the pipeline rewords, summarises or infers a career fact; editorial copy lives in `src/cv.json`
where a human can review it.

The PDFs are built for applicant tracking systems as well as people — single column, selectable
text, no layout tables, since multi-column CVs are read out of order by ATS parsers.

| File                    | Contents                                                                               |
| :---------------------- | :------------------------------------------------------------------------------------- |
| `public/cv-onepage.pdf` | Profile, key achievements, recent roles, condensed earlier career, education, skills   |
| `public/cv.pdf`         | Complete history with achievement bullets, education with awards, full competency list |

Both are committed, because `public/` is copied verbatim into the build and the site links to them.

## Getting started

```bash
pnpm install
pnpm run dev
```

`pnpm` is pinned via `packageManager` — not npm, not yarn. `postinstall` fetches Chrome for
Puppeteer, so the first install is slow.

| Command                  | Action                                                        |
| :----------------------- | :------------------------------------------------------------ |
| `pnpm run dev`           | Development server on `localhost:4321`                        |
| `pnpm run build`         | Production site **and** the Pagefind search index             |
| `pnpm run pdf`           | Build, then regenerate both CV PDFs into `public/`            |
| `pnpm run preview`       | Preview the production build                                  |
| `pnpm run test`          | Vitest suite once (27 files)                                  |
| `pnpm run test:coverage` | Tests with a v8 coverage report                               |
| `pnpm run lint`          | Prettier and ESLint — note this **writes**, it does not check |
| `pnpm astro check`       | Type and diagnostic check across `.astro` files               |
| `pnpm run refresh`       | Upgrade Astro and all dependencies                            |

Before calling a change done:

```bash
pnpm lint && pnpm astro check && pnpm test && pnpm build
```

`build` does **not** regenerate the PDFs. If you touched content, `src/cv.json` or
`src/utils/cv.ts`, run `pnpm run pdf` as well — the PDFs are committed and go stale silently.

## Stack

Astro 7 (static, Content Layer API) · UnoCSS Wind4 · TypeScript strict · Vitest · Pagefind
search · Puppeteer for the PDFs · D3 and Mermaid for visualisations · KaTeX for maths ·
PhotoSwipe lightbox. Deployed to GitHub Pages from `/cv/`.

Deliberately **not** Netlify — support was removed on purpose.

## Structure

```text
/
├── AGENTS.md              # Agent brief: architecture, commands, and a long Traps section
├── CLAUDE.md              # Auto-loaded rules; the two-repository workflow
├── DESIGN.md              # The Rosely design system
├── .claude/               # Hooks, skills and agents — see below
├── public/                # Copied verbatim: PDFs, icons, and the document archive
├── scripts/generate-pdf.js
├── tests/                 # 27 Vitest files, several asserting against built dist/
└── src/
    ├── content/           # Every collection: work, education, article, project, …
    ├── components/        # Astro components, D3 charts, modals
    ├── layouts/           # layout.astro is the shell every page passes through
    ├── pages/             # File-based routing, incl. the print-only /cv routes
    ├── styles/            # Rosely palette, Mermaid and Shiki themes, alerts
    ├── utils/             # cv.ts curation, timeline, Markdown extensions
    └── cv.json            # Contact details, headline, summary, curation limits
```

Content is the Astro **Content Layer API**: `article` (20), `project` (40), `passion` (38),
`work` (34), `creation` (12), `education` (7), `page` (7) and `social`, each with a strict Zod
schema in `src/content.config.ts`. Navigation is **inferred** from the `page` collection, so
adding a page is a Markdown file rather than a route — there is no menu data file.

## The archive

`public/` carries 16 original historical documents — Word manuscripts, conference decks, scans and
contemporaneous HTML exports, the earliest being a 1987 honours thesis. Several articles reproduce
a paper or thesis from its source and link to the original, stating in a preface what was repaired
and why.

These are personal documents and live in this repository **only**; the Spotlite template ships no
archive.

## Two repositories

The same site is deployed twice, from repositories with **no shared history and no merge path**:

|                       | repository           | site                                             | base         |
| :-------------------- | :------------------- | :----------------------------------------------- | :----------- |
| **primary**, personal | `ChristineTham/cv`   | [christham.net](https://christham.net/cv/)       | `/cv/`       |
| alternate, template   | `hellotham/spotlite` | [hellotham.com](https://hellotham.com/spotlite/) | `/spotlite/` |

Work happens here and is backported to Spotlite, which is this repository minus the archive, minus
the download links pointing at it, and minus the agent tooling. The direction matters: here the
source manuscripts are to hand, so a reproduction can be checked against its original.

## Claude Code configuration

This repository is set up for [Claude Code](https://claude.com/claude-code), and that
configuration lives here only — Spotlite is a template and ships the site, not the machinery for
maintaining one copy of it.

**`CLAUDE.md`** is loaded automatically into every session. It is deliberately short and covers
only what the other documents do not: the two-repository workflow, the Markdown extensions, the
house pattern for reproduced documents, and the check to run before calling anything done.

**`AGENTS.md`** is the full brief — stack, commands, content model, the CV pipeline, and a long
**Traps** section where every entry is a real debugging session (Astro's cache lying to you,
UnoCSS resolving variants before shortcuts, Mermaid baking colours in at render time, `oklch()`
computed colours that cannot be parsed by hand). It is _not_ auto-loaded, so `CLAUDE.md` tells
Claude to read it.

**`.claude/hooks/`**

| Hook                    | Fires on   | Purpose                                                                                                                                                                       |
| :---------------------- | :--------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `check-sibling-repo.py` | Edit/Write | Compares each written file against its twin in the other repository, normalising the base path and host first. Refuses archive files and agent tooling written into Spotlite. |
| `report-push-state.py`  | Bash       | After any `git push`, reports where **both** repositories stand — a `cd` persists between commands, so a push meant for one can land in the other twice.                      |

**`.claude/skills/`**

| Skill                  | Use                                                                                                                 |
| :--------------------- | :------------------------------------------------------------------------------------------------------------------ |
| `write-in-my-voice`    | Draft or revise an article in my voice, Australian English, via a draft–critique–revise loop against published work |
| `reproduce-document`   | Add a paper or thesis as a faithful reproduction following the house pattern                                        |
| `legacy-office-source` | Read a legacy `.DOC` or `.PPT` and recover its figures as SVG                                                       |
| `sync-both`            | Backport to Spotlite, check both, push primary-first, confirm both deploys                                          |

`sync-both` is invoked by name as `/sync-both`; it is marked `disable-model-invocation` because it
commits and pushes two repositories.

**`.claude/agents/`** holds `content-fidelity-verifier`, which checks a converted document still
says everything its source said, and `responsive-contrast-auditor`, which audits built pages for
horizontal overflow and contrast across breakpoints and both themes — two defect classes that are
invisible by looking at the page.

## Deployment

Pushing to `main` triggers `.github/workflows/deploy.yml` (`withastro/action`), which builds and
publishes to GitHub Pages under `/cv/`. The badge above reports the most recent run.

**This repository is public.** Anything committed is published, including git history.

## Licence

MIT — see [LICENSE](LICENSE). The code is free to reuse; the CV content and the document archive
are mine. If you want the template rather than my biography, fork
[Spotlite](https://github.com/hellotham/spotlite).
