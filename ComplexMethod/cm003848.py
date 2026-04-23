def sample_frames(
        self,
        metadata: VideoMetadata,
        num_frames: int | None = None,
        fps: int | float | None = None,
        skip_secs: int | None = 1,
        **kwargs,
    ):
        """
        Video sampling function which:
            - Uses `num_frames` (if provided) or calculates it from `fps` and metadata.
            - Applies a basic center-skip if fewer frames than available, otherwise
                optionally skips `skip_secs` from both the start and end.
            - Uniformly samples the desired number of frames between the start and end indices.

        Args:
            metadata (`VideoMetadata`):
                Metadata of the video containing information about total duration, fps and total number of frames.
            num_frames (`int`, *optional*):
                Maximum number of frames to sample. Defaults to `self.num_frames`.
            fps (`int` or `float`, *optional*):
                Target frames to sample per second. Defaults to `self.fps`.
            skip_secs (`float`, *optional*, defaults to `1`):
                Number of seconds to skip from the start and end if the video is long enough.

        Returns:
            np.ndarray:
                Indices to sample video frames.
        """
        if metadata is None or getattr(metadata, "fps", None) is None:
            raise ValueError(
                "Asked to sample frames per second but no video metadata was provided which is required when sampling in SmolVLM. "
                "Please pass in `VideoMetadata` object or set `do_sample_frames=False`"
            )

        num_frames = num_frames if num_frames is not None else self.num_frames
        fps = fps if fps is not None else self.fps
        total_num_frames = metadata.total_num_frames

        # Step 1) Estimate how many frames we'd sample at `target_fps`, fallback if target_fps <= 0
        estimated_frames = int(round(fps * metadata["duration"]))

        # Step 2) desired_frames
        desired_frames = min(estimated_frames, num_frames)
        if desired_frames < 1:
            desired_frames = 1

        # Step 3) center skip logic
        start_idx = 0
        end_idx = total_num_frames - 1

        if skip_secs > 0 and (metadata["duration"] - 2 * skip_secs) > (num_frames * fps):
            start_idx = int(skip_secs * metadata["fps"])
            end_idx = int(total_num_frames - skip_secs * metadata["fps"])

        start_idx = max(0, start_idx)
        end_idx = min(end_idx, total_num_frames - 1)
        if start_idx >= end_idx:
            start_idx, end_idx = 0, total_num_frames - 1

        indices = np.linspace(start_idx, end_idx, desired_frames, dtype=int)
        indices = np.unique(indices)

        return indices