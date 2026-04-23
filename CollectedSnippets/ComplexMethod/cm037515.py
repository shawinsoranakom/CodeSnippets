def sample_times(
        cls,
        duration: float,
        max_frames: int,
        frame_sample_mode: str,
        max_fps: int | None,
        candidate_target_fps: list[float] | None = None,
        **kwargs,
    ) -> npt.NDArray:
        if frame_sample_mode == "fps":
            assert candidate_target_fps is not None
            # Try larger and larger FPSs until we hit one that can't span the video
            sampling_fps = candidate_target_fps[0]
            for candidate_fps in candidate_target_fps[1:]:
                if max_frames / candidate_fps < duration:
                    break
                sampling_fps = candidate_fps
            times = np.arange(0, max_frames) / sampling_fps
            times = times[times < duration]
            return times
        elif frame_sample_mode == "uniform_last_frame":
            if max_fps is not None:
                max_duration = (
                    max_frames - 1
                ) / max_fps  # -1 to include the last frame
                if max_duration < duration:
                    times = np.linspace(
                        0, duration, num=max_frames, endpoint=True, dtype=np.float64
                    )
                else:
                    times = np.arange(0.0, stop=duration, step=1 / max_fps)
                    times = np.concatenate([times, [duration]], axis=0)
                    assert len(times) <= max_frames
            else:
                times = np.linspace(
                    0, duration, num=max_frames, endpoint=True, dtype=np.float64
                )
            return times
        else:
            raise NotImplementedError(frame_sample_mode)