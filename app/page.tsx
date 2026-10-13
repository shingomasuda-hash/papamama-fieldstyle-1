import Lp1Page from '@/components/Lp1Page';
import { resolveFv } from '@/data/lp1Layout';

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };

export default async function Page({ searchParams }: Props) {
  const { fv } = await searchParams;
  return <Lp1Page fv={resolveFv(fv)} />;
}
