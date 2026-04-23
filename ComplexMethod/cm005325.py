def sample_frames(
        self,
        metadata: VideoMetadata,
        fps: int | float | None = None,
        **kwargs,
    ):
        """
        Args:
            metadata (`VideoMetadata`):
                Metadata of the video containing information about total duration, fps and total number of frames.
            fps (`int` or `float`, *optional*):
                Target frames to sample per second. Defaults to `self.fps`.
        Returns:
            np.ndarray:
                Indices to sample video frames.
        """
        if metadata is None or getattr(metadata, "fps", None) is None:
            raise ValueError(
                "Asked to sample frames per second but no video metadata was provided which is required when sampling in GLM4V. "
                "Please pass in `VideoMetadata` object or set `do_sample_frames=False`"
            )

        total_frames = metadata.total_num_frames
        requested_fps = fps if fps is not None else self.fps

        max_frame_idx = total_frames - 1
        duration = metadata.duration or round(max_frame_idx / metadata.fps) + 1

        if duration <= self.max_duration:
            n = int(math.floor(duration * requested_fps))
            frame_indices = [min(max_frame_idx, int(math.ceil(i * metadata.fps / requested_fps))) for i in range(n)]
        else:
            num_samples = int(self.max_duration * requested_fps)
            if num_samples >= total_frames:
                frame_indices = list(range(total_frames))
            else:
                target_seconds = np.linspace(0, duration, num_samples, endpoint=True)
                frame_indices = [min(max_frame_idx, int(math.ceil(t * metadata.fps))) for t in target_seconds]

        seen, uniq = set(), []
        for idx in frame_indices:
            if idx not in seen:
                seen.add(idx)
                uniq.append(idx)

        if len(uniq) & 1:
            uniq.append(uniq[-1])

        return np.array(uniq)