#!/usr/bin/env python3
"""Warn when a file edited here has drifted from its twin in the sibling repository.

cv and spotlite are the same site deployed twice, from repositories with no shared history and
no merge path, so nothing but memory keeps them together. cv is the primary: work there and
backport to spotlite, which is the same site minus the personal archive and minus this tooling.
This compares the file just written against its counterpart, normalising the base path first —
a raw diff would flag every file, every time, on `/cv/` versus `/spotlite/` alone.

The hook fires whichever way an edit goes, because catching a stray spotlite-first change is
exactly when it earns its keep. Note that it can only fire in a session rooted at a repository
that has it, and spotlite no longer does — so a session started there is unguarded. That is the
cost of a clean template, and the reason to start every session in cv.
"""

import json
import re
import sys
from fnmatch import fnmatch
from pathlib import Path

PAIR = {'spotlite': 'cv', 'cv': 'spotlite'}
BASE = {'spotlite': '/spotlite/', 'cv': '/cv/'}
# Only content and source travel between the repos. Build output and local notes do not.
# DESIGN.md is watched because it is now the one root document shared by both, and so the one
# that can drift unnoticed. tests/ is watched because two of its comments sat asserting cv's base
# was '/spotlite/' -- invisible to the twin diff, since that normalises to what spotlite's correct
# copy normalises to, and only foreign_base can see it. README.md is deliberately not watched: it
# is a different document in each repo, the full project README in cv and the template's front
# page in spotlite.
WATCHED = ('src/', 'public/', 'scripts/', 'tests/', 'DESIGN.md')
SKIP = ('dist/', 'node_modules/', '.astro/', 'coverage/')

# Two quite different things live in cv and never in spotlite.
#
# The archive: original historical documents -- manuscripts, decks, scans and the
# contemporaneous HTML exports. cv is a personal CV; spotlite is a public template and has no
# business shipping a personal archive.
#
# Matched against a lowercased path, because these arrive in whatever case the 1990s gave them
# and fnmatch is case-SENSITIVE on macOS (os.path.normcase is identity on POSIX). An earlier
# version listed `public/*.PPT` alone and so did not recognise `Banktech06 NAB Chris Tham
# SOA.ppt` as archive material at all -- which was worse than a plain miss, because the file
# then fell through to the twin comparison and came back as "missing from spotlite", advising
# that a personal conference deck be copied into the public template.
CV_ONLY_ARCHIVE = ('public/*.zip', 'public/*.pdf', 'public/*.doc',
                   'public/*.ppt', 'public/*.dot')
# The tooling: this hook and its sibling, the skills, the agents, and the two briefs. They
# describe a two-repo workflow that only makes sense from the primary side, and much of what
# they say is about the personal archive spotlite does not carry. A template should ship the
# site, not the machinery for maintaining one particular copy of it.
CV_ONLY_TOOLING = ('.claude/*', 'AGENTS.md', 'CLAUDE.md')
# Belong in both, but the content is each repo's own identity rather than shared material: the
# manifest names and scopes the site, and the CV PDFs are rendered against it and embed absolute
# URLs. Require both to exist and compare no further.
KEEP_IN_BOTH = ('public/cv.pdf', 'public/cv-onepage.pdf', 'public/site.webmanifest')

# These carry the same prose in both repos but no download links in spotlite, because the
# documents they point at are not there. Differences are expected, so warn rather than block --
# which does mean an unrelated drift in one of them will not be caught here.
MAY_DIVERGE = (
    'src/content/article/auug-1993.md',
    'src/content/article/auug-1994.md',
    'src/content/article/openworld-1994.md',
    'src/content/article/crypt-usenix91.md',
    'src/content/article/suntech-1990.md',
    'src/content/article/banktech-2006.md',
    'src/content/article/btell-2003.md',
    'src/content/article/apc-2004.md',
    'src/content/article/ark-2005.md',
    'src/content/article/apc-2004-edit.md',
    'src/content/article/eac-2005.md',
    'src/content/page/education.md',
)


def cv_only(rel):
    """Return why this path belongs in cv alone, phrased to follow '<rel> is ...', or None."""
    if rel in KEEP_IN_BOTH:
        return None
    if any(fnmatch(rel.lower(), pat) for pat in CV_ONLY_ARCHIVE):
        return ('an original historical document, and those are kept in cv only — spotlite is a '
                'public template and does not ship a personal archive. Put it in cv/public/ '
                'instead, and give the spotlite copy of any article citing it no download link')
    if any(fnmatch(rel, pat) for pat in CV_ONLY_TOOLING):
        return ('agent tooling, and that is kept in cv only — spotlite is a public template and '
                'ships the site, not the machinery for maintaining it. Edit the cv copy; nothing '
                'here is backported')
    return None


