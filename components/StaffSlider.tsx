'use client';

import { useCallback, useEffect, useLayoutEffect, useRef, useState, type CSSProperties } from 'react';
import styles from './StaffSlider.module.css';
import { BODY_W, IMG_SIZES, STAFF_STAGE as S, srcSet2x } from '@/data/lp1Layout';
import { STAFF, STAFF_CARD_SIZE } from '@/data/staff';

const N = STAFF.length;
// Three copies make the carousel loop so that, like the design, a neighbour card
// peeks in on both sides. Only the middle copy is exposed to assistive tech.
const COPIES = 3;
const CARD_W = STAFF_CARD_SIZE.width * S.cardScale;
const CARD_H = STAFF_CARD_SIZE.height * S.cardScale;

// Rendered card width: 382.4 of 509 design px.
const CARD_SIZES = `(min-width: ${BODY_W}px) ${Math.ceil(CARD_W)}px, ${((CARD_W / BODY_W) * 100).toFixed(2)}vw`;

const mod = (n: number, m: number) => ((n % m) + m) % m;
const useIsoLayoutEffect = typeof window === 'undefined' ? useEffect : useLayoutEffect;

const stageVars = {
  '--layer-y': S.layerY,
  '--layer-h': S.layerH,
  '--card-top': S.cardY - S.layerY,
  '--card-x': S.cardX,
  '--card-w': CARD_W,
  '--card-h': CARD_H,
  '--gap': S.pitch - CARD_W,
  '--pad-right': BODY_W - S.cardX - CARD_W,
  '--dot-top': S.dotCenterY - S.layerY,
  '--dot-size': S.dotSize,
} as CSSProperties;

