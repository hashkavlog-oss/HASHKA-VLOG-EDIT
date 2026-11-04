import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "../fonts";

/** Thin progress bar (bottom) + optional brand handle (top-right). */
export const Overlay: React.FC<{ accent: string; brand?: string; scale: number }> = ({ accent, brand, scale }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          left: 0,
          bottom: 0,
          height: 8 * scale,
          width: `${(frame / Math.max(1, durationInFrames - 1)) * 100}%`,
          background: accent,
        }}
      />
      {brand ? (
        <div
          style={{
            position: "absolute",
            top: 40 * scale,
            right: 40 * scale,
            fontFamily,
            fontWeight: 800,
            fontSize: 30 * scale,
            color: "rgba(255,255,255,0.85)",
            textShadow: "0 2px 8px rgba(0,0,0,0.6)",
          }}
        >
          {brand}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
