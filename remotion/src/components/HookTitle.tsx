import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "../fonts";

/** Big hook text at the top for the first ~3 seconds (stops the scroll). */
export const HookTitle: React.FC<{ text: string; accent: string; fontSize: number; seconds?: number }> = ({
  text,
  accent,
  fontSize,
  seconds = 3.2,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const inP = spring({ frame, fps, config: { damping: 12, stiffness: 160 } });
  const out = interpolate(frame, [seconds * fps - 8, seconds * fps], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  if (!text || frame > seconds * fps) return null;
  return (
    <AbsoluteFill style={{ alignItems: "center", top: "9%", height: "auto", bottom: "auto" }}>
      <div
        style={{
          fontFamily,
          fontWeight: 900,
          fontSize,
          lineHeight: 1.12,
          color: "#111",
          background: accent,
          padding: `${fontSize * 0.25}px ${fontSize * 0.45}px`,
          borderRadius: fontSize * 0.3,
          maxWidth: "86%",
          textAlign: "center",
          boxShadow: "0 18px 50px rgba(0,0,0,0.45)",
          transform: `scale(${interpolate(inP, [0, 1], [0.6, 1])}) rotate(${interpolate(inP, [0, 1], [-4, -1.5])}deg)`,
          opacity: Math.min(inP, out),
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
