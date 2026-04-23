def sample_frames(
        self,
        metadata: VideoMetadata,
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
            num_frames (`int`, *optional*):
                Maximum number of frames to sample. Defaults to `self.num_frames`.
            fps (`int` or `float`, *optional*):
                Target frames to sample per second. Defaults to `self.fps`.

        Returns:
            np.ndarray:
                Indices to sample video frames.
        """
        if fps is not None and num_frames is not None:
            raise ValueError(
                "`num_frames`, `fps`, and `sample_indices_fn` are mutually exclusive arguments, please use only one!"
            )

        num_frames = num_frames if num_frames is not None else self.num_frames
        fps = fps if fps is not None else self.fps
        total_num_frames = metadata.total_num_frames

        # If num_frames is not given but fps is, calculate num_frames from fps
        if num_frames is None and fps is not None:
            if metadata is None or metadata.fps is None:
                raise ValueError(
                    "Asked to sample `fps` frames per second but no video metadata was provided which is required when sampling with `fps`. "
                    "Please pass in `VideoMetadata` object or use a fixed `num_frames` per input video"
                )
            num_frames = int(total_num_frames / metadata.fps * fps)

        if num_frames > total_num_frames:
            raise ValueError(
                f"Video can't be sampled. The `num_frames={num_frames}` exceeds `total_num_frames={total_num_frames}`. "
            )

        if num_frames is not None:
            indices = torch.arange(0, total_num_frames, total_num_frames / num_frames).int()
        else:
            indices = torch.arange(0, total_num_frames).int()
        return indices