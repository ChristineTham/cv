---
name: sync-both
description: Backport a finished change from cv to spotlite, verify both, then commit, push and confirm both deploys. Use whenever a change is complete in cv and needs to reach spotlite, and when a change was made in spotlite by mistake and has to be brought back the other way.
disable-model-invocation: true
---

# Backport from cv to spotlite

`ChristineTham/cv` and `hellotham/spotlite` are the same site deployed twice, from repositories
with **no shared history and no merge path**. A change that lands in one and not the other
diverges silently and stays diverged.

|                 | path                               | `site`                  | `base`       |
| :-------------- | :--------------------------------- | :---------------------- | :----------- |
| **cv**, primary | `~/Repositories/Websites/cv`       | `https://christham.net` | `/cv/`       |
| spotlite        | `~/Repositories/Websites/spotlite` | `https://hellotham.com` | `/spotlite/` |

Work in `cv` and backport to `spotlite`. The backport is a **subtraction**: the same prose and
the same assets, minus the personal archive and the download links that point at it.

## 1. Establish what changed

```bash
git -C ~/Repositories/Websites/cv status --short
git -C ~/Repositories/Websites/spotlite status --short
```

If the change is in `spotlite` instead, something went the wrong way round. Bring it back to `cv`
first, confirm it is right there, and then come back to step 2 — do not carry on in the wrong
direction just because the edit already exists.

## 2. Copy, then rewrite the base path — anchored

Copy each changed file, then rewrite **anchored on the link opener**:

```bash
sed -i '' 's#](/cv/#](/spotlite/#g' <file>      # cv -> spotlite, the usual direction
sed -i '' 's#](/spotlite/#](/cv/#g' <file>      # spotlite -> cv, recovering a stray change
```

A blanket `s#/spotlite/#/cv/#g` is wrong. `spotlite` is also an article slug, so it turns
`/spotlite/article/spotlite/` into `/cv/article/cv/` and breaks the link. Anchoring on `](`
rewrites only the start of a URL.

**Never copy `astro.config.mjs` wholesale.** It differs in `site` and `base`, and the two
repositories word some comments differently. Port the specific lines by hand. The same
caution applies to any root config you did not write in this change.

## 3. Drop what spotlite must not carry

`spotlite` is a public template: it ships the site, and nothing else. So the backported copy
loses:

- **the archive** — anything matching `public/*.zip`, `*.pdf`, `*.DOC`, `*.PPT`, `*.DOT`. The
  manuscripts, decks and scans live in `cv/public/` only;
- **the download links that point at them.** The standalone `**[Download …]**` lines go; where a
  link sat inside a sentence, the sentence keeps its words and loses the link;
- **the tooling** — `.claude/`, `AGENTS.md` and `CLAUDE.md`. These never cross. If a step of this
  backport is copying one of them, the step is wrong: edit the `cv` copy and stop. A template
  shipping them would hand every forker a hook that refuses their files and a skill that syncs to
  a repository they do not own.

`.claude/hooks/check-sibling-repo.py` blocks both the archive and the tooling when written under
`spotlite/`, so this is enforced rather than remembered. It also knows which articles are expected
to differ.

That enforcement has one hole worth knowing: the hook only runs in a session rooted at a
repository that has it, and `spotlite` does not. Work started there is unguarded.

## 4. Verify they now match

```bash
diff <(sed 's#/cv/#/BASE/#g' cv/<file>) <(sed 's#/spotlite/#/BASE/#g' spotlite/<file>)
```

Read the hunks before believing them. Both base strings are also real paths — `cv` is a page
route, `spotlite` an article slug — so normalisation produces false positives, and any file
naming both bases deliberately looks badly drifted when it is fine.

Normalising both sides is what makes this meaningful — a raw diff always differs on the base
path alone. Expect one legitimate exception: a link to the `spotlite` article normalises
asymmetrically (`/BASE/article/BASE/` against `/BASE/article/spotlite/`) and is correct.

## 5. Check both, separately

In each repository:

```bash
pnpm lint && pnpm astro check && pnpm test && pnpm build
```

`pnpm lint` **writes** — it is `prettier --write .` then `eslint --fix .`. If the change
added vendored or generated files, they must be in `.prettierignore` and the eslint `ignores`
_before_ this runs.

If content, `src/cv.json` or `src/utils/cv.ts` changed, also run `pnpm run pdf` in both — the
PDFs are committed and go stale silently.

## 6. Commit and push, one repository per command

Use `git -C` rather than `cd`. A `cd` earlier in a compound command persists, so a push written
as if it targeted one repository can land in the other twice — which has happened here more than
once. Primary first:

```bash
git -C ~/Repositories/Websites/cv add -A && git -C ~/Repositories/Websites/cv commit -F - <<'EOF'
...
EOF
git -C ~/Repositories/Websites/cv push origin main
```

Then the same for spotlite, as a **separate** command. Confirm with:

```bash
git -C ~/Repositories/Websites/cv log origin/main..HEAD --oneline
git -C ~/Repositories/Websites/spotlite log origin/main..HEAD --oneline
```

Both must be empty.

## 7. Confirm both deploys carry the right commit

```bash
gh run list --limit 1 --json status,conclusion,headSha
```

Per repository, waiting until `status` is `completed` **and** `headSha` matches that
repository's HEAD. A green run against the previous commit means nothing.

## Report

State both SHAs, both deploy results, and anything deliberately left unsynced with the reason.
