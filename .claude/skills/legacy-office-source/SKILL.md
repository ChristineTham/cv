---
name: legacy-office-source
description: Read a legacy Word .DOC or PowerPoint .PPT and turn it into a new article, or use it to correct and enrich one already published, converting its figures to SVG. Use this whenever a .DOC, .PPT, .DOT or an old Office file appears in a request, whenever a paper's Word manuscript or its conference slide deck turns up, and whenever an existing reproduction's figures are scans or GIFs that a vector original could replace. Reach for it even when the request sounds like plain "add this paper" or "convert these figures" — the manuscript is almost always a better source than any HTML export made from it, and it usually proves something about that export.
---

# Working from a Word manuscript or a PowerPoint deck

A `.DOC` manuscript and its `.PPT` deck are better sources than the HTML that was exported from
them years later. They predate the export, they carry figures as vector objects rather than
480-pixel GIFs, and comparing one against its export routinely turns up something the export
lost.

This skill covers getting text and figures out of those binaries. It says nothing about how the
resulting article should be shaped — if the project has its own convention for reproductions
(this one does: see `reproduce-document`), follow that for frontmatter, preface, repairs and
provenance links.

Paths below are written against three things worth settling up front:

```bash
SKILL=path/to/this/skill          # holds scripts/ and references/
SRC=path/to/the/originals         # wherever the .DOC and .PPT live

# LibreOffice does the format reading. It is rarely on PATH when installed as a Mac app.
SOFFICE=$(command -v soffice libreoffice 2>/dev/null | head -1)
[ -n "$SOFFICE" ] || SOFFICE=/Applications/LibreOffice.app/Contents/MacOS/soffice
```

## First work out what you are holding

Spend a few minutes here. It changes everything downstream, and the cheapest mistake to make is
publishing a second copy of something the project already has.

```bash
file "$SRC/paper.DOC" "$SRC/paper.PPT"
```

`file` reports the OLE summary stream for PowerPoint, which is unusually informative: title,
subject, author, revision count, creation and last-saved dates, slide count. Those dates settle
questions the prose cannot — a deck last saved days before one conference and revised for another
establishes which version came first.

Then ask whether this is the source of something already published. Search the project's article
or content directory for the title. If it is, the job is probably **not** a new article. It is
more likely to be:

- correcting the published one where the export lost or mangled something, and
- replacing its figures with vector versions.

Say so plainly rather than producing a near-duplicate. When two published versions of the same
paper genuinely exist — a conference version and a revision for a different audience — prefer
publishing both, cross-linked, marking where they diverge, over silently consolidating them.

## Extracting the text

On macOS, `textutil` handles Word formats back to WinWord 2.0. LibreOffice does the same job on
any platform and is worth reaching for when `textutil` is absent or produces nothing useful:

```bash
textutil -convert txt -output out.txt "$SRC/paper.DOC"
"$SOFFICE" --headless --convert-to txt --outdir out/ "$SRC/paper.DOC"    # portable alternative
```

Either way the result is a binary preamble, then the prose, then binary again. Find the title to
locate the start, and a known closing phrase to locate the end.

**Word field codes survive the conversion, and they are evidence rather than noise.** Read them
before stripping them:

