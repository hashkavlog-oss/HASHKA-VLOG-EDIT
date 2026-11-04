export type EditProps = {
  /** Path inside public/, e.g. "jobs/x/video.mp4" */
  video: string;
  /** Path inside public/ to a Caption[] JSON */
  captions: string;
  /** Hook title shown for the first seconds (empty = none) */
  title: string;
  durationInSeconds: number;
  accent?: string;
  /** Vertical caption position 0 (top) – 1 (bottom) */
  captionY?: number;
  /** How long one caption page stays (ms). Lower = fewer words */
  wordsPerPageMs?: number;
  /** Small handle/brand text in the corner, e.g. "@hashka" */
  brand?: string;
  uppercase?: boolean;
};

export const DEFAULTS = {
  accent: "#FFD400",
  wordsPerPageMs: 1100,
  fps: 30,
} as const;
