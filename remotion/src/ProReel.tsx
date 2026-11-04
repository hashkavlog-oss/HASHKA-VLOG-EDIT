import { AbsoluteFill, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Captions } from "./components/Captions";
import { Icon } from "./components/Icons";
import { BigWord, Counter, Gauge, ListCard, ProElement, Sticker, Timeline } from "./components/ProElements";
import { fontFamily } from "./fonts";
import { DEFAULTS, EditProps } from "./types";

export type ProReelProps = EditProps & {
  /** person-only layer (VP9 webm with alpha) for graphics behind the speaker */
  fg?: string;
  elements?: ProElement[];
  accent2?: string;
  /** top-left logo text, e.g. "HASHKA'S\nPODCAST" */
  logo?: string;
};

const El: React.FC<{ el: ProElement; dur: number; a: string; b: string }> = ({ el, dur, a, b }) => {
  switch (el.type) {
    case "bigword":
      return <BigWord el={el} dur={dur} a={a} />;
    case "counter":
      return <Counter el={el} dur={dur} a={a} />;
    case "gauge":
      return <Gauge el={el} dur={dur} a={a} b={b} />;
    case "sticker":
      return <Sticker el={el} dur={dur} a={a} b={b} />;
    case "list":
      return <ListCard el={el} dur={dur} a={a} />;
    case "timeline":
      return <Timeline el={el} dur={dur} a={a} />;
  }
};

const defaultLayer = (el: ProElement) =>
  el.layer ?? (el.type === "sticker" || el.type === "gauge" || el.type === "timeline" ? "back" : "front");

export const ProReel: React.FC<ProReelProps> = (p) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const a = p.accent ?? DEFAULTS.accent;
  const b = p.accent2 ?? "#2F5BFF";
  const els = p.elements ?? [];
  const t = frame / fps;

  const layer = (which: "front" | "back") =>
    els
      .map((el, i) => ({ el, i }))
      .filter(({ el }) => defaultLayer(el) === which)
      .map(({ el, i }) => {
        const from = Math.round(el.from * fps);
        const dur = Math.max(1, Math.round((el.to - el.from) * fps));
        return (
          <Sequence key={`${which}${i}`} from={from} durationInFrames={dur} layout="none">
            <El el={el} dur={dur} a={a} b={b} />
          </Sequence>
        );
      });

  // hide captions while a big front word/counter is on screen (cleaner, like pro edits)
  const hideCaps = els.some(
    (el) => (el.type === "bigword" || el.type === "counter") && defaultLayer(el) === "front" && t >= el.from && t < el.to,
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "#000", fontFamily }}>
      {p.video ? <OffthreadVideo src={staticFile(p.video)} style={{ width: "100%", height: "100%" }} /> : null}
      {/* subtle vignette so graphics pop */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, transparent 55%, rgba(0,0,0,0.45) 100%)" }} />
      {layer("back")}
      {p.fg ? <OffthreadVideo src={staticFile(p.fg)} transparent muted style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }} /> : null}
      {layer("front")}

      {p.captions ? (
        <AbsoluteFill style={{ opacity: hideCaps ? 0 : 1 }}>
          <Captions
            src={p.captions}
            accent={a}
            switchEveryMs={p.wordsPerPageMs ?? 900}
            y={p.captionY ?? 0.6}
            fontSize={64}
            maxWidth={900}
            uppercase={false}
            variant="clean"
          />
        </AbsoluteFill>
      ) : null}

      {p.logo ? (
        <div style={{ position: "absolute", left: 50, top: 90, display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ width: 72, height: 72, borderRadius: 20, background: a, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Icon name="mic" size={46} color="#111" stroke={2.2} />
          </div>
          <div style={{ fontWeight: 900, fontSize: 30, lineHeight: 1.05, color: a, whiteSpace: "pre", textShadow: "0 3px 10px rgba(0,0,0,.6)" }}>{p.logo}</div>
        </div>
      ) : null}
      {p.title ? <HookBar text={p.title} a={a} /> : null}
      <div style={{ position: "absolute", left: 0, bottom: 0, height: 8, width: `${(frame / (durationInFrames - 1)) * 100}%`, background: a }} />
    </AbsoluteFill>
  );
};

const HookBar: React.FC<{ text: string; a: string }> = ({ text, a }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame > fps * 3) return null;
  const o = Math.min(1, frame / 5, (fps * 3 - frame) / 6);
  return (
    <div style={{ position: "absolute", left: 60, right: 60, top: 260, textAlign: "center", opacity: o }}>
      <span style={{ background: a, color: "#111", fontWeight: 900, fontSize: 74, lineHeight: 1.25, padding: "6px 22px", borderRadius: 14, boxDecorationBreak: "clone", WebkitBoxDecorationBreak: "clone" }}>{text}</span>
    </div>
  );
};
