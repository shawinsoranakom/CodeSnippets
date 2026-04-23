def get_candidate_target_fps(
        cls,
        video_fps: float,
        sampling_fps: float,
        max_fps: float = 8.0,
    ) -> list[float]:
        """
        Return the subset of `video_fps` factors that remain multiples
        of `sampling_fps`.

        Examples:
            >>> get_candidate_target_fps(video_fps=6, sampling_fps=2)
            [2, 6]
            >>> get_candidate_target_fps(video_fps=5, sampling_fps=1)
            [1, 5]
            >>> get_candidate_target_fps(video_fps=2, sampling_fps=2)
            [2]
            >>> get_candidate_target_fps(video_fps=5, sampling_fps=2)
            Traceback (most recent call last):
                ...
            ValueError: sampling_fps=2 must divide video_fps=5 to produce
                consistent frame steps.
        """
        video_fps = int(video_fps)
        sampling_fps = int(sampling_fps)
        max_fps = int(max_fps)

        if sampling_fps is None:
            raise ValueError("sampling_fps must be provided")
        if video_fps <= 0 or sampling_fps <= 0:
            raise ValueError(
                "video_fps and sampling_fps must be positive "
                f"(got {video_fps}, {sampling_fps})"
            )
        if video_fps % sampling_fps != 0:
            raise ValueError(
                f"sampling_fps={sampling_fps} must divide video_fps={video_fps}."
            )

        candidates = []
        for candidate in range(sampling_fps, video_fps + 1, sampling_fps):
            if candidate > max_fps:
                break
            if video_fps % candidate == 0:
                candidates.append(float(candidate))

        return candidates