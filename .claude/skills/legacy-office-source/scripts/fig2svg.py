#!/usr/bin/env python3
"""Convert an xfig .fig drawing to SVG.

Written because `fig2dev` (the TransFig tool the original Makefiles call) is not always
installable, and because its SVG output hardcodes black — which is invisible on a dark page.

Covers xfig format 1.4/2.x, which is what pre-1995 papers carry: ellipses, polylines and text.
Splines, arcs and compounds are NOT implemented; the converter refuses a file containing one
rather than silently dropping it. Modern 3.x files have a colour table and different field
orders and are not handled here — use fig2dev for those.

The fig coordinate system with `coord_system 2` is upper-left origin with y increasing
downwards, which is SVG's, so coordinates pass through unchanged and the viewBox is in fig
units. Divide by the header's resolution for inches.

    fig2svg.py DES.FIG "alt text" > figure.svg
    fig2svg.py DES.FIG "alt text" --plain > figure.svg    # black only, no dark-mode block
"""

import argparse
import html
import re
import sys

# xfig font numbers, for the fonts these papers actually use. font_flags bit 2 set means the
# number indexes the PostScript font list instead; both land on the same handful of families.
FONTS = {
    0: ('Times, serif', 'normal', 'normal'),
    1: ('Times, serif', 'normal', 'bold'),
    2: ('Times, serif', 'italic', 'normal'),
    3: ('Times, serif', 'italic', 'bold'),
    4: ('Helvetica, sans-serif', 'normal', 'normal'),
    5: ('Helvetica, sans-serif', 'normal', 'bold'),
    12: ('Courier, monospace', 'normal', 'normal'),
}
ANCHOR = {0: 'start', 1: 'middle', 2: 'end'}
END = 9999          # a points list is terminated by the pair 9999 9999


class FigError(Exception):
    pass


def parse(text):
    """Return (resolution, coord_system, [objects])."""
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    if not lines[0].startswith('#FIG'):
        raise FigError('not an xfig file: no #FIG header')
    version = lines[0].split()[1] if len(lines[0].split()) > 1 else '?'
    if version.startswith('3'):
        raise FigError(f'xfig {version} has a colour table and different field orders; use fig2dev')

    res, coord = (int(v) for v in lines[1].split()[:2])
    objects, i = [], 2

    def points_from(start):
        """Read a points list, which may wrap over several continuation lines."""
        vals, j = [], start
        while j < len(lines):
            vals += [int(float(v)) for v in lines[j].split()]
            j += 1
            if len(vals) >= 2 and vals[-2] == END and vals[-1] == END:
                vals = vals[:-2]
                break
        return list(zip(vals[0::2], vals[1::2])), j

    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.startswith('#'):
            i += 1
            continue
        f = line.split()
        kind = int(f[0])

        if kind == 1:                                   # ellipse
            objects.append({
                'kind': 'ellipse', 'style': int(f[2]), 'thickness': int(f[3]),
                'fill': int(f[7]), 'style_val': float(f[8]),
                'cx': int(f[11]), 'cy': int(f[12]), 'rx': int(f[13]), 'ry': int(f[14]),
            })
            i += 1

        elif kind == 2:                                 # polyline
            sub, style, thickness = int(f[1]), int(f[2]), int(f[3])
            fill, style_val = int(f[7]), float(f[8])
            fwd, back = int(f[9]), int(f[10])
            i += 1
            arrows = {}
            for which, present in (('forward', fwd), ('backward', back)):
                if present:
                    a = lines[i].split()
                    arrows[which] = {'width': float(a[3]), 'height': float(a[4])}
                    i += 1
            pts, i = points_from(i)
            objects.append({
                'kind': 'polyline', 'sub': sub, 'style': style, 'thickness': thickness,
                'fill': fill, 'style_val': style_val, 'points': pts, 'arrows': arrows,
            })

        elif kind == 4:                                 # text
            # 13 numeric fields, then the string, which may contain spaces.
            head = line.split(None, 13)
            body = head[13] if len(head) > 13 else ''
            objects.append({
                'kind': 'text', 'sub': int(head[1]), 'font': int(head[2]),
                'size': float(head[3]), 'angle': float(head[7]),
                'flags': int(head[8]), 'height': float(head[9]),
                'x': int(head[11]), 'y': int(head[12]),
                'text': body.split('\x01')[0],
            })
            i += 1

        elif kind in (3, 5, 6, -6):
            what = {3: 'spline', 5: 'arc', 6: 'compound', -6: 'compound end'}[kind]
            raise FigError(f'line {i + 1}: {what} objects are not implemented')
        else:
            raise FigError(f'line {i + 1}: unknown object type {kind}')

    return res, coord, objects


def dash(style, style_val, thickness):
    """xfig line style to an SVG dash array, in fig units."""
    if style == 1:                                    # dashed
        d = max(style_val, 1.0)
        return f'{d * 2:.1f} {d:.1f}'
    if style == 2:                                    # dotted
        return f'{max(thickness, 1)} {max(style_val, 1.0) * 1.5:.1f}'
    return None


def bbox(objects):
    xs, ys = [], []
    for o in objects:
        if o['kind'] == 'ellipse':
            xs += [o['cx'] - o['rx'], o['cx'] + o['rx']]
            ys += [o['cy'] - o['ry'], o['cy'] + o['ry']]
        elif o['kind'] == 'polyline':
            xs += [p[0] for p in o['points']]
            ys += [p[1] for p in o['points']]
        else:
            # The stored height/length are xfig's own measurement of the string.
            w = o['size'] * 0.5 * len(o['text']) * (80 / 72)
            x0 = {0: o['x'], 1: o['x'] - w / 2, 2: o['x'] - w}[o['sub']]
            xs += [x0, x0 + w]
            ys += [o['y'] - o['size'] * (80 / 72), o['y'] + o['size'] * 0.25]
    return min(xs), min(ys), max(xs), max(ys)


