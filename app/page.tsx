import Lp1Page from '@/components/Lp1Page';
import { resolveFv } from '@/data/lp1Layout';

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };

export default async function Page({ searchParams }: Props) {
  const { fv } = await searchParams;
  // DEFAULT_FV picks the FV for / when no ?fv is given (set to 2 on the LP1-1 Vercel project only).
  return <Lp1Page fv={resolveFv(fv ?? process.env.DEFAULT_FV)} />;
}
