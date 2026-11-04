import { Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "../fonts";
import { Icon } from "./Icons";

export type Pop = {
  /** seconds: when the keyword is spoken */
  at: number;
  dur?: number;
  /** image inside public/, e.g. "images/gov_palace.jpg" */
  image?: string;
  icon?: string;
  label: string;
  side?: "left" | "right";
};

/** Polaroid-style picture that pops in beside the video when a keyword is spoken. */
export const KeywordPop: React.FC<{ pop: Pop; a: string; b: string; frames: number; top: number }> = ({
  pop,
  a,
  b,
  frames,
  top,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const right = (pop.side ?? "right") === "right";
  const p = spring({ frame, fps, config: { damping: 12, stiffness: 170 } });
  const out = interpolate(frame, [frames - 8, frames], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const wobble = Math.sin(frame / 9) * 1.2;
  const rot = (right ? 6 : -6) + wobble;
  const x = interpolate(p, [0, 1], [right ? 500 : -500, 0]) + out * (right ? 500 : -500);

  return (
    <div
      style={{
        position: "absolute",
        top,
        [right ? "right" : "left"]: 40,
        width: 400,
        transform: `translateX(${x}px) rotate(${rot}deg) scale(${interpolate(p, [0, 1], [0.7, 1])})`,
        fontFamily,
        filter: "drop-shadow(0 30px 40px rgba(0,0,0,0.55))",
      }}
    >
      <div style={{ background: "#fff", padding: 16, paddingBottom: 18, borderRadius: 18 }}>
        {pop.image ? (
          <Img
            src={staticFile(pop.image)}
            style={{ width: "100%", height: 260, objectFit: "cover", borderRadius: 10, display: "block" }}
          />
        ) : (
          <div
            style={{
              height: 260,
              borderRadius: 10,
              background: `linear-gradient(135deg, ${a}, ${b})`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Icon name={pop.icon ?? "lightbulb"} size={170} color="#111" stroke={1.6} />
          </div>
        )}
        <div
          style={{
            marginTop: 14,
            fontSize: 40,
            fontWeight: 900,
            color: "#111",
            textAlign: "center",
            lineHeight: 1.05,
          }}
        >
          {pop.label}
        </div>
      </div>
      {/* tape sticker */}
      <div
        style={{
          position: "absolute",
          top: -22,
          left: "50%",
          width: 150,
          height: 44,
          marginLeft: -75,
          background: `${a}cc`,
          transform: "rotate(-4deg)",
          borderRadius: 6,
        }}
      />
    </div>
  );
};