| Field                    | What it tells you                                                                                                                                                       |
| :----------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AUTONUM` / `AUTONUMLGL` | Headings carry **no literal numbers**. Any numbers in a derived HTML were introduced by that conversion, so wrong ones there are conversion faults, not the author's.   |
| `EMBED MSPowerPoint`     | This figure is an embedded PowerPoint object, so a vector copy exists — see below. A figure without this marker is a pasted picture and may have no vector form at all. |
| `SYMBOL 183 \f "Symbol"` | A bullet character. Strip these or every list item gains a nonsense word.                                                                                               |
| `METAFILEPICT`           | The OLE clipboard format name that precedes a cached metafile. Counting these tells you how many embedded objects to expect.                                            |

Word also justifies with discretionary hyphens, so extracted text is full of `pro cessing`,
`dis tributed`, `com ple xi ty`. Do not try to repair these by rule; handle them in the
comparison instead.

### Never finish a truncated line from inference

Dumps get written with a per-line cap — `[:150]`, `head -c`, a column limit in a table — to keep
the survey readable. That is fine for surveying. It is **not** fine as the text you then quote
from, and the failure is silent: a sentence cut at 150 characters still reads as a whole sentence,
so the temptation is to complete it from context and move on.

Two quotations in one article were invented exactly this way. A slide reading "ensuring programs
implement agreed solutions" was cut at "…implement" and published as "implement them". Another
reading "as well as Technology budget" was cut at "as well as T" and published as "Technology
Strategy" — which also changed the claim, from an operating budget to a strategy programme.

So: **survey with a cap, quote from an uncapped re-extraction.** If a dump was truncated, do not
repair it, regenerate it. And treat any sentence that ends suspiciously near the cap as unread.

## Comparing the manuscript against an existing export

This is where the value is. Squash **both** sides to lowercase alphanumerics with **no spaces at
all**, then diff as a character stream:

```python
sq = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
sm = difflib.SequenceMatcher(None, sq(doc), sq(html), autojunk=False)
```

Removing spaces entirely is what makes this work: every soft-hyphen split collapses, and so does
every difference in line wrapping and tag placement. Word-level diffing on one such pair reported
94 differing regions, of which one was real. The character stream reported three, of which one
was real: the HTML export had dropped a word from a list.

Strip HTML with a **known tag list**, never `<[^>]+>` — a wildcard eats everything between a real
`a<b` and a later `a>b`. Decode entities _after_ stripping, or a decoded `&lt;` becomes a tag
opener for the strip to eat.

Anything the comparison turns up belongs in the article's preface, especially when it corrects
something that preface previously claimed.

## Figures: two routes, and they are not equivalent

### Route A — metafiles cached in the .DOC (prefer this for a paper's figures)

Word stored a Windows Metafile rendering of every embedded OLE object so it could draw the figure
without launching the application that owned it. Those caches are vector, and they are _the
figure as the paper printed it_.

```bash
python3 "$SKILL/scripts/extract_wmf.py" "$SRC/paper.DOC" -o wmf/
python3 "$SKILL/scripts/wmf2svg.py" wmf/paper-00.wmf "alt text" > figure-1.svg
```

`extract_wmf.py` scans for the metafile header, validates the declared length and the terminating
EOF record, deduplicates, and writes each one out. Caches normally appear twice — Word keeps a
copy in the object stream and another inline — and the tool reports which are doubled, which is a
useful signal that a picture really is an embedded object.

`wmf2svg.py` walks the GDI records. It has been tested against real papers, but the format has
sharp edges that produce plausible, silently wrong pictures. If a converted figure looks _nearly_
right, read `references/wmf-traps.md` before assuming the source is at fault.

### Route B — LibreOffice, from the .PPT

Modern PowerPoint **cannot open PowerPoint 4.0** and fails quietly: an AppleScript `open` returns
with zero presentations rather than an error. LibreOffice can, because it bundles libmwaw, which
covers PowerPoint Mac v1–v4 and Windows v2–v4 and 95.

```bash
"$SOFFICE" --headless --norestore -env:UserInstallation=file:///tmp/loprofile \
  --convert-to svg --outdir out/ "$SRC/deck.PPT"
```

The `-env:UserInstallation` flag matters: it keeps the conversion out of any running LibreOffice
profile, so this works even with the application open.

That yields **one SVG holding every slide**, with a script for navigation. List the slides, then
pull one out:

```bash
node "$SKILL/scripts/slide2svg.mjs" out/deck.svg --list
node "$SKILL/scripts/slide2svg.mjs" out/deck.svg id24 figure-4.svg \
  --drop "slide title,first words of each bullet" --rotate "Security,Management"
