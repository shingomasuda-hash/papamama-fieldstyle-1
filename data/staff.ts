export type StaffMember = {
  id: string;
  name: string;
  kana: string;
  /** Card artwork (586×816 transparent PNG, original pixels). */
  image: string;
  /** Text transcribed from the card artwork for screen readers. */
  description: string;
};

export const STAFF_CARD_SIZE = { width: 586, height: 816 } as const;

export const STAFF: readonly StaffMember[] = [
  {
    id: 'moriyuki',
    name: '森行 啓太',
    kana: 'モリユキ ケイタ',
    image: '/design/staff/staff-01.png',
    description: '趣味：キャンプ、サップ、サッカー、スノボー、ダイビング。特技：お客様を笑顔にできる！ 一言：お客様にとって最高の１台をご提案します！',
  },
  {
    id: 'iinuma',
    name: '飯沼 蒼太郎',
    kana: 'イイヌマ ソウタロウ',
    image: '/design/staff/staff-02.png',
    description: '趣味：アウトドア、旅、サッカー。特技：暴飲暴食。一言：ベストアンサーを探していきましょう！',
  },
  {
    id: 'goto',
    name: '後藤 朱里',
    kana: 'ゴトウ アカリ',
    image: '/design/staff/staff-03.png',
    description: '趣味：サップ、釣り。特技：書道、バスケットボール。',
  },
  {
    id: 'takagi',
    name: '高木 流星',
    kana: 'タカギ リュウセイ',
    image: '/design/staff/staff-04.png',
    description: '趣味：食べること。特技：太ること。一言：こう見えても意外と車屋歴長いです！',
  },
  {
    id: 'yamada',
    name: '山田 零音',
    kana: 'ヤマダ レオト',
    image: '/design/staff/staff-05.png',
    description: '趣味：サッカー、旅行、ゴルフ。特技：太らないこと。一言：なんでもご相談ください！',
  },
  {
    id: 'matsuura',
    name: '松浦 加奈',
    kana: 'マツウラ カナ',
    image: '/design/staff/staff-06.png',
    description: '趣味：モータースポーツ観戦、お酒、食べる事。一言：お客様のカーライフ全般サポート致します！ 最後にこの方お願いします！！',
  },
];
