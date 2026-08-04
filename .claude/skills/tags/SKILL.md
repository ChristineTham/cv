---
name: tags
description: Add, merge, rename or review a tag. Use whenever new content needs tagging, whenever a tag is missing from the canonical list and the build refuses it, whenever two tags look like the same subject written twice, and whenever asked to review or tidy the vocabulary. Also use before inventing a tag — the list is closed and there is usually already a word for it.
---

# The tag vocabulary

One vocabulary across five collections — `article`, `work`, `project`, `education`, `creation` — declared in `src/utils/tags.ts` as `TAG_GROUPS` and **enforced by the build**. `src/content.config.ts` validates every collection's `tags` against a Zod enum built from it, so a tag that is not on the list fails the build naming the file and listing every valid option.

Each distinct tag publishes a page at `/tag/<slug>/` showing everything carrying it, and `/tags/` lists the whole vocabulary grouped. Categories are a separate, article-only axis in `src/utils/articles.ts` — do not confuse them.

## Why it is closed

Because the failure is silent otherwise. A reworded synonym does not degrade gracefully: it publishes a second page, and each page then claims to be the whole of a subject that has been cut in half. Before the list was closed, "IT strategy" and "Technology strategy" had drifted apart across two roles at the same bank, and "Data analytics" and "Data science" across two consulting engagements. Neither produced an error. Both looked fine on every page they appeared on.

The enum is what makes a rename impossible to do halfway. Change the list without the content, or the content without the list, and the build stops.

## Review it

```bash
python3 .claude/skills/tags/scripts/review.py
```

Reports four things. Read them in this order:

- **Orphans** — declared but on nothing. Either the word arrived before the entry, or the last entry carrying it was retagged. Remove it, or use it.
- **Near-misses** — pairs close enough to be one subject written twice. This is the one thing the closed list cannot catch by itself: both halves are valid canonical tags, and that is exactly the problem. **Most flagged pairs are legitimate** — `Music` and `Chamber music` are a genus and a species, `DVD` and `DVD player` are a disc and a machine. Judge each; the script is a prompt, not a verdict.
- **Singletons** — on exactly one entry. Fine in bulk: a specific employer, a specific genre. A long tail that grew in one sitting usually means someone was inventing rather than reusing.
- **Islands** — professional subjects confined to one collection. A genre or an employer belongs to one collection and that is fine. A capability that appears in the writing and never in the work, or the reverse, is the drift this system exists to stop. `Architecture practice` on articles alone beside `Architecture governance` on roles alone is the shape to look for — the string matcher cannot see that one.

The script parses `TAG_GROUPS` out of the TypeScript directly, so it needs no build and cannot disagree with what ships.

## Tag new content

1. **Read the entry.** Every tag must be readable off the entry's own text. Do not tag a role with a subject because it sounds plausible for that employer.
2. **Look for the existing word first** — `/tags/` grouped, or the review script's output. The list is 150-odd words and already covers most of what new content is about.
3. Reuse it exactly, including case. `macOS`, `iOS`, `UNIX` and `SACD` are spelled the way the vocabulary spells them.
4. Only if there is genuinely no word for it, add one.

Where an entry mirrors another — `project/adventure` and `article/adventure` are the same thing seen twice — give it the same tags.

## Add a tag

Put it in the group it belongs to in `TAG_GROUPS`, alphabetically within that group. The groups have no behaviour beyond ordering `/tags/`; moving a tag between them changes nothing else. They exist because **near-synonyms are invisible in an alphabetical list of 152 strings and obvious when they sit three lines apart under one heading** — so read the group before adding to it.

Then add it to the entry. Both edits, or the build fails — which is the point.

## Merge two tags

A merge is a content edit and a list edit, and the build enforces that you do both.

1. Decide which name survives. Prefer the one already on more entries, and the one that reads as a subject rather than an artefact — `Risk management` over `Risk analysis`.
2. Rewrite every entry carrying the loser. **Scope the edit to the `tags:` value in frontmatter.** Words like "Security", "Banking" and "Thriller" run all through the body prose, and a substitution over the whole file will quietly corrupt an article while reporting success. `scripts/review.py` contains a `read_tags` that handles all three YAML shapes in use here; reuse its `tag_region` rather than writing a fourth parser.
3. Deduplicate — an entry may already carry both, and a naive merge leaves it carrying the survivor twice.
4. Remove the loser from `TAG_GROUPS`.
5. Rebuild. The old page disappears; check nothing linked to it by slug.

## Rename a tag

The same as a merge, minus the deduplication, plus one thing: the slug changes, so the page moves. `/tag/<slug>/` is derived from the name by `tagSlug`, and nothing redirects. If the old URL has been live long enough to be worth keeping, say so rather than assuming.

## Two traps

**Slugs must stay unique across the whole vocabulary, not within a group.** `tagIndex` throws naming both offenders, because two pages competing for one URL would resolve by route ordering rather than by intent. `Design systems` and `Design Systems` collide; so would `Client/server` and `Client server`.

**A merge can move an entry's tag count to zero for its collection.** Check the tag page still has the sections you expect afterwards — a tag that loses its last article stops showing a Writing section, and its back link changes to whichever side it still has.

## Before finishing

```bash
pnpm lint && pnpm astro check && pnpm test && pnpm build
```

Tagging touches `src/content/`, so **run `pnpm run pdf` as well** — the CV PDFs are committed and go stale silently. Then `/sync-both`: everything here is content and code, which crosses to `spotlite`, while this skill and the rest of `.claude/` never does.
