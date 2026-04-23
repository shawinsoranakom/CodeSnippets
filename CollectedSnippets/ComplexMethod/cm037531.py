def _get_dummy_videos(
        self,
        *,
        width: int,
        height: int,
        num_frames: int,
        num_videos: int,
        overrides: VideoDummyOptions | None = None,
    ) -> list[npt.NDArray]:
        if num_videos == 0:
            return []
        if overrides:
            if overrides.num_frames:
                if overrides.num_frames > num_frames:
                    logger.warning(
                        "video.num_frames override (%d) exceeds model's "
                        "maximum number of frames (%d), will be ignored",
                        overrides.num_frames,
                        num_frames,
                    )
                num_frames = min(num_frames, overrides.num_frames)
            if overrides.width:
                if overrides.width > width:
                    logger.warning(
                        "video.width override (%d) exceeds model's "
                        "maximum width (%d), will be ignored",
                        overrides.width,
                        width,
                    )
                width = min(width, overrides.width)
            if overrides.height:
                if overrides.height > height:
                    logger.warning(
                        "video.height override (%d) exceeds model's "
                        "maximum height (%d), will be ignored",
                        overrides.height,
                        height,
                    )
                height = min(height, overrides.height)
        video = np.full((num_frames, width, height, 3), 255, dtype=np.uint8)
        return [video] * num_videos