# Normalising the base path makes the twin comparison possible, but it also makes this hook
# blind to a file using the WRONG base: cv saying `/spotlite/` normalises to exactly what
# spotlite saying `/spotlite/` normalises to, so the diff is clean and the error invisible. That
# is how cv's AGENTS.md sat claiming spotlite's base path without anything noticing. These two
# checks look at the raw text instead, and only at forms that are never legitimate.
#
# Both are deliberately narrow. `/spotlite/` appears innocently inside `/cv/article/spotlite/`
# because spotlite is also an article slug, and `.claude/` and CLAUDE.md document both repos on
# purpose, so a blanket search for the other repo's name would cry wolf constantly.
def foreign_base(rel, text, this_repo):
    """Return a complaint if the file uses the sibling's base path where it cannot be right."""
    if rel.startswith('.claude/') or rel == 'CLAUDE.md':
        return None                       # these files discuss both repos by design
    other = PAIR[this_repo]
    hits = []
    if f']({BASE[other]}' in text:
        hits.append(f'a link opening `]({BASE[other]}`')
    m = re.search(r"base:\s*'(/[a-z]+/)'", text)
    if m and m.group(1) != BASE[this_repo]:
        hits.append(f"a base declaration of `{m.group(1)}`")
    if not hits:
        return None
    return (f'{rel} contains {" and ".join(hits)}, which is {other}\'s base path, not '
            f'{this_repo}\'s. Normalising hides this from the twin comparison, so it has to be '
            f'checked directly. Use {BASE[this_repo]} here.')


def normalise(text):
    """Collapse each repo's own base path and host so only real differences remain.

    A file like robots.txt or site.webmanifest names the host as well as the base, so
    collapsing the base alone still flags it every time.
    """
    text = re.sub(r'/(?:spotlite|cv)/', '/BASE/', text)
    return re.sub(r'\b(?:hellotham\.com|christham\.net)\b', 'SITE', text)


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    path = (event.get('tool_input') or {}).get('file_path')
    if not path:
        return 0
    here = Path(path).resolve()

    parts = here.parts
    try:
        i = next(n for n, p in enumerate(parts) if p in PAIR)
    except StopIteration:
        return 0

    rel = str(Path(*parts[i + 1:]))
    if rel.startswith(SKIP):
        return 0

    this_repo, twin_repo = parts[i], PAIR[parts[i]]

    # Checked ahead of WATCHED, because the point of these is that they have no twin: comparing
    # them is not merely unnecessary, it would report every one of them as missing from spotlite.
    reason = cv_only(rel)
    if reason:
        if this_repo == 'spotlite':
            print(f'{rel} is {reason}.', file=sys.stderr)
            return 2
        # Nothing to compare against, but the raw-text base check still applies — and this is
        # the file set it exists for. AGENTS.md sat claiming spotlite's base path unnoticed.
        try:
            complaint = foreign_base(rel, here.read_text(), this_repo)
        except (UnicodeDecodeError, FileNotFoundError):
            return 0
        if complaint:
            print(complaint, file=sys.stderr)
            return 2
        return 0

    if not rel.startswith(WATCHED):
        return 0

    twin = Path(*parts[:i], PAIR[parts[i]], *parts[i + 1:])

    if not twin.exists():
        print(f'{rel} exists in {this_repo} but not in {twin_repo}.', file=sys.stderr)
        return 2

    if rel in KEEP_IN_BOTH:
        return 0

    try:
        a, b = here.read_text(), twin.read_text()
    except UnicodeDecodeError:
        # Binary: no base path to check or normalise, compare bytes and stop.
        if here.read_bytes() != twin.read_bytes():
            print(f'{rel} differs between {this_repo} and {twin_repo}.', file=sys.stderr)
            return 2
        return 0
    except FileNotFoundError:
        return 0

    complaint = foreign_base(rel, a, this_repo)
    if complaint:
        print(complaint, file=sys.stderr)
        return 2

    if normalise(a) == normalise(b):
        return 0

    if rel in MAY_DIVERGE:
        print(f'{rel} differs from {twin_repo}. That is expected — spotlite carries this article '
              f'without its download links. Check the difference is only those links.')
        return 0

    print(
        f'{rel} differs between {this_repo} and {twin_repo}, ignoring base paths. '
        f'The two repositories have no merge path, so port the change across before '
        f'committing:\n  {twin}',
        file=sys.stderr,
    )
    return 2


if __name__ == '__main__':
    sys.exit(main())
