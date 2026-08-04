#!/usr/bin/env python3
"""
Review the tag vocabulary against what the content actually uses.

Reports four things, in the order they matter:

  ORPHANS      declared in CANONICAL_TAGS but on nothing. Either the word arrived before
               the entry, or the last entry carrying it was retagged and nobody noticed.
  NEAR-MISSES  pairs close enough to be the same subject written twice. This is the one
               the closed list cannot catch by itself: "Data analytics" and "Data science"
               are both valid canonical tags, and both wrong, because only one should be.
  SINGLETONS   on exactly one entry. Legitimate in bulk — a specific album, a specific
               employer — but a long tail growing in one sitting usually means the writer
               was inventing rather than reusing.
  ISLANDS      used by exactly one collection. Fine for a genre or an employer; worth a
               look for anything professional, because a subject that ought to connect
               writing to work and does not is the drift this whole system exists to stop.

Run from the repository root:  python3 .claude/skills/tags/scripts/review.py
"""

from __future__ import annotations

import difflib
import pathlib
import re
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[4]
COLLECTIONS = ('article', 'work', 'project', 'education', 'creation')

FRONTMATTER = re.compile(r'\A---\n(.*?)\n---\n', re.S)
QUOTED = re.compile(r"'((?:[^']|'')*)'|\"([^\"]*)\"")


def tag_region(fm: str):
    """Offsets of the value of the top-level `tags:` key, across all three YAML shapes."""
    m = re.search(r'^tags:[ \t]*(.*)$', fm, re.M)
    if not m:
        return None
    if m.group(1).strip():
        if not m.group(1).strip().startswith('['):
            return (m.start(1), m.end(1))
        depth, i = 0, m.start(1)
        while i < len(fm):
            if fm[i] == '[':
                depth += 1
            elif fm[i] == ']':
                depth -= 1
                if depth == 0:
                    return (m.start(1), i + 1)
            i += 1
        raise ValueError('unbalanced flow sequence in tags')
    start = i = m.end() + 1
    for line in fm[start:].split('\n'):
        if line.strip() and not line[0].isspace():
            break
        i += len(line) + 1
    return (start, min(i, len(fm)))


def read_tags(path: pathlib.Path) -> list[str]:
    m = FRONTMATTER.match(path.read_text(encoding='utf-8'))
    if not m:
        return []
    region = tag_region(m.group(1))
    if region is None:
        return []
    lo, hi = region
    return [q.group(1) or q.group(2) for q in QUOTED.finditer(m.group(1)[lo:hi])]


def canonical() -> dict[str, list[str]]:
    """Parse TAG_GROUPS out of src/utils/tags.ts without needing a TypeScript runtime."""
    text = (ROOT / 'src/utils/tags.ts').read_text(encoding='utf-8')
    body = text[text.index('export const TAG_GROUPS = {') :]
    body = body[: body.index('\n} as const')]
    groups: dict[str, list[str]] = {}
    current = None
    for line in body.split('\n'):
        head = re.match(r"\s*'([^']+)':\s*\[", line)
        if head:
            current = head.group(1)
            groups[current] = []
            line = line[head.end() :]
        if current is not None:
            groups[current] += [q.group(1) or q.group(2) for q in QUOTED.finditer(line)]
    return groups


NORMALISE = re.compile(r'[^a-z0-9]+')


def key(tag: str) -> str:
    """Compare on letters alone, so casing, punctuation and spacing stop hiding a twin."""
    return NORMALISE.sub('', tag.lower())


STEM = (
    ('ies', 'y'),
    ('es', ''),
    ('s', ''),
    ('ing', ''),
)


def stem(word: str) -> str:
    for suffix, replacement in STEM:
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)] + replacement
    return word


def main() -> int:
    groups = canonical()
    declared = [t for g in groups.values() for t in g]
    group_of = {t: name for name, tags in groups.items() for t in tags}

    used: dict[str, set[str]] = defaultdict(set)  # tag -> collections carrying it
    counts: dict[str, int] = defaultdict(int)
    unknown: list[tuple[str, str]] = []

    for collection in COLLECTIONS:
        base = ROOT / 'src/content' / collection
        for path in sorted(base.rglob('*.md')):
            for tag in set(read_tags(path)):
                counts[tag] += 1
                used[tag].add(collection)
                if tag not in group_of:
                    unknown.append((str(path.relative_to(ROOT)), tag))

    print(f'{len(declared)} declared, {len(counts)} in use, '
          f'{sum(counts.values())} assignments across {len(COLLECTIONS)} collections\n')

    if unknown:
        # The build enforces this, so reaching here means the list and the content were
        # edited apart — report it first, because nothing else will build until it is fixed.
        print('NOT IN THE CANONICAL LIST — the build will refuse these')
        for path, tag in unknown:
            print(f'   {tag!r} in {path}')
        print()

    orphans = [t for t in declared if t not in counts]
    print(f'ORPHANS ({len(orphans)}) — declared, carried by nothing')
    for tag in orphans:
        print(f'   {tag}  [{group_of[tag]}]')
    if not orphans:
        print('   none')
    print()

    print('NEAR-MISSES — same subject, possibly written twice')
    seen: set[tuple[str, str]] = set()
    hits = 0
    for i, a in enumerate(declared):
        for b in declared[i + 1 :]:
            ka, kb = key(a), key(b)
            ratio = difflib.SequenceMatcher(None, ka, kb).ratio()
            words_a = {stem(w) for w in re.split(r'[^a-z0-9]+', a.lower()) if w}
            words_b = {stem(w) for w in re.split(r'[^a-z0-9]+', b.lower()) if w}
            shared = words_a & words_b
            # Either the strings are nearly identical, or one is the other plus a
            # qualifier — "Banking" and "Retail banking" were exactly that.
            close = ratio >= 0.82 or (shared and (words_a <= words_b or words_b <= words_a))
            if close and (a, b) not in seen:
                seen.add((a, b))
                hits += 1
                same = ' SAME GROUP' if group_of[a] == group_of[b] else ''
                print(f'   {a} ({counts.get(a, 0)}) ~ {b} ({counts.get(b, 0)}){same}')
    if not hits:
        print('   none')
    print()

    singles = sorted(t for t in counts if counts[t] == 1)
    print(f'SINGLETONS ({len(singles)} of {len(counts)}) — on exactly one entry')
    print('  ', ', '.join(singles) if singles else 'none')
    print()

    professional = {'Architecture and strategy', 'Software and computing', 'Finance', 'Working life'}
    islands = sorted(
        t for t in counts if len(used[t]) == 1 and group_of.get(t) in professional and counts[t] > 1
    )
    print(f'ISLANDS ({len(islands)}) — professional subjects confined to one collection')
    for tag in islands:
        print(f'   {tag} ({counts[tag]}) only in {next(iter(used[tag]))}  [{group_of[tag]}]')
    if not islands:
        print('   none')

    return 1 if unknown else 0


if __name__ == '__main__':
    sys.exit(main())
