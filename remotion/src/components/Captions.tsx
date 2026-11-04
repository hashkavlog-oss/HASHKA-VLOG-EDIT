import { useEffect, useMemo, useState } from "react";
import {
  AbsoluteFill,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useDelayRender,
  useVideoConfig,
} from "remotion";
import { createTikTokStyleCaptions } from "@remotion/captions";
import type { Caption, TikTokPage } from "@remotion/captions";
import { fontFamily } from "../fonts";

type Props = {
  src: string;
  accent: string;
  switchEveryMs: number;
  y: number;
  fontSize: number;
  maxWidth: number;
  uppercase: boolean;
};

export const Captions: React.FC<Props> = ({ src, switchEveryMs, ...style }) => {
  const [captions, setCaptions] = useState<Caption[] | null>(null);
  const { delayRender, continueRender, cancelRender } = useDelayRender();
  const [handle] = useState(() => delayRender("Loading captions"));
  const { fps } = useVideoConfig();

  useEffect(() => {
    fetch(staticFile(src))
      .then((r) => r.json())
      .then((data: Caption[]) => {
        setCaptions(data);
        continueRender(handle);
      })
      .catch((e) => cancelRender(e));
  }, [src, handle, continueRender, cancelRender]);

  const pages = useMemo(
    () =>
      captions
        ? createTikTokStyleCaptions({
            captions,
            combineTokensWithinMilliseconds: switchEveryMs,
          }).pages
        : [],
    [captions, switchEveryMs],
  );

  return (
    <AbsoluteFill>
      {pages.map((page, i) => {
        const next = pages[i + 1];
        const from = Math.round((page.startMs / 1000) * fps);
        // keep the page on screen until the next one, but hide after long pauses
        const lastToken = page.tokens[page.tokens.length - 1];
        const endMs = Math.min(next ? next.startMs : Infinity, lastToken.toMs + 700);
        const dur = Math.round((endMs / 1000) * fps) - from;
        if (dur <= 0) return null;
        return (
          <Sequence key={i} from={from} durationInFrames={dur} layout="none">
            <CaptionPage page={page} {...style} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const CaptionPage: React.FC<{ page: TikTokPage } & Omit<Props, "src" | "switchEveryMs">> = ({
  page,
  accent,
  y,
  fontSize,
  maxWidth,
  uppercase,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = page.startMs + (frame / fps) * 1000;

  const pop = spring({ frame, fps, config: { damping: 14, stiffness: 220, mass: 0.6 } });
  const scale = interpolate(pop, [0, 1], [0.82, 1]);
  const lift = interpolate(pop, [0, 1], [24, 0]);

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-start",
        alignItems: "center",
        top: `${y * 100}%`,
        transform: `translateY(-50%)`,
        height: "auto",
        bottom: "auto",
      }}
    >
      <div
        style={{
          fontFamily,
          fontWeight: 900,
          fontSize,
          lineHeight: 1.18,
          maxWidth,
          textAlign: "center",
          whiteSpace: "pre-wrap",
          textTransform: uppercase ? "uppercase" : "none",
          transform: `translateY(${lift}px) scale(${scale})`,
          opacity: pop,
          letterSpacing: -0.5,
        }}
      >
        {page.tokens.map((t, i) => {
          const active = t.fromMs <= nowMs && t.toMs > nowMs;
          const spoken = t.fromMs <= nowMs;
          return (
            <span
              key={`${t.fromMs}-${i}`}
              style={{
                color: active ? "#111" : spoken ? "#fff" : "rgba(255,255,255,0.92)",
                backgroundColor: active ? accent : "transparent",
                borderRadius: fontSize * 0.18,
                padding: `0 ${fontSize * 0.08}px`,
                boxDecorationBreak: "clone",
                WebkitBoxDecorationBreak: "clone",
                WebkitTextStroke: active ? "0px" : `${fontSize * 0.09}px #000`,
                paintOrder: "stroke fill",
                textShadow: active ? "none" : `0 ${fontSize * 0.06}px ${fontSize * 0.12}px rgba(0,0,0,0.55)`,
              }}
            >
              {t.text}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