def render(res, objects, label, plain=False, pad=8, box=None):
    # The text extents in bbox() are estimated from the font size and the character count,
    # because only a renderer knows the real ones. The estimate is deliberately generous, so it
    # never clips — but it leaves uneven margins. Pass --bbox with the measured values to tighten
    # it: load the SVG inline in a browser and take the union of getBBox() over every element.
    x0, y0, x1, y1 = box if box else bbox(objects)
    x0, y0 = x0 - pad, y0 - pad
    w, h = (x1 - x0) + pad, (y1 - y0) + pad
    out = []
    # Intrinsic size in CSS pixels, from the drawing's real size in inches: fig units divided by
    # the header resolution, times 96. Without this an <img>-embedded SVG falls back to 300x150.
    px_w, px_h = w * 96.0 / res, h * 96.0 / res
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.0f} {y0:.0f} {w:.0f} {h:.0f}" '
        f'width="{px_w:.0f}" height="{px_h:.0f}" '
        f'role="img" aria-label="{html.escape(label, quote=True)}">'
    )
    # Black on a light page, light on a dark one. An <img>-embedded SVG cannot see the host
    # document's theme class, but it does see the OS preference, which is what this site falls
    # back to when the visitor has not used the toggle.
    if plain:
        out.append('<style>.f{stroke:#000;fill:none}.t{fill:#000}.s{fill:#000;stroke:none}</style>')
    else:
        out.append(
            '<style>'
            '.f{stroke:#000;fill:none}.t{fill:#000}.s{fill:#000;stroke:none}'
            '@media (prefers-color-scheme:dark){'
            '.f{stroke:#d4d4d8}.t{fill:#d4d4d8}.s{fill:#d4d4d8}}'
            '</style>'
        )
    # One marker per distinct arrow size, so a figure with two arrow scales keeps both.
    sizes = sorted({(a['width'], a['height'])
                    for o in objects if o['kind'] == 'polyline'
                    for a in o['arrows'].values()})
    if sizes:
        out.append('<defs>')
        for n, (aw, ah) in enumerate(sizes):
            out.append(
                f'<marker id="a{n}" viewBox="0 0 {ah} {aw}" refX="{ah}" refY="{aw / 2:.2f}" '
                f'markerWidth="{ah}" markerHeight="{aw}" orient="auto-start-reverse" '
                f'markerUnits="userSpaceOnUse">'
                f'<path class="s" d="M0,0 L{ah},{aw / 2:.2f} L0,{aw} Z"/></marker>'
            )
        out.append('</defs>')
    index = {sz: n for n, sz in enumerate(sizes)}

    for o in objects:
        if o['kind'] == 'ellipse':
            attrs = f'cx="{o["cx"]}" cy="{o["cy"]}" rx="{o["rx"]}" ry="{o["ry"]}"'
            sw = f' stroke-width="{o["thickness"]}"'
            d = dash(o['style'], o['style_val'], o['thickness'])
            da = f' stroke-dasharray="{d}"' if d else ''
            out.append(f'<ellipse class="f" {attrs}{sw}{da}/>')

        elif o['kind'] == 'polyline':
            pts = ' '.join(f'{x},{y}' for x, y in o['points'])
            closed = o['sub'] in (2, 3)                # box or polygon
            tag = 'polygon' if closed else 'polyline'
            sw = f' stroke-width="{o["thickness"]}"'
            d = dash(o['style'], o['style_val'], o['thickness'])
            da = f' stroke-dasharray="{d}"' if d else ''
            mk = ''
            if 'forward' in o['arrows']:
                a = o['arrows']['forward']
                mk += f' marker-end="url(#a{index[(a["width"], a["height"])]})"'
            if 'backward' in o['arrows']:
                a = o['arrows']['backward']
                mk += f' marker-start="url(#a{index[(a["width"], a["height"])]})"'
            out.append(f'<{tag} class="f" points="{pts}"{sw}{da}{mk}/>')

        else:
            family, style, weight = FONTS.get(o['font'], FONTS[0])
            size = o['size'] * (res / 72.0)            # points to fig units
            st = f' font-style="{style}"' if style != 'normal' else ''
            wt = f' font-weight="{weight}"' if weight != 'normal' else ''
            rot = (f' transform="rotate({-o["angle"] * 180 / 3.141592653589793:.1f} '
                   f'{o["x"]} {o["y"]})"') if abs(o['angle']) > 1e-6 else ''
            out.append(
                f'<text class="t" x="{o["x"]}" y="{o["y"]}" font-family="{family}" '
                f'font-size="{size:.1f}" text-anchor="{ANCHOR[o["sub"]]}"{st}{wt}{rot}>'
                f'{html.escape(o["text"])}</text>'
            )

    out.append('</svg>')
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('fig')
    ap.add_argument('label', help='aria-label describing the figure')
    ap.add_argument('--plain', action='store_true', help='black only, no dark-mode rule')
    ap.add_argument('--pad', type=int, default=8)
    ap.add_argument('--bbox', help='measured x0,y0,x1,y1 to replace the estimated text extents')
    a = ap.parse_args()
    box = [float(v) for v in a.bbox.split(',')] if a.bbox else None

    text = open(a.fig, encoding='latin-1').read()
    try:
        res, coord, objects = parse(text)
    except FigError as e:
        sys.exit(f'{a.fig}: {e}')
    if coord != 2:
        sys.exit(f'{a.fig}: coord_system {coord} (lower-left origin) is not handled')
    print(render(res, objects, a.label, plain=a.plain, pad=a.pad, box=box))


if __name__ == '__main__':
    main()
