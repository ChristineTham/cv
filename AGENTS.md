# Chris Tham's CV — Astro CV and portfolio site

This repository generates a professional CV — two print-ready PDFs and a browsable site — from a single set of Markdown files, built with **Astro** and **UnoCSS**. The CV is the deliverable; the portfolio site around it is where the detail the PDF had to omit lives.

`README.md` documents the project for a human setting it up. This file is for coding agents: what the project is, how it is put together, and — in the Traps section — the specific things that have cost real debugging time. `DESIGN.md` covers the visual system.

The same codebase is deployed twice, and **this brief lives in `cv` only.** The `spotlite` copy is the public template: it ships the site without the machinery for maintaining it, so it has no `AGENTS.md`, no `CLAUDE.md` and no `.claude/`. Everything below therefore describes `cv`. `CLAUDE.md` covers what the two repositories do not share and how a change reaches the other one.

## 🎯 What this project is

Two audiences at once, and the tension between them explains most design decisions:

- **A professional record.** Employers and recruiters read the work history, and two CV PDFs are generated from the same content. Career facts are a document of record — nothing in the pipeline may reword, summarise or infer one.
- **The upstream of a reusable template.** `hellotham/spotlite` is this same codebase published under MIT for anyone to fork, and it is produced from here by subtraction. So biography belongs in `src/content/` and the `src/*.json` files, never in the code — anything hard-coded into a component becomes a defect in the template.

Tone is professional but not corporate-bland. All prose is **Australian English**.

## 🛠 Tech Stack

