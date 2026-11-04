import { AbsoluteFill, interpolate, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Video } from "@remotion/media";
import { Background } from "./components/Background";
import { Captions } from "./components/Captions";
import { Card, InfoCard } from "./components/InfoCard";
import { KeywordPop, Pop } from "./components/KeywordPop";
import { fontFamily } from "./fonts";
import { DEFAULTS, EditProps } from "./types";

export type InfoReelProps = EditProps & {
  cards?: Card[];
  /** pictures that pop in when a keyword is spoken */
  pops?: Pop[];
  /** second accent colour (shapes, bullets) */
  accent2?: string;
  /** small label under the video, e.g. "HASHKA'S PODCAST" */
  show?: string;
};

// 16:9 video framed in the middle of a 9:16 canvas
const VW = 1000;
const VH = Math.round((VW * 9) / 16);
const VTOP = 790;

export const InfoReel: React.FC<InfoReelProps> = (p) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const a = p.accent ?? DEFAULTS.accent;
  const b = p.accent2 ?? "#2EE6D6";
  const enter = spring({ frame, fps, config: { damping: 18, stiffness: 120 } });
  const zoom = interpolate(frame, [0, durationInFrames], [1, 1.06]);
  const hookFrames = Math.round(3.4 * fps);

  return (
    <AbsoluteFill style={{ fontFamily }}>
      <Background a={a} b={b} />

      {/* video frame */}
      <div
        style={{
          position: "absolute",
          left: (1080 - VW) / 2,
          top: VTOP,
          width: VW,
          height: VH,
          borderRadius: 40,
          overflow: "hidden",
          boxShadow: `0 0 0 4px ${a}, 0 0 70px ${a}55, 0 40px 90px rgba(0,0,0,0.6)`,
          transform: `scale(${interpolate(enter, [0, 1], [0.9, 1])})`,
          opacity: enter,
        }}
      >
        {p.video ? (
          <Video
            src={staticFile(p.video)}
            style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${zoom})` }}
          />
        ) : (
          <div style={{ width: "100%", height: "100%", background: "#333" }} />
        )}
      </div>
      {/* corner shapes on the frame */}
      <div style={{ position: "absolute", left: 22, top: VTOP - 28, width: 90, height: 90, borderLeft: `8px solid ${b}`, borderTop: `8px solid ${b}`, borderRadius: "28px 0 0 0", opacity: enter }} />
      <div style={{ position: "absolute", right: 22, top: VTOP + VH - 62, width: 90, height: 90, borderRight: `8px solid ${b}`, borderBottom: `8px solid ${b}`, borderRadius: "0 0 28px 0", opacity: enter }} />

      {/* show label */}
      {p.show ? (
        <div
          style={{
            position: "absolute",
            top: VTOP + VH + 34,
            width: "100%",
            textAlign: "center",
            fontSize: 30,
            fontWeight: 800,
            letterSpacing: 8,
            color: "rgba(255,255,255,0.55)",
          }}
        >
          ● {p.show.toUpperCase()} ●
        </div>
      ) : null}

      {/* hook title (first seconds) */}
      {p.title ? (
        <Sequence durationInFrames={hookFrames} layout="none">
          <Hook text={p.title} a={a} frames={hookFrames} />
        </Sequence>
      ) : null}

      {/* topic info cards */}
      {(p.cards ?? []).map((c, i) => {
        const from = Math.round(c.from * fps);
        const dur = Math.round((c.to - c.from) * fps);
        return dur > 0 ? (
          <Sequence key={i} from={from} durationInFrames={dur} layout="none">
            <InfoCard card={c} a={a} b={b} durationInFrames={dur} />
          </Sequence>
        ) : null;
      })}

      {/* keyword pictures: over the upper half of the video frame */}
      {(p.pops ?? []).map((pp, i) => {
        const from = Math.round(pp.at * fps);
        const dur = Math.round((pp.dur ?? 2.6) * fps);
        return (
          <Sequence key={`pop${i}`} from={from} durationInFrames={dur} layout="none">
            <KeywordPop pop={pp} a={a} b={b} frames={dur} top={VTOP - 210} />
          </Sequence>
        );
      })}

      {p.captions ? (
        <Captions
          src={p.captions}
          accent={a}
          switchEveryMs={p.wordsPerPageMs ?? 1000}
          y={p.captionY ?? 0.79}
          fontSize={72}
          maxWidth={960}
          uppercase={p.uppercase ?? false}
        />
      ) : null}

      {/* progress bar */}
      <div style={{ position: "absolute", left: 0, bottom: 0, height: 10, width: `${(frame / (durationInFrames - 1)) * 100}%`, background: `linear-gradient(90deg, ${a}, ${b})` }} />
      {p.brand ? (
        <div style={{ position: "absolute", top: 60, right: 50, fontSize: 32, fontWeight: 800, color: "rgba(255,255,255,0.8)" }}>{p.brand}</div>
      ) : null}
    </AbsoluteFill>
  );
};

const Hook: React.FC<{ text: string; a: string; frames: number }> = ({ text, a, frames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame, fps, config: { damping: 11, stiffness: 150 } });
  const out = interpolate(frame, [frames - 10, frames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div
      style={{
        position: "absolute",
        left: 60,
        right: 60,
        top: 230,
        display: "flex",
        justifyContent: "center",
        opacity: Math.min(p, out),
        transform: `scale(${interpolate(p, [0, 1], [0.5, 1])}) rotate(-2deg)`,
      }}
    >
      <div
        style={{
          background: a,
          color: "#111",
          fontSize: 84,
          fontWeight: 900,
          lineHeight: 1.08,
          textAlign: "center",
          padding: "34px 46px",
          borderRadius: 40,
          boxShadow: `0 0 0 8px rgba(255,255,255,0.08), 0 30px 80px ${a}55`,
        }}
      >
        {text}
      </div>
    </div>
  );
};