```

It extracts the slide, un-hides its ancestors, crops to content, and strips the other slides'
definitions — worth doing on its own, since that step took one figure from 252 KB to 25 KB. The
script needs `puppeteer` resolvable, so run it from a directory where that is installed, or point
`NODE_PATH` at one.

**libmwaw's import loses things.** Two seen so far, both confirmed by exporting PDF as well and
finding the same loss, which locates the fault in the import rather than the SVG writer:

- **Text rotation is dropped.** Vertical labels arrive lying flat across the middle of a diagram.
  `--rotate` puts named labels back upright.
- **Text is re-wrapped to LibreOffice's metrics**, sometimes breaking a word mid-way. The wrap is
  baked into two positioned tspans, so it needs the text element rebuilt by hand.

Name both repairs in the preface. Whatever raster you are replacing is the authority for layout,
even when it is the thing being superseded.

## Which source is right

The same diagram can exist in three forms, and they are not interchangeable:

| Source                              | What it is                                                     |
| :---------------------------------- | :------------------------------------------------------------- |
| The slide in the `.PPT`             | The **talk**. Usually in the presentation template's colours.  |
| The object embedded in the `.DOC`   | The **paper as submitted**, often recoloured for print.        |
| A contemporaneous GIF or PNG export | A **later revision** again, sometimes recoloured a third time. |

For an article reproducing a paper, the embedded object wins. Reach for the slide only when the
figure is not an embedded object and has no cache — and say in the preface that it came from the
deck. Where colours differ between sources, that difference is itself worth a sentence.

## Verify the finished article against the source

Do this **after the article is written**, not only while extracting. It is a different check from
the one above: that one compares the source against an existing export, this one compares the
source against the thing you just produced. Run it before calling the work done, every time.

Compare **paragraph by paragraph**, not as one character stream. A stream diff punishes reordering
— and reordering is exactly what happens when a slide's shapes are read in z-order but rewritten
into a table, so it reports 30% loss on a section that lost nothing. Ask instead: does each source
paragraph appear _somewhere_ in the output?

```python
sq = lambda s: re.sub(r'[^a-z0-9]', '', html.unescape(s).lower())
haystack = sq(article_markdown)
missing = [p for p in source_paragraphs
           if len(sq(p)) >= 4 and sq(p) not in haystack and not in_any_figure(sq(p))]
```

Three things that make the difference between a check that works and one that lies:

- **Search the figures too.** Text that moved into an SVG has not been lost. Read every `<tspan>`
  in each referenced figure and search that as well, or every diagram will read as a total loss.
- **`html.unescape` before squashing.** SVG stores `&` as `&amp;`, so squashing raw markup injects
  `amp` into the middle of every label and "Finance & Corporate" stops matching itself. Eight
  phantom losses in one run came from this alone.
- **Expect to triage.** A check tuned quiet enough not to need triage is tuned quiet enough to
  miss a handful of wrong characters at the end of a long paragraph, which is precisely where
  invented text hides. Noise is the price; pay it.

Every surviving difference then goes in the preface, named. "556 of the source's 557 paragraphs
appear verbatim, and here is the one that does not" is a much stronger claim than silence.

### A text-only check scores a dropped diagram as perfect

The check above counts paragraphs, and a drawing has none — so a slide reproduced as a table can
lose its entire picture and still verify at 100%. One slide's three text streams were faithfully
tabulated while the whole architecture diagram beside them vanished, and nothing complained.

Text fidelity and figure fidelity are separate questions. For the second, **render every figure and
look at it.** Two cheap signals catch most of it before you spend attention:

- **Byte size.** A 247 KB SVG that renders to a 1.4 KB PNG is blank. That is how one figure whose
  viewBox had been blown out to 4,000× the slide canvas was caught.
- **viewBox against the slide canvas.** PowerPoint 4:3 is 25400 × 19050 in 1/100 mm. Anything wildly
  wider is off-canvas junk pulled in by crop-to-content; anything much smaller is a crop that ate
  the drawing.

And when deciding whether a slide is "mostly text", decide it from the **render**, not from the
extracted strings. A slide can be a bullet list that reads like a diagram, or a diagram whose text
reads like a list. Only looking tells you which.

## Finishing

- Add the originals to wherever the project serves downloads, **each file on its own — do not bundle
  them into a ZIP**, and quote each real size in the link text rather than guessing. A zip hides what
  is in it, needs unpacking before anyone can look, and duplicates bytes that are already there. In
  this project that is `cv/public/` and never `spotlite/public/`; the originals are personal
  documents and `spotlite` is a public template.
- **Do not archive HTML exports derived from the originals.** They are worth extracting and
  comparing against — that comparison is the most valuable thing in this skill — but the finding
  belongs in the preface, not the export in `public/`. The manuscript is the source of record.
- Work in `cv` first, then backport to `spotlite`. Figures and article prose go to both; the
  archive and the download links pointing at it stay in `cv`. `sync-both` covers the mechanics.
- Check the built page for overflow and contrast. **Point any audit at the right host and base
  path** — auditing one site's URLs against another's preview measures 404 pages, which pass every
  check while proving nothing.
- **Run the verification above and quote its result.** Not "the article is faithful" but "n of the
  source's m paragraphs appear verbatim, and the exceptions are these". If you cannot say the
  number, the check has not been run.

## Reference

- `references/wmf-traps.md` — the GDI record traps that produce plausible-but-wrong pictures, and
  the LibreOffice SVG structure notes. Read it whenever a converted figure is close but not right.
