import { AbsoluteFill, staticFile, useVideoConfig } from "remotion";
import { Video } from "@remotion/media";
import { Captions } from "./components/Captions";
import { HookTitle } from "./components/HookTitle";
import { Overlay } from "./components/Overlay";
import { DEFAULTS, EditProps } from "./types";

/** One component for both 9:16 reels and 16:9 episodes; sizes follow the canvas. */
export const Edit: React.FC<EditProps> = (p) => {
  const { width, height } = useVideoConfig();
  const vertical = height > width;
  const accent = p.accent ?? DEFAULTS.accent;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {p.video ? <Video src={staticFile(p.video)} style={{ width: "100%", height: "100%" }} /> : null}
      {p.captions ? (
        <Captions
          src={p.captions}
          accent={accent}
          switchEveryMs={p.wordsPerPageMs ?? (vertical ? DEFAULTS.wordsPerPageMs : 1800)}
          y={p.captionY ?? (vertical ? 0.68 : 0.84)}
          fontSize={vertical ? 84 : 64}
          maxWidth={vertical ? 940 : width * 0.8}
          uppercase={p.uppercase ?? false}
        />
      ) : null}
      <HookTitle text={p.title} accent={accent} fontSize={vertical ? 76 : 64} />
      <Overlay accent={accent} brand={p.brand} scale={vertical ? 1 : 1.2} />
    </AbsoluteFill>
  );
};
