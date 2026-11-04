import { Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "../fonts";
import { Icon } from "./Icons";

/** Timeline element written by Claude from the transcript (seconds are clip time). */
export type ProElement =
  | { type: "bigword"; from: number; to: number; /** wrap words in *stars* to colour them accent, rest white */ text: string; y?: number; layer?: "front" | "back"; size?: number }
  | { type: "timeline"; from: number; to: number; points: { label: string; at: number; text?: string }[]; x?: number; y?: number; layer?: "front" | "back" }
  | { type: "counter"; from: number; to: number; value: number; text?: string; prefix?: string; suffix?: string; y?: number; layer?: "front" | "back" }
  | { type: "gauge"; from: number; to: number; value: number; label?: string; suffix?: string; y?: number; layer?: "front" | "back" }
  | { type: "sticker"; from: number; to: number; image?: string; icon?: string; label?: string; x?: number; y?: number; w?: number; rotate?: number; layer?: "front" | "back" }
  | { type: "list"; from: number; to: number; title?: string; items: string[]; /** seconds when each item appears (synced to speech) */ times?: number[]; y?: number; layer?: "front" | "back" };

const ease = (x: number) => 1 - Math.pow(1 - x, 3);

const useInOut = (dur: number) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const inP = spring({ frame, fps, config: { damping: 12, stiffness: 170, mass: 0.8 } });
  const out = interpolate(frame, [dur - 7, dur], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return { frame, fps, inP, out };
};

const textShadow = "0 6px 0 rgba(0,0,0,0.35), 0 10px 30px rgba(0,0,0,0.55)";

export const BigWord: React.FC<{ el: Extract<ProElement, { type: "bigword" }>; dur: number; a: string }> = ({ el, dur, a }) => {
  const { frame, inP, out } = useInOut(dur);
  // auto-fit: the longest word must fit the 1020px width (Montserrat Black ≈ 0.78em per Cyrillic capital)
  const longest = Math.max(...el.text.replace(/\*/g, "").split(/\s+/).map((w) => w.length));
  const size = Math.min(el.size ?? 132, Math.floor(1000 / (longest * 0.78)));
  const shake = frame < 8 ? Math.sin(frame * 2.2) * (8 - frame) * 0.8 : 0;
  return (
    <div style={{ position: "absolute", left: 30, right: 30, top: `${(el.y ?? 0.56) * 100}%`, transform: "translateY(-50%)", textAlign: "center" }}>
      <div
        style={{
          display: "inline-block",
          fontFamily,
          fontWeight: 900,
          fontSize: size,
          lineHeight: 1,
          letterSpacing: -2,
          color: a,
          textTransform: "uppercase",
          textShadow,
          WebkitTextStroke: "3px rgba(0,0,0,0.25)",
          opacity: out,
          transform: `scale(${interpolate(inP, [0, 1], [1.6, 1])}) rotate(${shake}deg)`,
          filter: `blur(${interpolate(inP, [0, 0.6], [8, 0], { extrapolateRight: "clamp" })}px)`,
        }}
      >
        {renderTwoTone(el.text, a)}
      </div>
    </div>
  );
};

/** "*alpha* HUMAN" -> alpha in accent, HUMAN white. No stars = all accent. */
const renderTwoTone = (text: string, a: string) => {
  if (!text.includes("*")) return text;
  return text.split(/(\*[^*]+\*)/).map((part, i) =>
    part.startsWith("*") ? (
      <span key={i} style={{ color: a }}>{part.slice(1, -1)}</span>
    ) : (
      <span key={i} style={{ color: "#fff" }}>{part}</span>
    ),
  );
};

/** Vertical timeline: line grows, each point + label appears when it is spoken. */
export const Timeline: React.FC<{ el: Extract<ProElement, { type: "timeline" }>; dur: number; a: string }> = ({ el, dur, a }) => {
  const { frame, fps, inP, out } = useInOut(dur);
  const x = (el.x ?? 0.68) * 1080;
  const top = (el.y ?? 0.22) * 1920;
  const len = 640;
  const n = el.points.length;
  return (
    <div style={{ position: "absolute", inset: 0, opacity: out, fontFamily }}>
      <div style={{ position: "absolute", left: x - 4, top, width: 8, height: len * inP, background: a, borderRadius: 4, boxShadow: "0 0 20px rgba(0,0,0,.4)" }} />
      <div style={{ position: "absolute", left: x - 16, top: top - 16, width: 32, height: 32, borderRadius: "50%", background: a, transform: `scale(${inP})` }} />
      {el.points.map((pt, i) => {
        const f = Math.round((pt.at - el.from) * fps);
        const p = spring({ frame: frame - f, fps, config: { damping: 13, stiffness: 180 } });
        const py = top + (len * (i + 1)) / (n + 0.4);
        const right = i % 2 === 0;
        return (
          <div key={i} style={{ position: "absolute", top: py - 16, left: 0, width: 1080 }}>
            <div style={{ position: "absolute", left: x - 16, width: 32, height: 32, borderRadius: "50%", background: a, transform: `scale(${p})` }} />
            <div
              style={{
                position: "absolute",
                top: -46,
                ...(right ? { left: x + 46 } : { right: 1080 - x + 46 }),
                textAlign: right ? "left" : "right",
                opacity: p,
                transform: `translateX(${interpolate(p, [0, 1], [right ? 40 : -40, 0])}px)`,
              }}
            >
              <div style={{ fontWeight: 900, fontSize: 92, color: "#fff", lineHeight: 1, letterSpacing: -2, textShadow }}>{pt.label}</div>
              {pt.text ? <div style={{ fontWeight: 800, fontSize: 34, color: a, textShadow, marginTop: 6, maxWidth: 420 }}>{pt.text}</div> : null}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export const Counter: React.FC<{ el: Extract<ProElement, { type: "counter" }>; dur: number; a: string }> = ({ el, dur, a }) => {
  const { frame, fps, inP, out } = useInOut(dur);
  const p = ease(interpolate(frame, [0, fps * 1.1], [0, 1], { extrapolateRight: "clamp" }));
  const n = Math.round(el.value * p).toLocaleString("en-US").replace(/,/g, " ");
  return (
    <div style={{ position: "absolute", left: 20, right: 20, top: `${(el.y ?? 0.3) * 100}%`, transform: "translateY(-50%)", textAlign: "center", opacity: out }}>
      <div style={{ fontFamily, fontWeight: 900, fontSize: 128, lineHeight: 1, color: a, letterSpacing: -3, textShadow, transform: `scale(${interpolate(inP, [0, 1], [0.6, 1])})`, whiteSpace: "nowrap" }}>
        {el.prefix ?? ""}
        {n}
        {el.suffix ?? ""}
        {el.text ? <span style={{ marginLeft: 22, textTransform: "uppercase" }}>{el.text}</span> : null}
      </div>
    </div>
  );
};

/** Segmented radial gauge with a counting percentage and a label pointing at it. */
export const Gauge: React.FC<{ el: Extract<ProElement, { type: "gauge" }>; dur: number; a: string; b: string }> = ({ el, dur, a, b }) => {
  const { frame, fps, inP, out } = useInOut(dur);
  const p = ease(interpolate(frame, [6, 6 + fps * 1.4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const v = el.value * p;
  const segs = 24;
  const R = 230;
  const cx = 540;
  const cy = (el.y ?? 0.25) * 1920;
  const lit = Math.round((v / 100) * segs);
  return (
    <div style={{ position: "absolute", inset: 0, opacity: out }}>
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        {Array.from({ length: segs }).map((_, i) => {
          const appear = interpolate(inP, [i / segs / 1.3, i / segs / 1.3 + 0.2], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const ang = -90 + (i / segs) * 360;
          return (
            <rect
              key={i}
              x={cx - 26}
              y={cy - R - 36}
              width={52}
              height={72}
              rx={6}
              fill={i < lit ? a : b}
              opacity={appear * (i < lit ? 1 : 0.85)}
              transform={`rotate(${ang + 90} ${cx} ${cy})`}
            />
          );
        })}
        {/* needle */}
        <rect x={cx - 5} y={cy - R - 46} width={10} height={92} rx={5} fill="#fff" transform={`rotate(${(v / 100) * 360} ${cx} ${cy})`} opacity={inP} />
      </svg>
      <div style={{ position: "absolute", left: 0, width: 1080, top: cy - 70, textAlign: "center", fontFamily, fontWeight: 900, fontSize: 130, color: "#fff", textShadow, lineHeight: 1 }}>
        {v < 10 && el.value < 10 ? v.toFixed(0) : Math.round(v)}
        {el.suffix ?? "%"}
      </div>
      {el.label ? (
        <div style={{ position: "absolute", left: 0, width: 1080, top: cy + R + 60, display: "flex", justifyContent: "center", alignItems: "center", gap: 18, opacity: inP }}>
          <span style={{ width: interpolate(inP, [0, 1], [0, 90]), height: 6, background: a, borderRadius: 3 }} />
          <span style={{ fontFamily, fontWeight: 900, fontSize: 46, color: "#fff", textTransform: "uppercase", textShadow, whiteSpace: "nowrap" }}>{el.label}</span>
          <span style={{ width: interpolate(inP, [0, 1], [0, 90]), height: 6, background: a, borderRadius: 3 }} />
        </div>
      ) : null}
    </div>
  );
};

/** Cut-out style picture with thick white outline (put on the back layer = behind the speaker). */
export const Sticker: React.FC<{ el: Extract<ProElement, { type: "sticker" }>; dur: number; a: string; b: string }> = ({ el, dur, a, b }) => {
  const { frame, inP, out } = useInOut(dur);
  const w = el.w ?? 760;
  const isPng = (el.image ?? "").toLowerCase().endsWith(".png");
  const rot = (el.rotate ?? -4) + Math.sin(frame / 14) * 1.2;
  const outline = "drop-shadow(0 0 0 #fff) drop-shadow(6px 0 0 #fff) drop-shadow(-6px 0 0 #fff) drop-shadow(0 6px 0 #fff) drop-shadow(0 -6px 0 #fff) drop-shadow(0 25px 35px rgba(0,0,0,.5))";
  return (
    <div
      style={{
        position: "absolute",
        left: (el.x ?? 0.5) * 1080 - w / 2,
        top: (el.y ?? 0.3) * 1920,
        width: w,
        transform: `translateY(-50%) scale(${interpolate(inP, [0, 1], [0.4, 1]) * (1 + frame * 0.0006)}) rotate(${rot}deg)`,
        opacity: out,
        filter: isPng ? outline : "drop-shadow(0 25px 35px rgba(0,0,0,.5))",
      }}
    >
      {el.image ? (
        <Img
          src={staticFile(el.image)}
          style={{
            width: "100%",
            display: "block",
            ...(isPng ? {} : { border: "14px solid #fff", borderRadius: 22, height: w * 0.66, objectFit: "cover" }),
          }}
        />
      ) : (
        <div style={{ width: "100%", height: w * 0.66, borderRadius: 30, border: "14px solid #fff", background: `linear-gradient(135deg, ${a}, ${b})`, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Icon name={el.icon ?? "lightbulb"} size={w * 0.4} color="#111" stroke={1.5} />
        </div>
      )}
      {el.label ? (
        <div style={{ position: "absolute", left: "50%", top: -34, transform: "translateX(-50%) rotate(-3deg)", background: a, color: "#111", fontFamily, fontWeight: 900, fontSize: 46, padding: "8px 26px", borderRadius: 12, whiteSpace: "nowrap", textTransform: "uppercase" }}>
          {el.label}
        </div>
      ) : null}
    </div>
  );
};

export const ListCard: React.FC<{ el: Extract<ProElement, { type: "list" }>; dur: number; a: string }> = ({ el, dur, a }) => {
  const { frame, fps, inP, out } = useInOut(dur);
  return (
    <div style={{ position: "absolute", left: 70, right: 70, top: `${(el.y ?? 0.2) * 100}%`, fontFamily, opacity: out }}>
      {el.title ? <div style={{ fontWeight: 900, fontSize: 64, color: a, textTransform: "uppercase", textShadow, marginBottom: 18, transform: `translateY(${interpolate(inP, [0, 1], [-30, 0])}px)` }}>{el.title}</div> : null}
      {el.items.map((it, i) => {
        const start = el.times?.[i] !== undefined ? Math.round((el.times[i] - el.from) * fps) : 8 + i * 10;
        const p = spring({ frame: frame - start, fps, config: { damping: 15, stiffness: 160 } });
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 14, opacity: p, transform: `translateX(${interpolate(p, [0, 1], [-80, 0])}px)` }}>
            <div style={{ width: 54, height: 54, borderRadius: 14, background: a, color: "#111", fontWeight: 900, fontSize: 36, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>{i + 1}</div>
            <div style={{ fontWeight: 800, fontSize: 48, color: "#fff", textShadow }}>{it}</div>
          </div>
        );
      })}
    </div>
  );
};
