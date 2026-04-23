def sample_frames(
        self,
        metadata: VideoMetadata,
        temporal_patch_size: int | None = None,
        min_frames: int | None = None,
        max_frames: int | None = None,
        num_frames: int | None = None,
        fps: int | float | None = None,
        **kwargs,
    ):
        """
        Default sampling function which uniformly samples the desired number of frames between 0 and total number of frames.
        If `fps` is passed along with metadata, `fps` frames per second are sampled uniformty. Arguments `num_frames`
        and `fps` are mutually exclusive.

        Args:
            metadata (`VideoMetadata`):
                Metadata of the video containing information about total duration, fps and total number of frames.
            temporal_patch_size (`int`, *optional*):
                The temporal patch size of the vision encoder. Number of sampled frames will be rounded to be divisible by frame factor.
            min_frames (`int`, *optional*):
                The minimum number of frames that can be sampled.
            max_frames (`int`, *optional*):
                The maximum number of frames that can be sampled.
            num_frames (`int`, *optional*):
                Maximum number of frames to sample. Defaults to `self.num_frames`.
            fps (`int` or `float`, *optional*):
                Target frames to sample per second. Defaults to `self.fps`.

        Returns:
            np.ndarray:
                Indices to sample video frames.
        """
        if fps is not None and num_frames is not None:
            raise ValueError("`num_frames` and `fps` are mutually exclusive arguments, please use only one!")

        num_frames = num_frames if num_frames is not None else self.num_frames
        fps = fps if fps is not None else self.fps
        temporal_patch_size = temporal_patch_size if temporal_patch_size is not None else self.temporal_patch_size
        min_frames = min_frames if min_frames is not None else self.min_frames
        max_frames = max_frames if max_frames is not None else self.max_frames
        total_num_frames = metadata.total_num_frames

        # If num_frames is not given but fps is, calculate num_frames from fps
        if num_frames is not None:
            num_frames = round(num_frames / temporal_patch_size) * temporal_patch_size
        elif fps is not None:
            if metadata is None or metadata.fps is None:
                raise ValueError(
                    "Asked to sample `fps` frames per second but no video metadata was provided which is required when sampling with `fps`. "
                    "Please pass in `VideoMetadata` object or use a fixed `num_frames` per input video"
                )
            max_frames = math.floor(min(max_frames, total_num_frames) / temporal_patch_size) * temporal_patch_size
            num_frames = total_num_frames / metadata.fps * fps
            num_frames = min(max(num_frames, min_frames), max_frames, total_num_frames)
            num_frames = math.floor(num_frames / temporal_patch_size) * temporal_patch_size

        if num_frames > total_num_frames:
            raise ValueError(
                f"Video can't be sampled. The inferred `num_frames={num_frames}` exceeds `total_num_frames={total_num_frames}`. "
                "Decrease `num_frames` or `fps` for sampling."
            )

        if num_frames is not None:
            indices = torch.arange(0, total_num_frames, total_num_frames / num_frames).int()
        else:
            indices = torch.arange(0, total_num_frames).int()

        return indices