export default function StaffSlider() {
  const scroller = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(0);
  const activeRef = useRef(0);
  const drag = useRef<{ id: number; x: number; left: number } | null>(null);

  const pitchPx = useCallback(() => {
    const el = scroller.current;
    return el ? (el.clientWidth / BODY_W) * S.pitch : 1;
  }, []);
  const rawIndex = useCallback(() => {
    const el = scroller.current;
    return el ? Math.round(el.scrollLeft / pitchPx()) : N;
  }, [pitchPx]);

  const behavior = (): ScrollBehavior =>
    window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';

  const scrollToRaw = useCallback(
    (raw: number, smooth = true) => {
      scroller.current?.scrollTo({ left: raw * pitchPx(), behavior: smooth ? behavior() : 'instant' });
    },
    [pitchPx],
  );

  // Start on the first staff member of the middle copy; keep position on resize.
  useIsoLayoutEffect(() => {
    const el = scroller.current;
    if (!el) return;
    scrollToRaw(N + activeRef.current, false);
    const ro = new ResizeObserver(() => scrollToRaw(N + activeRef.current, false));
    ro.observe(el);
    return () => ro.disconnect();
  }, [scrollToRaw]);

  // Track the visible card, and silently re-centre into the middle copy once settled.
  useEffect(() => {
    const el = scroller.current;
    if (!el) return;
    const hasScrollEnd = 'onscrollend' in window;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const settle = () => {
      if (drag.current) return;
      el.style.scrollSnapType = '';
      const raw = rawIndex();
      if (raw < N || raw >= 2 * N) scrollToRaw(N + mod(raw, N), false);
    };
    const onScroll = () => {
      const i = mod(rawIndex(), N);
      if (i !== activeRef.current) {
        activeRef.current = i;
        setActive(i);
      }
      if (!hasScrollEnd) {
        clearTimeout(timer);
        timer = setTimeout(settle, 150);
      }
    };
    el.addEventListener('scroll', onScroll, { passive: true });
    el.addEventListener('scrollend', settle);
    return () => {
      el.removeEventListener('scroll', onScroll);
      el.removeEventListener('scrollend', settle);
      clearTimeout(timer);
    };
  }, [rawIndex, scrollToRaw]);

  const goTo = (i: number) => {
    const raw = rawIndex();
    scrollToRaw(raw - mod(raw, N) + i);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    const keys: Record<string, () => void> = {
      ArrowLeft: () => scrollToRaw(rawIndex() - 1),
      ArrowRight: () => scrollToRaw(rawIndex() + 1),
      Home: () => goTo(0),
      End: () => goTo(N - 1),
    };
    const fn = keys[e.key];
    if (fn) {
      e.preventDefault();
      fn();
    }
  };

  // Mouse drag (touch and trackpads use native scrolling).
  const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if (e.pointerType !== 'mouse' || e.button !== 0) return;
    const el = e.currentTarget;
    drag.current = { id: e.pointerId, x: e.clientX, left: el.scrollLeft };
    el.setPointerCapture(e.pointerId);
    el.style.scrollSnapType = 'none';
    el.dataset.dragging = 'true';
  };
  const onPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    const d = drag.current;
    if (!d || d.id !== e.pointerId) return;
    e.currentTarget.scrollLeft = d.left - (e.clientX - d.x);
  };
  const endDrag = (e: React.PointerEvent<HTMLDivElement>) => {
    const d = drag.current;
    if (!d || d.id !== e.pointerId) return;
    drag.current = null;
    const el = e.currentTarget;
    delete el.dataset.dragging;
    const moved = el.scrollLeft - d.left;
    const start = Math.round(d.left / pitchPx());
    // A short flick is enough to move one card; longer drags land on the nearest card.
    const target = Math.abs(moved) > pitchPx() / 2 ? rawIndex() : Math.abs(moved) > 30 ? start + Math.sign(moved) : start;
    scrollToRaw(target);
  };

  return (
    <section className={styles.stage} style={stageVars} aria-roledescription="carousel" aria-label="スタッフ紹介">
      <img className={styles.layer} src="/design/staff-stage-bg.png" srcSet={srcSet2x('/design/staff-stage-bg.png', '/design/staff-stage-bg@2x.png', 509)} sizes={IMG_SIZES} width={509} height={660} alt="" aria-hidden="true" draggable={false} />
      <div
        ref={scroller}
        className={styles.scroller}
        tabIndex={0}
        aria-label="スタッフ一覧（左右の矢印キーで切り替え）"
        onKeyDown={onKeyDown}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
      >
        <div className={styles.track}>
          {Array.from({ length: COPIES }, (_, c) =>
            STAFF.map((m, i) => {
              const live = c === 1;
              return (
                <div
                  key={`${c}-${m.id}`}
                  className={styles.slide}
                  role={live ? 'group' : undefined}
                  aria-roledescription={live ? 'slide' : undefined}
                  aria-label={live ? `${i + 1} / ${N}` : undefined}
                  aria-hidden={live ? undefined : true}
                  inert={!live}
                  data-staff={live ? i + 1 : undefined}
                >
                  <img
                    src={m.image}
                    srcSet={srcSet2x(m.image, m.image2x, STAFF_CARD_SIZE.width)}
                    sizes={CARD_SIZES}
                    width={STAFF_CARD_SIZE.width}
                    height={STAFF_CARD_SIZE.height}
                    alt={live ? `${m.name}（${m.kana}）。${m.description}` : ''}
                    draggable={false}
                    loading={live && i === 0 ? 'eager' : 'lazy'}
                  />
                </div>
              );
            }),
          )}
        </div>
      </div>
      <img className={styles.overlay} src="/design/staff-stage-overlay.png" srcSet={srcSet2x('/design/staff-stage-overlay.png', '/design/staff-stage-overlay@2x.png', 509)} sizes={IMG_SIZES} width={509} height={660} alt="" aria-hidden="true" draggable={false} />
      <div className={styles.dots} role="group" aria-label="表示するスタッフを選択">
        {STAFF.map((m, i) => (
          <button
            key={m.id}
            type="button"
            className={styles.dot}
            style={{ '--dot-x': S.dotCenterX + (i - (N - 1) / 2) * S.dotSpacing } as CSSProperties}
            aria-label={`${i + 1}人目：${m.name}`}
            aria-current={active === i ? 'true' : undefined}
            onClick={() => goTo(i)}
          />
        ))}
      </div>
      <p className="sr-only" aria-live="polite" aria-atomic="true">
        {`${active + 1} / ${N}：${STAFF[active].name}`}
      </p>
    </section>
  );
}
