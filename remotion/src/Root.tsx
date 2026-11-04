import { CalculateMetadataFunction, Composition } from "remotion";
import { Edit } from "./Edit";
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

export const RemotionRoot: React.FC = () => (
  <>
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
