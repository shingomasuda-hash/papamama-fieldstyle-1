import { CONSULTATION_URL, INSTAGRAM_URL, PAINT_URL } from './links';

/** Native size of /design/lp1-body.png (full design rows y >= 1118). */
export const BODY_W = 509;
export const BODY_H = 13136;

export const FV_IMAGES = {
  '1': { src: '/design/lp1-fv-1.jpg', width: 594, height: 1544 },
  '2': { src: '/design/lp1-fv-2.jpg', width: 596, height: 1554 },
} as const;
export type FvKey = keyof typeof FV_IMAGES;

export function resolveFv(value: string | string[] | undefined): FvKey {
  const v = Array.isArray(value) ? value[0] : value;
  return v === '2' ? '2' : '1';
}

export type Hotspot = {
  id: string;
  href: string;
  label: string;
  /** x, y, w, h in lp1-body.png pixels (button incl. its drop shadow). */
  rect: readonly [number, number, number, number];
};

// Rectangles detected from the button colours in the design and verified visually.
export const HOTSPOTS: readonly Hotspot[] = [
  { id: 'top-consultation', href: CONSULTATION_URL, label: '相談予約', rect: [42, 100, 202, 56] },
  { id: 'top-paint', href: PAINT_URL, label: '塗装体験予約', rect: [272, 100, 202, 56] },
  { id: 'whatwecan-explain', href: CONSULTATION_URL, label: 'まずは説明を聞く（相談予約）', rect: [42, 1285, 432, 55] },
  { id: 'whatwecan-consultation', href: CONSULTATION_URL, label: '相談予約をする', rect: [42, 1368, 432, 56] },
  { id: 'paint-line', href: PAINT_URL, label: 'LINEから予約（塗装体験予約）', rect: [42, 5281, 432, 55] },
  { id: 'footer-consultation', href: CONSULTATION_URL, label: '相談予約', rect: [42, 12150, 202, 55] },
  { id: 'footer-paint', href: PAINT_URL, label: '塗装体験予約', rect: [272, 12150, 202, 56] },
  { id: 'footer-instagram', href: INSTAGRAM_URL, label: 'Instagram', rect: [109, 12970, 76, 76] },
];

/**
 * STAFF slider geometry in lp1-body.png pixels, measured by template matching the
 * staff card PNGs against the static design (scale 0.6525, error ≈ 4/255).
 */
export const STAFF_STAGE = {
  /** Rows covered by staff-stage-bg.png / staff-stage-overlay.png. */
  layerY: 9180 - 1118,
  layerH: 9840 - 9180,
  cardScale: 0.6525,
  cardX: 71,
  cardY: 9206 - 1118,
  /** Card-to-card distance. The design's peeks measure 419 (left) / 423 (right). */
  pitch: 421,
  dotCenterY: 9793.8 - 1118,
  dotCenterX: 255.61,
  dotSpacing: 31.21,
  dotSize: 11,
} as const;

export const pct = (v: number, total: number) => `${(v / total) * 100}%`;
