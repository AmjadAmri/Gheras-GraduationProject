export function formatAgeGroup(ageGroup?: string | null): string {
  const value = (ageGroup || "").trim();
  if (!value) return "";
  return value.replace(/\s+/g, "");
}

export function artStylePreview(styleKey: string): string {
  const palettes: Record<string, { bg1: string; bg2: string; accent: string }> = {
    storybook: { bg1: '#20C4B2', bg2: '#1AA3A4', accent: '#FDE68A' },
    cartoon: { bg1: '#FF8A7A', bg2: '#F05D5E', accent: '#FDE68A' },
    watercolor: { bg1: '#7DD3FC', bg2: '#38BDF8', accent: '#E0F2FE' },
    paper: { bg1: '#F59E0B', bg2: '#F97316', accent: '#FEF3C7' },
    pixel: { bg1: '#EC4899', bg2: '#DB2777', accent: '#FBCFE8' },
    anime: { bg1: '#818CF8', bg2: '#6366F1', accent: '#E0E7FF' },
  };

  const palette = palettes[styleKey] || { bg1: '#20C4B2', bg2: '#0EA5A4', accent: '#CCFBF1' };

  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">
      <defs>
        <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="${palette.bg1}"/>
          <stop offset="100%" stop-color="${palette.bg2}"/>
        </linearGradient>
      </defs>
      <rect width="640" height="360" rx="28" fill="url(#g)"/>
      <circle cx="110" cy="85" r="46" fill="${palette.accent}" opacity="0.95"/>
      <circle cx="528" cy="86" r="34" fill="#ffffff" opacity="0.20"/>
      <rect x="86" y="170" width="468" height="112" rx="26" fill="#ffffff" opacity="0.18"/>
      <rect x="116" y="194" width="190" height="20" rx="10" fill="#ffffff" opacity="0.78"/>
      <rect x="116" y="230" width="288" height="16" rx="8" fill="#ffffff" opacity="0.48"/>
      <rect x="426" y="190" width="92" height="92" rx="24" fill="#ffffff" opacity="0.24"/>
      <circle cx="472" cy="238" r="24" fill="${palette.accent}" opacity="0.95"/>
    </svg>
  `;

  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}
