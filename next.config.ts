import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Design images are served as-is from /public/design (no re-encoding).
  images: { unoptimized: true },
};

export default nextConfig;
