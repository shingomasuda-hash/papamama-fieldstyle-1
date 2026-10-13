import StaffSlider from './StaffSlider';
import styles from './Lp1Page.module.css';
import { BODY_H, BODY_W, FV_IMAGES, HOTSPOTS, STAFF_STAGE, pct, type FvKey, type Hotspot } from '@/data/lp1Layout';

const FV_ALT =
  "PAPAMAMA CAR'S あなただけの一台で、遊びをもっと自由に。日本最大級の遊びの祭典 FIELDSTYLE OUTDOOR & LIFESTYLE FESTA 出店決定！ 2026年11月14日（土）〜11月15日（日） 愛知県国際展示場";

function HotspotLink({ spot }: { spot: Hotspot }) {
  const [x, y, w, h] = spot.rect;
  return (
    <a
      className={styles.hotspot}
      href={spot.href}
      aria-label={spot.label}
      data-cta={spot.id}
      style={{ left: pct(x, BODY_W), top: pct(y, BODY_H), width: pct(w, BODY_W), height: pct(h, BODY_H) }}
    />
  );
}

export default function Lp1Page({ fv }: { fv: FvKey }) {
  const fvImage = FV_IMAGES[fv];
  // Keep DOM (tab) order equal to the visual order around the STAFF slider.
  const before = HOTSPOTS.filter((s) => s.rect[1] < STAFF_STAGE.layerY);
  const after = HOTSPOTS.filter((s) => s.rect[1] >= STAFF_STAGE.layerY);

  return (
    <main className={styles.page}>
      <h1 className="sr-only">PAPAMAMA CAR&apos;S FIELDSTYLE 2026 出店決定</h1>
      <img
        className={styles.fv}
        src={fvImage.src}
        width={fvImage.width}
        height={fvImage.height}
        alt={FV_ALT}
        fetchPriority="high"
        data-fv={fv}
      />
      <div className={styles.body}>
        <img className={styles.bodyImg} src="/design/lp1-body.png" width={BODY_W} height={BODY_H} alt="" decoding="async" />
        <div className="sr-only">
          <p>あなたの理想の一台を、あなたらしいスタイルで。FIELDSTYLE出店決定！家族で楽しめる塗装体験イベントも開催！愛車の相談OK、下取り査定もOK。相談予約で入場チケット無料プレゼント。</p>
          <p>開催日：2026年11月14日（土）〜15日（日） 09:00〜17:00（ブースOPEN）。会場：AICHI SKY EXPO 愛知国際展示場（〒479-0881 愛知県常滑市セントレア5丁目）。</p>
        </div>
        {before.map((s) => (
          <HotspotLink key={s.id} spot={s} />
        ))}
        <StaffSlider />
        {after.map((s) => (
          <HotspotLink key={s.id} spot={s} />
        ))}
      </div>
    </main>
  );
}
