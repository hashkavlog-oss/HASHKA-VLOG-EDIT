import { CalculateMetadataFunction, Composition } from "remotion";
import { Edit } from "./Edit";
import { InfoReel, InfoReelProps } from "./InfoReel";
import { DEFAULTS, EditProps } from "./types";

const calculateMetadata: CalculateMetadataFunction<EditProps> = ({ props }) => ({
  durationInFrames: Math.max(1, Math.round(props.durationInSeconds * DEFAULTS.fps)),
});

const demo: EditProps = {
  video: "",
  captions: "demo/captions.json",
  title: "Сэтгэл түгшилтийг яаж даван туулах вэ?",
  durationInSeconds: 8,
  brand: "@hashka",
};

const infoMeta: CalculateMetadataFunction<InfoReelProps> = ({ props }) => ({
  durationInFrames: Math.max(1, Math.round(props.durationInSeconds * DEFAULTS.fps)),
});

const infoDemo: InfoReelProps = {
  ...demo,
  show: "Hashka's podcast",
  cards: [
    { from: 3.4, to: 8, icon: "brain", kicker: "Сэдэв", title: "Сэтгэл түгшил гэж юу вэ?", points: ["Айдас ба санаа зовнил", "Биеийн хариу урвал"] },
  ],
  pops: [{ at: 4, label: "Улс төр", icon: "vote" }],
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="InfoReel"
      component={InfoReel}
      fps={DEFAULTS.fps}
      width={1080}
      height={1920}
      durationInFrames={240}
      defaultProps={infoDemo}
      calculateMetadata={infoMeta}
    />
    <Composition
      id="Reel"
      component={Edit}
      fps={DEFAULTS.fps}
      width={1080}
      height={1920}
      durationInFrames={240}
      defaultProps={demo}
      calculateMetadata={calculateMetadata}
    />
    <Composition
      id="Wide"
      component={Edit}
      fps={DEFAULTS.fps}
      width={1920}
      height={1080}
      durationInFrames={240}
      defaultProps={demo}
      calculateMetadata={calculateMetadata}
    />
  </>
);
