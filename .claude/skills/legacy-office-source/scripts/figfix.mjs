// Finish a slide extracted by slide2svg.mjs into a shippable figure: drop remaining
// presentation furniture, repair the SVG writer's rotated-label overprint, re-crop to the
// content, and strip the definitions the drops orphaned.
//
//   node figfix.mjs fig-raw.svg figure-1.svg --drop "slide title|stray caption" --fix-rotated
//
// --drop removes text shapes whose content contains any of the given phrases — separated by
// | rather than commas, so a phrase can contain a comma — then sweeps the bullet glyphs the
// removal orphans. List bullets are drawn as separate BulletChar groups outside the text
// shape, so removing the shape alone leaves its bullets floating in the figure.
//
// --fix-rotated repairs rotated two-line labels whose lines print on top of each other. For a
// text shape rotated -90 the writer emits the first TextPosition tspan correctly (its anchor
// equals the rotate() centre) but every later tspan at its final page coordinates, still
// inside the rotated frame, so the browser rotates an already-rotated position. The repair is
// the inverse rotation about the transform's own centre — (px, py) becomes
// (cx + cy - py, cy + px - cx) — after which the forward transform lands each line exactly
// where LibreOffice's own PDF export, which renders these labels correctly, puts it.
//
// There is deliberately no dedupe option. Some drawings arrive drawn twice over at identical
// positions; the overlay is pixel-identical and harmless, and removing "duplicates" by
// serialised markup emptied a clipPath — identical markup is not an identical object — which
// clipped its group to nothing. Leave doubled drawings alone.
//
// Needs `puppeteer` resolvable, like slide2svg.mjs: run it from a directory where that is
// installed, or point NODE_PATH at one.
import puppeteer from 'puppeteer'
import { readFileSync, writeFileSync } from 'fs'

const args = process.argv.slice(2)
const flag = (name) => {
  const i = args.indexOf(name)
  return i === -1 ? null : args[i + 1]
}
const [src, out] = args.filter(
  (a, i) => !a.startsWith('--') && (i === 0 || !args[i - 1].startsWith('--'))
)
const drop = (flag('--drop') || '')
  .split('|')
  .map((s) => s.trim())
  .filter(Boolean)
const fixRotated = args.includes('--fix-rotated')

if (!src || !out) {
  console.error('usage: figfix.mjs <in.svg> <out.svg> [--drop "a|b"] [--fix-rotated]')
  process.exit(1)
}

const browser = await puppeteer.launch({
  headless: 'shell',
  args: ['--disable-gpu', '--no-sandbox']
})
const page = await browser.newPage()
await page.setContent(
  `<body style="margin:0">${readFileSync(src, 'utf8').replace(/<\?xml[^>]*\?>\s*/, '')}</body>`,
  { waitUntil: 'load' }
)

const result = await page.evaluate(
  (dropList, fixRot) => {
    const root = document.querySelector('svg')
    const report = { dropped: [], fixed: [], bullets: 0 }

    // Record each dropped shape's rendered rect, then sweep for bullet glyphs sitting on its
    // left margin.
    const droppedRects = []
    for (const t of [...root.querySelectorAll('text')]) {
      const s = t.textContent.replace(/\s+/g, ' ').trim()
      if (!dropList.some((d) => s.includes(d))) continue
      const g = t.closest('g.TextShape, g[class^="com.sun.star"]')
      const target = g || t
      droppedRects.push(target.getBoundingClientRect())
      target.remove()
      report.dropped.push(s.slice(0, 50))
    }
    for (const b of [...root.querySelectorAll('g.BulletChar')]) {
      const r = b.getBoundingClientRect()
      const cx = r.x + r.width / 2,
        cy = r.y + r.height / 2
      const hit = droppedRects.some(
        (d) =>
          cx > d.x - d.width * 0.15 - 20 &&
          cx < d.x + d.width &&
          cy > d.y - d.height * 0.03 &&
          cy < d.y + d.height * 1.03
      )
      if (hit) {
        b.remove()
        report.bullets++
      }
    }

    if (fixRot) {
      for (const t of [...root.querySelectorAll('text[transform]')]) {
        const m = t.getAttribute('transform').match(/rotate\(-90[ ,]+([\d.-]+)[ ,]+([\d.-]+)\)/)
        if (!m) continue
        const cx = Number(m[1]),
          cy = Number(m[2])
        const pos = [...t.querySelectorAll('tspan.TextPosition')]
        for (const ts of pos.slice(1)) {
          const px = Number(ts.getAttribute('x')),
            py = Number(ts.getAttribute('y'))
          ts.setAttribute('x', String(Math.round(cx + cy - py)))
          ts.setAttribute('y', String(Math.round(cy + px - cx)))
        }
        if (pos.length > 1)
          report.fixed.push(t.textContent.replace(/\s+/g, ' ').trim().slice(0, 40))
      }
    }

    const slide = root.querySelector('g.Slide') || root
    const bb = slide.getBBox()
    const pad = Math.max(bb.width, bb.height) * 0.02
    root.setAttribute(
      'viewBox',
      `${Math.round(bb.x - pad)} ${Math.round(bb.y - pad)} ` +
        `${Math.round(bb.width + 2 * pad)} ${Math.round(bb.height + 2 * pad)}`
    )
    root.removeAttribute('width')
    root.removeAttribute('height')

    // Several passes, because removing one definition can orphan another that only it used.
    for (let pass = 0; pass < 3; pass++) {
      const used = new Set()
      for (const el of root.querySelectorAll('*')) {
        for (const a of el.attributes) {
          for (const m of a.value.matchAll(/url\(#([^)]+)\)/g)) used.add(m[1])
          if ((a.name === 'href' || a.name === 'xlink:href') && a.value.startsWith('#')) {
            used.add(a.value.slice(1))
          }
        }
      }
      root.querySelectorAll('defs > *').forEach((d) => {
        if (d.id && !used.has(d.id)) d.remove()
      })
    }
    root.querySelectorAll('defs').forEach((d) => {
      if (!d.children.length) d.remove()
    })

    report.xml = root.outerHTML
    report.viewBox = root.getAttribute('viewBox')
    return report
  },
  drop,
  fixRotated
)

await browser.close()
writeFileSync(out, result.xml)
console.log(`${out}  viewBox ${result.viewBox}  ${(result.xml.length / 1024).toFixed(1)} KB`)
if (result.dropped.length) console.log(`  dropped: ${result.dropped.join(' / ')}`)
if (result.fixed.length) console.log(`  fixed rotated: ${result.fixed.join(' / ')}`)
if (result.bullets) console.log(`  removed orphan bullets: ${result.bullets}`)
