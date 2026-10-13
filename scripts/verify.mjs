// QA for LP1: screenshots, CTA hrefs/hit-testing, FV switching, STAFF slider.
// Usage: BASE_URL=http://localhost:3000 node scripts/verify.mjs
// Outputs qa/screenshots/* and qa/screenshots/report.json (compare with scripts/compare.py).
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync, existsSync } from 'node:fs';

const BASE = process.env.BASE_URL ?? 'http://localhost:3000';
const OUT = 'qa/screenshots';
mkdirSync(OUT, { recursive: true });

const EXPECTED = {
  'top-consultation': 'https://s.lmes.jp/landing-qr/2007227107-GgA3P6zw?uLand=hxg1Jo',
  'top-paint': 'https://s.lmes.jp/landing-qr/2007227107-GgA3P6zw?uLand=WvWa0c',
  'whatwecan-explain': 'https://s.lmes.jp/landing-qr/2007227107-GgA3P6zw?uLand=hxg1Jo',
  'whatwecan-consultation': 'https://s.lmes.jp/landing-qr/2007227107-GgA3P6zw?uLand=hxg1Jo',
  'paint-line': 'https://s.lmes.jp/landing-qr/2007227107-GgA3P6zw?uLand=WvWa0c',
  'footer-consultation': 'https://s.lmes.jp/landing-qr/2007227107-GgA3P6zw?uLand=hxg1Jo',
  'footer-paint': 'https://s.lmes.jp/landing-qr/2007227107-GgA3P6zw?uLand=WvWa0c',
  'footer-instagram': 'https://s.lmes.jp/landing-qr/2007227107-GgA3P6zw?uLand=pxS26L',
};

const exe = process.env.CHROMIUM_PATH ?? '/opt/pw-browsers/chromium';
const browser = await chromium.launch(existsSync(exe) ? { executablePath: exe } : {});
const report = { pages: {}, slider: {}, failures: [] };
const fail = (msg) => {
  report.failures.push(msg);
  console.error('FAIL', msg);
};

async function open(width, query = '', touch = false) {
  const ctx = await browser.newContext({ viewport: { width, height: 900 }, deviceScaleFactor: 1, hasTouch: touch, isMobile: touch });
  const page = await ctx.newPage();
  await page.goto(`${BASE}/${query}`, { waitUntil: 'load' });
  // Lazy images that are off-screen never resolve decode(), so skip them and cap the wait.
  await page.evaluate(() =>
    Promise.race([
      Promise.all([...document.images].filter((i) => i.loading !== 'lazy').map((i) => i.decode().catch(() => {}))),
      new Promise((r) => setTimeout(r, 5000)),
    ]),
  );
  await page.waitForTimeout(300);
  return { ctx, page };
}

// State of the slider: which staff card sits at the design's card position.
const sliderState = (page) =>
  page.evaluate(() => {
    const sc = document.querySelector('[aria-label^="スタッフ一覧"]');
    const u = sc.clientWidth / 509;
    const target = sc.getBoundingClientRect().left + 71 * u;
    const slides = [...sc.querySelectorAll(':scope > div > div')];
    let best = null;
    slides.forEach((s, k) => {
      const d = Math.abs(s.getBoundingClientRect().left - target);
      if (!best || d < best.d) best = { k, d };
    });
    const dots = [...document.querySelectorAll('[aria-label="表示するスタッフを選択"] button')];
    return {
      visible: (best.k % 6) + 1,
      offsetPx: +best.d.toFixed(2),
      copy: Math.floor(best.k / 6),
      activeDot: dots.findIndex((d) => d.getAttribute('aria-current') === 'true') + 1,
      live: document.querySelector('[aria-live="polite"]')?.textContent,
    };
  });

for (const width of [509, 390, 375]) {
  for (const fv of ['1', '2']) {
    const { ctx, page } = await open(width, fv === '2' ? '?fv=2' : '');
    const data = await page.evaluate(() => {
      const fvImg = document.querySelector('img[data-fv]');
      const body = fvImg.nextElementSibling;
      const b = body.getBoundingClientRect();
      const f = fvImg.getBoundingClientRect();
      const ctas = [...document.querySelectorAll('a[data-cta]')].map((a) => {
        const bb = body.getBoundingClientRect();
        const r = a.getBoundingClientRect();
        a.scrollIntoView({ block: 'center' });
        const r2 = a.getBoundingClientRect();
        const hit = document.elementFromPoint(r2.left + r2.width / 2, r2.top + r2.height / 2);
        return {
          id: a.dataset.cta,
          href: a.getAttribute('href'),
          label: a.getAttribute('aria-label'),
          rel: { x: r.left - bb.left, y: r.top - bb.top, w: r.width, h: r.height },
          hitOk: hit === a,
        };
      });
      window.scrollTo(0, 0);
      return {
        fvSrc: fvImg.getAttribute('src'),
        fvRect: { top: f.top + scrollY, h: f.height, w: f.width, left: f.left },
        bodyRect: { top: b.top + scrollY, h: b.height, w: b.width, left: b.left },
        scrollWidth: document.documentElement.scrollWidth,
        innerWidth,
        ctas,
      };
    });
    const tag = `w${width}-fv${fv}`;
    console.log('page', tag);
    if (Math.abs(data.bodyRect.top - (data.fvRect.top + data.fvRect.h)) > 0.01) fail(`${tag}: seam gap between FV and body`);
    if (data.scrollWidth > data.innerWidth) fail(`${tag}: horizontal scroll`);
    for (const c of data.ctas) {
      if (EXPECTED[c.id] !== c.href) fail(`${tag}: ${c.id} href ${c.href}`);
      if (!c.hitOk) fail(`${tag}: ${c.id} is covered by another element`);
    }
    if (data.ctas.length !== Object.keys(EXPECTED).length) fail(`${tag}: CTA count ${data.ctas.length}`);
    data.slider = await sliderState(page);
    // Chromium's full-page capture resets inner scroll offsets (slider jumps to scrollLeft≈14),
    // so the STAFF stage is also captured as an element shot at rest; compare.py pastes it back.
    const stage = page.locator('section[aria-roledescription="carousel"]');
    await stage.scrollIntoViewIfNeeded();
    await page.waitForTimeout(600);
    data.stageShotTop = await stage.evaluate((el) => el.getBoundingClientRect().top + scrollY);
    await stage.screenshot({ path: `${OUT}/stage-${tag}.png` });
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: `${OUT}/${tag}.png`, fullPage: true });
    report.pages[tag] = data;
    await ctx.close();
  }
}

