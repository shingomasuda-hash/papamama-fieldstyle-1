import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: "FIELDSTYLE 2026 出店決定｜PAPAMAMA CAR'S",
  description:
    "PAPAMAMA CAR'Sが日本最大級の遊びの祭典 FIELDSTYLE 2026（2026年11月14日・15日／愛知県国際展示場）に出店。会場での相談予約・塗装体験予約を受付中。",
  alternates: { canonical: '/' },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