- **Package Manager:** [pnpm](https://pnpm.io/) — pinned via `packageManager`; never npm or yarn
- **Framework:** [Astro](https://astro.build) 7, static output, `base: '/cv/'`, Content Layer API
- **Styling:** [UnoCSS](https://unocss.dev/) with Wind4, Typography, and Icons presets
- **Fonts:** Astro's `fonts` integration via the fontsource provider (Noto Sans / Serif / Sans Mono)
- **Type Safety:** [TypeScript](https://www.typescriptlang.org/), `astro/tsconfigs/strict`
- **Linting & Formatting:** [ESLint](https://eslint.org/) (flat config, `jsx-a11y` strict) and [Prettier](https://prettier.io/)
- **Testing:** [Vitest](https://vitest.dev/) with `jsdom` and `v8` coverage
- **Image Processing:** [Sharp](https://sharp.pixelplumbing.com/)
- **Lightbox:** [PhotoSwipe](https://photoswipe.com/) for click-to-zoom image galleries
- **Visualisations:** [D3.js](https://d3js.org/) for interactive data-driven components and [Mermaid](https://mermaid.js.org/) via `astro-mermaid` for diagrams
- **Maths:** Sätteri parses `$…$`; `src/utils/katex-mdast.ts` typesets it with KaTeX at build time
- **Search Indexing:** [Pagefind](https://pagefind.app/) for static full-site search
- **PDF Generation:** [Puppeteer](https://pptr.dev/) driving dedicated print-only routes

**Not Netlify.** Support was deliberately removed — do not reintroduce it.

## 🚀 Key Commands

| Command                  | Action                                                          |
| :----------------------- | :-------------------------------------------------------------- |
| `pnpm install`           | Install dependencies (postinstall fetches Chrome for Puppeteer) |
| `pnpm run dev`           | Start local development server (default: `localhost:4321`)      |
| `pnpm run build`         | Build production site **and** the Pagefind index                |
| `pnpm run pdf`           | Build, then regenerate both CV PDFs into `./public/`            |
| `pnpm run search:index`  | Run Pagefind indexing against `./dist/`                         |
| `pnpm run preview`       | Preview the production build locally                            |
| `pnpm run test`          | Run the Vitest test suite once                                  |
| `pnpm run test:watch`    | Run Vitest in watch mode                                        |
| `pnpm run test:coverage` | Run tests and generate a v8 coverage report                     |
| `pnpm run lint`          | Run both Prettier and ESLint checks with auto-fixes             |
| `pnpm astro check`       | Type and diagnostic check across `.astro` files                 |
| `pnpm run refresh`       | Upgrade Astro and all dependencies to latest versions           |

Note that `build` does **not** generate the PDFs — that is `pnpm run pdf`.

Before calling any change done: `pnpm lint && pnpm astro check && pnpm test && pnpm build`. If you touched content, `src/content/cv/profile.md` or `src/utils/cv.ts`, run `pnpm run pdf` as well — the PDFs are committed and go stale silently.

Prefer non-interactive commands. Watch-mode tools need `CI=true` or their single-run form.

## 📂 Project Structure

- `src/pages/`: Site routes. File-based routing.
- `src/components/`: Reusable Astro components (including D3 charts and modals).
- `src/layouts/`: Page structures. `layout.astro` is the shell every page passes through; the rest are per-section.
- `src/content/`: Source files for content collections.
- `src/assets/`: Dynamic assets processed by Astro (images).
- `public/`: Static assets served directly, copied verbatim into the build.
- `scripts/generate-pdf.js`: Renders the `/cv/` routes to PDF with Puppeteer.
- `src/content.config.ts`: Schemas and loaders for content collections.
- `src/utils/cv.ts`: Deterministic CV curation.
- `src/utils/timeline.ts`: Normalises work and education into timeline entries.
- `src/components/entitylogo.astro`: Shared company/institution mark across all six surfaces.
- `src/components/wordcloud.astro`: Animated tag cloud on `/work`.
- `src/components/search.astro`: Header search UI and client logic.
- `src/pages/api/search.json.ts`: Fallback search index endpoint.
- `tests/`: 27 Vitest files. Several assert against built output in `dist/`, so a broken build fails tests.

## 📝 Content Management

This project uses the **Astro Content Layer API**. Collections are `article`, `project`, `work`, `education`, `social`, `page`, `creation`, `passion`, all with strict Zod schemas in `src/content.config.ts`.

Navigation is **inferred from the `page` collection** (`order`, `shorttitle`), so adding a page is a Markdown file, not a route. There is no menu data file.

Structured non-Markdown data lives in `src/social.json`, `src/superpowers.json` and `src/config.json` (site identity). The CV's own copy is Markdown, not JSON: `src/content/cv/profile.md` holds contact details and the competency cut-offs in frontmatter, and the Profile, Career and Key Achievements prose in its body.

Fields worth understanding before you edit them:

- **`work.tags`** — feeds the `/work` word cloud, where a tag's size is _how many roles carry it_. That only works if the vocabulary is reused deliberately across entries; rewording per entry silently destroys the weighting.
- **`description`** on `work` and `education` — required, and load-bearing three times over: the list-page teaser, the detail page's meta description, **and the one-line form the CV prints**. It has to read as all three, and it has to fit one line of the one-pager — about 114 characters, past which the role costs 13.7mm instead of 9.3mm.
- **`image` / `logo` / `logoBackground`** — square mark, extended wordmark, and the tile colour that makes a mark read as a seamless circle. All optional; a missing `image` falls back to an initials monogram.
- **`work.priority`** and **`summary`** — CV curation only; the site always shows the full body. `priority` is 1, 2 or 3 and picks which hand-written form each document prints:

  | priority | full CV       | one-pager                |
  | :------- | :------------ | :----------------------- |
  | 1        | the body      | `summary`                |
  | 2        | `summary`     | `description`            |
  | 3        | `description` | role, employer and years |

  `summary` is required at 1 and 2 (a Zod refinement enforces it) and must be absent at 3. Note the diagonal: a summary is read on the **one-pager** at priority 1 but only in the **full CV** at priority 2 — so a priority 1 summary must be two short bullets, while a priority 2 summary can be as long as the role deserves. `education` has no priority and behaves exactly as priority 2, because every qualification is shown.

  **If the one-pager stops fitting, lower a role's priority. Never shorten a summary that is already the author's minimum, and never reintroduce truncation.**

### The CV pipeline

`src/utils/cv.ts` builds both documents from the same collections that drive the site, so there is one source of truth for every career fact. **Curation is deterministic and must stay that way**, and it never abridges: the `CV_DETAIL` table chooses between forms a person wrote, and no code path shortens text. An earlier version sliced bullet lists to fit, which is how a role came to end mid-list under a heading promising five more items. Editorial copy lives in `src/content/cv/profile.md` where a human can review it.

`scripts/generate-pdf.js` serves `dist` over a local HTTP server and drives Puppeteer. The one-pager measures itself and scales to fit exactly one page, **failing loudly** below 80% rather than spilling onto a second. The full CV re-renders denser if the last page would otherwise carry only a line or two. `public/cv-print.css` is deliberately outside the site's CSS pipeline and deliberately contains no `@media` blocks.

Both PDFs are committed, because `public/` is copied verbatim into the build and the site links to them.

## ⚠️ Traps

Each of these was a real debugging session. They are documented at their call sites too.

### The `.astro` cache lies to you

Adding a frontmatter field or editing `src/content.config.ts` will **not** appear in dev, and **restarting the dev server is not enough**:

```bash
rm -rf .astro
```

If components come back blank instead, Vite's cache is also stale and is never touched by clearing `.astro`:

```bash
rm -rf .astro node_modules/.vite
```

### `pnpm build`, never bare `astro build`

`astro build` wipes `dist/` without regenerating `dist/pagefind/`. Search then silently falls back to the JSON endpoint, with no error anywhere.

### UnoCSS resolves variants before shortcuts

A shortcut named `<variant>-<utility>` never fires — the variant wins, and your shortcut is dead code that produces no CSS and no error. `focus-ring` parsed as `focus:` + `ring` and emitted a 1px `currentColor` ring instead of the declared 2px accent focus-visible ring, on eleven elements. `hover-accent` parsed as `hover:` + a non-utility and emitted **nothing at all**.

Component shortcuts are therefore prefixed **`ui-`** (`ui-focus-ring`, `ui-hover-accent`), because `ui-` is not a variant. Renaming them back reintroduces the bug silently. After changing a shortcut, confirm it emitted:

```bash
grep -o "\.ui-focus-ring[^{]*{[^}]*}" dist/_astro/*.css
```

### Scoped `<style>` does not reach script-created DOM

Astro scopes styles by stamping an attribute onto elements **in the template**. Anything D3 creates at runtime never gets it, so scoped rules never match. Use `<style is:global>` with every selector anchored to a component-owned `id`.

### ClientRouter re-runs every inline script

View transitions swap the DOM on navigation, so `dataset.initialized` guards cannot see the previous element, and listeners on `document`/`window`, `requestAnimationFrame` loops and `IntersectionObserver`s **survive the swap** and keep writing into detached nodes.

Every component with an inline script must tear down:

```js
document.addEventListener('astro:before-swap', () => {
  teardown?.()
  teardown = null
})
```

Prefer an `AbortController` with `{ signal }` on each listener so one `abort()` drops the lot. `d3bubblechart.astro` is the reference implementation.

### The search fallback must match Pagefind's coverage

`src/pages/api/search.json.ts` must index **every** collection Pagefind picks up from rendered pages. When it drifted, four collections were unsearchable in dev while production worked perfectly — searching "swift" or "servicenow" returned nothing.

### Mermaid is themed entirely from CSS, in both schemes

Both palettes live in `src/styles/mermaid.css`. The `themeVariables` in `astro.config.mjs` still set the light colours at render time, and that duplication is deliberate.

Mermaid bakes colours into each SVG as it renders, so a diagram's appearance is decided by whatever config was in force during that particular render. `astro-mermaid` renders from two places — once when its module runs and again on `astro:after-swap` — and a client-side navigation fires both, so two passes race over the same diagrams. Lose that race and a diagram keeps Mermaid's stock palette until something re-renders it. That is why reloading appeared to "fix" a wrongly-themed diagram: a full page load only ever runs one pass.

Stating both themes in CSS takes appearance out of the render entirely. Dark rules carry an extra `.dark` class and so outrank their light counterparts.

What follows from that:

- **Everything needs `!important`.** Mermaid injects a `<style>` into each SVG scoped by the diagram's generated id, and an ID selector beats a class rule. That includes xychart and quadrant, which an earlier version of this note wrongly exempted — their text is styled from the same block, and the dark chart titles were unreadable until they were flagged.
- **Target the `<text>`, not the wrapping `<g>`.** xychart's `chart-title`, `bottom-axis` and `left-axis` classes sit on groups, while the fill sits on the text inside them. A rule on the group silently does nothing.
- **One rule needs a cascade layer.** Gantt paints `.vertText` as `fill: navy !important` from that id-scoped block, and no class selector can outrank an ID one however many classes it carries. `@layer mermaid-vert` wins because layer order reverses for important declarations, so a layered important beats an unlayered one outright.
- **Diagram geometry is pinned, not measured.** Gantt and xychart size themselves from the element they render into, and that measurement is only correct once layout has settled. Roughly one load in six produced a 300px canvas and a squashed chart with overlapping labels. `gantt.useWidth` and `xyChart.width` in `astro.config.mjs` remove the measurement; `useMaxWidth` stays on, so they still scale down to their column.
- **`pre.mermaid` inherits code-block styling.** Diagrams are authored as fenced code, so the typography preset gives the container a dark slate panel and pale text meant to sit on it. Correct for a code sample, wrong the moment the SVG replaces the source — on the light page it put a dark panel behind every diagram and read as the site having picked the wrong theme. `mermaid.css` resets background, colour and border on the container.
- **Gantt ignores its `themeVariables`.** `base` derives section and task colours through its own logic, so those charts are driven from CSS in both schemes.
- **Gantt used as a bar chart wants `todayMarker off`.** The psychometric charts on `/superpowers/` have no time axis, so Mermaid drew the marker at x ≈ 7,500,000. Clipped and invisible, but it makes a real overflow audit much harder to read.
- **Do not re-enable `autoTheme`** without also restoring the `data-theme` mirroring in `layout.astro` and `theme.astro`. It keys off an attribute this site no longer sets, can only swap between Mermaid's own built-in themes, and drives the swap by re-rendering.

The integration also double-initialises on load and can overwrite a diagram's stored source with its own rendered SVG, so `layout.astro` stamps `data-diagram` during parse to keep the first render deterministic.

### `html { overflow-x: hidden }` hides responsive breakage

The page never scrolls sideways, so nothing overflows _visibly_ — content is simply sliced off the right edge with no scrollbar and no other clue. Two real defects lived behind that: a 480px-wide wordmark in a 288px column on `/work/hellotham/`, cut off mid-word, and the SFIA table on `/superpowers/` losing its last column at 320px.

Neither is visible by looking at the page, and neither is a colour-scheme problem. Audit by comparing `documentElement.scrollWidth` against `clientWidth` at each breakpoint, and treat any difference as a defect even though the page looks fine. When something legitimately exceeds its column — a wide table, a code block, a diagram — give it its own `overflow-x: auto` box so the content stays reachable.

### Computed colours are `oklch()`; do not parse them by hand

`getComputedStyle().color` returns whatever colour space the value was authored in, and the UnoCSS theme is in `oklch`. Pulling three numbers out of the string with a regex and treating them as RGB produces confident nonsense: an audit written that way reported 222 contrast failures across the site, every one an artefact, and the real number was zero.

Resolve colours by painting them instead — assign to a canvas `fillStyle`, fill one pixel, read it back with `getImageData`. That returns real sRGB bytes for any colour the browser can render, including `color-mix()` and `oklab()`.

### A table cannot scroll without `display: block`

`overflow` does not apply to `display: table`, so a table wider than its column pushes the page instead of scrolling. Prose tables are handled in the global block in `layout.astro` with `display: block; width: max-content; max-width: 100%; overflow-x: auto` — the `max-content` restores the natural sizing that `block` would otherwise discard.

### Markdown runs on Sätteri, and its plugins are not remark/rehype

`markdown.processor` is Astro 7's default Rust processor, configured in `astro.config.mjs`. Its `mdastPlugins` / `hastPlugins` are Sätteri's own visitor interface (`defineMdastPlugin`), **not** unified plugins. A remark or rehype plugin passed there is accepted and silently never runs — no error, no output. That cost real time; see [bruits/satteri#180](https://github.com/bruits/satteri/issues/180).

Maths is the live example. `features.math` only _parses_ `$…$` into `math` / `inlineMath` nodes — nothing typesets them, so without a plugin the LaTeX reaches the page verbatim. `src/utils/katex-mdast.ts` renders them at the **mdast** phase, which is the only phase where they still exist as maths: after mdast→hast they are indistinguishable from a fenced block tagged `language-math`, which is why rehype-katex cannot be retrofitted.

If you need a unified plugin, `markdown.processor: unified({ remarkPlugins, rehypePlugins })` from `@astrojs/markdown-remark` still works, but it swaps the processor for the whole site.

### Syntax highlighting is prose, and its contrast is enforced

Astro's default `github-dark` renders comments at #6a737d on #24292e — 3.05:1, below the 4.5:1 that body text requires, and a code comment is a sentence. Nothing in the build complained, and it only surfaces on pages with substantial commented code, so it hid for a long time.

Code blocks now use the Rosely themes in `src/styles/shiki-rosely.ts`, one palette per colour scheme, wired through `shikiConfig.themes` with `defaultColor: 'light'` — Shiki inlines the light colours and emits the dark ones as `--shiki-dark` custom properties, which `src/styles/mermaid.css` swaps under `.dark`.

`tests/shiki-theme.test.ts` recomputes every token's ratio against its own background and fails below 4.5:1, so a palette tweak cannot quietly undo this. Note the two palettes are deliberately different hues, not one set relit: a foreground needs luminance below ~0.15 to clear 4.5:1 on the cream background and above ~0.27 on the near-black one, and nothing satisfies both.

### SVG has no intrinsic size without width/height

An SVG declaring only a `viewBox` collapses to 0×0 under `h-auto w-auto`. Always set a definite dimension on one axis and let the other follow — this is why `entitylogo.astro` passes only `height`.

The other half of that: with the height fixed and the width free, the width comes from the aspect ratio and can be anything. A 2000×400 wordmark at `h-24` wants 480px. Cap it against the container (`max-w-full`) before capping it at a fixed size, or it will run off a phone.

## 🎨 Styling Conventions

- **UnoCSS:** Use utility classes directly in `.astro` components.
- **Presets:** `presetWind4`, `presetIcons` (Iconify), and `presetTypography` are pre-configured.
- **Custom Config:** Theme, shortcuts, safelist and preflights in `uno.config.ts`.
- **Theme:** The **Rosely** palette (warm, low-contrast). See `DESIGN.md`.

## 🧑‍💻 Code Conventions

**Formatting is Prettier's job** (`prettier.config.cjs`): single quotes, **no semicolons**, no trailing commas, 100 columns, 2-space indent, and double quotes in CSS. Don't hand-format — run `pnpm lint`.

**Markdown prose is one line per paragraph.** `proseWrap: 'never'`, so a paragraph is a single long line that the editor soft-wraps. Do not hand-wrap prose at 100 columns: the wrap is invisible in the rendered page but very visible in a diff, where changing one word reflows the paragraph and buries the edit in a block of moved text. `pnpm lint` unwraps anything hand-wrapped, so writing it wrapped only produces churn. Hard line breaks (a trailing `\`) are preserved and still work; tables, code fences and frontmatter are untouched.

**Naming:** `UpperCamelCase` for types and interfaces, `lowerCamelCase` for variables and functions, `CONSTANT_CASE` for module-level constants. Kebab-case filenames.

**Language:** `const` by default, `let` only when reassigned, never `var`. Strict equality. Avoid `any` — prefer `unknown` or a real type. Avoid type assertions and non-null assertions; where one is unavoidable, justify it in a comment.

**Comments explain _why_.** The prevailing style is a short comment naming the failure the code prevents, not a restatement of what the line does. Match it — several traps above are documented at their call sites precisely so they don't recur.

**Simplicity and consistency win.** Follow existing patterns; prefer the simple solution; minimise coupling and dependencies.

## ♿ Accessibility

A requirement, not a polish pass. Target is **WCAG 2.2 Level AA**. In practice:

- Semantic landmarks and a logical heading hierarchy with no skipped levels.
- Every interactive element keyboard-operable, with a visible focus ring (`ui-focus-ring`).
- `prefers-reduced-motion` honoured by **JavaScript animation too** — the CSS preflight only tames CSS transitions; a `requestAnimationFrame` loop keeps running regardless.
- Anything that moves indefinitely needs a pause control (WCAG 2.2.2).
- Decorative images inside a labelled link take `alt=''`; don't repeat the link text.
- Hover-revealed content must be dismissible without moving the pointer (Escape).
- Contrast checked against the actual background, per theme — a token that passes on cream usually fails on near-black.
- Never use colour as the sole carrier of meaning.

## 🧪 Testing

Vitest, 27 files, `jsdom` environment. Tests cover collection contracts, routing, base-path handling, component behaviour, the search endpoint, the RSS route, the PDF script and the generated PDFs themselves.

Write the test first where you can, and add one whenever you fix a bug a test could have caught. Aim for >80% coverage on new code (`pnpm run test:coverage`).

## 🚢 Deployment

Deployed to **GitHub Pages** via `.github/workflows/deploy.yml` (`withastro/action`) on every push to `main`. Static output served from the `/cv/` base path.

**The repository is public.** Anything committed is published, including git history — do not commit personal data.

## 🔎 Search Behaviour

- Production and preview search is powered by Pagefind, generated during `pnpm run build`.
- Where Pagefind assets are absent, search falls back to `/api/search.json`.
- `src/pages/cv/*` are print-only routes: `noindex`, and excluded from both the sitemap and the search index.