// FV2 must only change the FV image.
for (const width of [509, 390, 375]) {
  const a = report.pages[`w${width}-fv1`];
  const b = report.pages[`w${width}-fv2`];
  if (a.bodyRect.h !== b.bodyRect.h) fail(`w${width}: body height differs between FV1/FV2`);
  if (JSON.stringify(a.ctas.map((c) => [c.id, c.href, c.rel])) !== JSON.stringify(b.ctas.map((c) => [c.id, c.href, c.rel])))
    fail(`w${width}: CTA geometry differs between FV1/FV2`);
  if (JSON.stringify(a.slider) !== JSON.stringify(b.slider)) fail(`w${width}: slider initial state differs`);
}

// ---- STAFF slider interaction --------------------------------------------------
async function stageShot(page, name) {
  const el = page.locator('section[aria-roledescription="carousel"]');
  await el.screenshot({ path: `${OUT}/${name}.png` });
}
const settle = (page) => page.waitForTimeout(900);

{
  // Touch swipe (CDP synthesized touch scroll gesture) at 390px.
  const { ctx, page } = await open(390, '', true);
  const sc = page.locator('[aria-label^="スタッフ一覧"]');
  await sc.scrollIntoViewIfNeeded();
  const box = await sc.boundingBox();
  const cdp = await ctx.newCDPSession(page);
  const seq = [await sliderState(page)];
  // Real touch drag (touchStart → touchMove… → touchEnd) across the card.
  const swipe = async (dx) => {
    const y = Math.round(box.y + box.height / 2);
    const x0 = Math.round(box.x + box.width / 2 - dx / 2);
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: x0, y }] });
    for (let s = 1; s <= 10; s++) {
      await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x0 + (dx * s) / 10, y }] });
      await page.waitForTimeout(16);
    }
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await settle(page);
    seq.push(await sliderState(page));
  };
  for (let i = 0; i < 6; i++) {
    await stageShot(page, `staff-touch-${seq.at(-1).visible}`);
    await swipe(-200);
  }
  await swipe(200);
  report.slider.touch = seq;
  const seen = new Set(seq.map((s) => s.visible));
  if (seen.size !== 6) fail(`touch swipe saw ${[...seen]}`);
  if (seq.some((s) => s.visible !== s.activeDot)) fail('touch: dot out of sync');
  if (seq.some((s) => s.offsetPx > 1)) fail('touch: card not snapped to design position');
  await ctx.close();
}

{
  // Keyboard, dots and mouse drag at 509px.
  const { ctx, page } = await open(509);
  const sc = page.locator('[aria-label^="スタッフ一覧"]');
  await sc.scrollIntoViewIfNeeded();
  await stageShot(page, 'staff-initial-509');
  await sc.focus();
  const keys = [await sliderState(page)];
  for (let i = 0; i < 6; i++) {
    await page.keyboard.press('ArrowRight');
    await settle(page);
    keys.push(await sliderState(page));
  }
  await page.keyboard.press('ArrowLeft');
  await settle(page);
  keys.push(await sliderState(page));
  report.slider.keyboard = keys;
  if (keys.map((k) => k.visible).join() !== '1,2,3,4,5,6,1,6') fail(`keyboard order ${keys.map((k) => k.visible)}`);

  const dots = [];
  for (let i = 5; i >= 0; i--) {
    await page.locator('[aria-label="表示するスタッフを選択"] button').nth(i).click();
    await settle(page);
    const s = await sliderState(page);
    dots.push(s);
    if (s.visible !== i + 1 || s.activeDot !== i + 1) fail(`dot ${i + 1} -> ${JSON.stringify(s)}`);
    await stageShot(page, `staff-dot-${i + 1}`);
  }
  report.slider.dots = dots;

  const box = await sc.boundingBox();
  const drags = [];
  for (const dx of [-160, -160, 160]) {
    await page.mouse.move(box.x + 250, box.y + 250);
    await page.mouse.down();
    for (let s = 1; s <= 8; s++) await page.mouse.move(box.x + 250 + (dx * s) / 8, box.y + 250);
    await page.mouse.up();
    await settle(page);
    drags.push(await sliderState(page));
  }
  report.slider.mouse = drags;
  if (drags.map((d) => d.visible).join() !== '2,3,2') fail(`mouse drag ${drags.map((d) => d.visible)}`);
  await ctx.close();
}

writeFileSync(`${OUT}/report.json`, JSON.stringify(report, null, 2));
await browser.close();
console.log(report.failures.length ? `${report.failures.length} failure(s)` : 'all checks passed');
process.exit(report.failures.length ? 1 : 0);
