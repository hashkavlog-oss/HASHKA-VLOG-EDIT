import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "../fonts";
import { Icon } from "./Icons";

export type Card = {
  /** seconds */
  from: number;
  to: number;
  icon: string;
  /** small label above the title, e.g. "СЭДЭВ" */
  kicker?: string;
  title: string;
  points?: string[];
  /** big animated number, e.g. {value: 70, suffix: "%", label: "..."} */
  stat?: { value: number; prefix?: string; suffix?: string; label: string };
};

export const InfoCard: React.FC<{ card: Card; a: string; b: string; durationInFrames: number }> = ({
  card,
  a,
  b,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 15, stiffness: 140 } });
  const exit = interpolate(frame, [durationInFrames - 10, durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const iconPop = spring({ frame: frame - 6, fps, config: { damping: 9, stiffness: 180 } });
  const statP = interpolate(frame, [10, 10 + fps * 1.2], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: (x) => 1 - Math.pow(1 - x, 3),
  });

  return (
    <div
      style={{
        position: "absolute",
        left: 50,
        right: 50,
        top: 150,
        fontFamily,
        color: "#fff",
        opacity: enter * (1 - exit),
        transform: `translateY(${interpolate(enter, [0, 1], [-60, 0]) + exit * -40}px) scale(${interpolate(enter, [0, 1], [0.92, 1])})`,
      }}
    >
      <div
        style={{
          position: "relative",
          borderRadius: 44,
          padding: "42px 44px 44px 44px",
          background: "linear-gradient(135deg, rgba(255,255,255,0.13), rgba(255,255,255,0.04))",
          border: "2px solid rgba(255,255,255,0.16)",
          boxShadow: `0 30px 80px rgba(0,0,0,0.45), inset 0 0 0 1px rgba(255,255,255,0.05)`,
          backdropFilter: "blur(10px)",
          overflow: "hidden",
        }}
      >
        {/* accent bar */}
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            bottom: 0,
            width: 14,
            background: `linear-gradient(180deg, ${a}, ${b})`,
            transform: `scaleY(${enter})`,
            transformOrigin: "top",
          }}
        />
        <div style={{ display: "flex", alignItems: "center", gap: 30 }}>
          <div style={{ position: "relative", width: 132, height: 132, flexShrink: 0 }}>
            <div
              style={{
                position: "absolute",
                inset: -10,
                borderRadius: "50%",
                border: `4px dashed ${b}`,
                opacity: 0.7,
                transform: `rotate(${frame * 1.5}deg)`,
              }}
            />
            <div
              style={{
                width: 132,
                height: 132,
                borderRadius: "50%",
                background: a,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transform: `scale(${iconPop})`,
                boxShadow: `0 0 50px ${a}88`,
              }}
            >
              <Icon name={card.icon} size={74} color="#111" stroke={2.1} />
            </div>
          </div>
          <div style={{ flex: 1 }}>
            {card.kicker ? (
              <div style={{ fontSize: 30, fontWeight: 800, letterSpacing: 4, color: b, marginBottom: 6 }}>
                {card.kicker.toUpperCase()}
              </div>
            ) : null}
            <div style={{ fontSize: 58, fontWeight: 900, lineHeight: 1.08 }}>{card.title}</div>
          </div>
        </div>

        {card.stat ? (
          <div style={{ display: "flex", alignItems: "baseline", gap: 22, marginTop: 30 }}>
            <div style={{ fontSize: 120, fontWeight: 900, color: a, lineHeight: 1 }}>
              {card.stat.prefix ?? ""}
              {Math.round(card.stat.value * statP)}
              {card.stat.suffix ?? ""}
            </div>
            <div style={{ fontSize: 36, fontWeight: 700, lineHeight: 1.2, opacity: 0.9 }}>{card.stat.label}</div>
          </div>
        ) : null}

        {card.points?.length ? (
          <div style={{ marginTop: 28, display: "flex", flexDirection: "column", gap: 16 }}>
            {card.points.map((pt, i) => {
              const p = spring({ frame: frame - 14 - i * 9, fps, config: { damping: 16, stiffness: 160 } });
              return (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 18,
                    fontSize: 40,
                    fontWeight: 700,
                    opacity: p,
                    transform: `translateX(${interpolate(p, [0, 1], [50, 0])}px)`,
                  }}
                >
                  <div
                    style={{
                      width: 50,
                      height: 50,
                      borderRadius: 14,
                      background: `${b}33`,
                      border: `2px solid ${b}`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    <Icon name="check" size={32} color={b} stroke={3} />
                  </div>
                  <span style={{ lineHeight: 1.2 }}>{pt}</span>
                </div>
              );
            })}
          </div>
        ) : null}
      </div>
    </div>
  );
};
