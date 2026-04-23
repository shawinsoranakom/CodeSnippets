def sample_frames(
        self,
        metadata: VideoMetadata,
        min_frames: int | None = None,
        max_frames: int | None = None,
        num_frames: int | None = None,
        fps: int | float | None = None,
        **kwargs,
    ):
        if fps is not None and num_frames is not None:
            raise ValueError("`num_frames` and `fps` are mutually exclusive arguments, please use only one!")

        num_frames = num_frames if num_frames is not None else self.num_frames
        min_frames = min_frames if min_frames is not None else self.min_frames
        max_frames = max_frames if max_frames is not None else self.max_frames
        total_num_frames = metadata.total_num_frames

        if num_frames is not None:
            if num_frames < min_frames or num_frames > max_frames:
                raise ValueError(f"`num_frames` must be {min_frames} <= x <= {max_frames}. Got {num_frames} instead.")
        else:
            if fps is not None and (metadata is None or metadata.fps is None):
                raise ValueError(
                    "Asked to sample `fps` frames per second but no video metadata was provided which is required when sampling with `fps`. "
                    "Please pass in `VideoMetadata` object or use a fixed `num_frames` per input video"
                )
            num_frames = total_num_frames / metadata.fps * fps if fps is not None else total_num_frames
            num_frames = min(max(num_frames, min_frames), max_frames, total_num_frames)

        if num_frames > total_num_frames:
            raise ValueError(
                f"Video can't be sampled. The inferred `num_frames={num_frames}` exceeds `total_num_frames={total_num_frames}`. "
                "Decrease `num_frames` or `fps` for sampling."
            )

        indices = torch.arange(0, total_num_frames, total_num_frames / num_frames).int()

        return indices