import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

/** Dark animated background: drifting glow blobs, dot grid and slow rotating rings. */
export const Background: React.FC<{ a: string; b: string }> = ({ a, b }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const blob = (x: number, y: number, r: number, c: string, sp: number, ph: number) => (
    <div
      style={{
        position: "absolute",
        left: x + Math.sin(t * sp + ph) * 90 - r,
        top: y + Math.cos(t * sp * 0.8 + ph) * 70 - r,
        width: r * 2,
        height: r * 2,
        borderRadius: "50%",
        background: c,
        filter: "blur(120px)",
        opacity: 0.55,
      }}
    />
  );
  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg,#0A0E1A 0%,#101629 50%,#0A0E1A 100%)", overflow: "hidden" }}>
      {blob(180, 260, 300, a, 0.35, 0)}
      {blob(920, 520, 260, b, 0.3, 2)}
      {blob(200, 1650, 280, b, 0.25, 4)}
      {blob(900, 1500, 240, a, 0.32, 1)}
      <AbsoluteFill
        style={{
          backgroundImage: "radial-gradient(rgba(255,255,255,0.09) 1.6px, transparent 1.6px)",
          backgroundSize: "36px 36px",
          maskImage: "linear-gradient(180deg, black 0%, transparent 35%, transparent 65%, black 100%)",
        }}
      />
      {[0, 1].map((i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: i ? -260 : 760,
            top: i ? 1380 : -160,
            width: 560,
            height: 560,
            borderRadius: "50%",
            border: `3px dashed ${i ? b : a}`,
            opacity: 0.22,
            transform: `rotate(${t * (i ? -8 : 10)}deg)`,
          }}
        />
      ))}
    </AbsoluteFill>
  );
};
