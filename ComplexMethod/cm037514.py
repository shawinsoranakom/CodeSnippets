def get_target_fps(
        cls,
        video_fps: float,
        max_frames: int,
        total_frames: int,
        frame_sample_mode: str,
        candidate_target_fps: list[float],
    ) -> float | None:
        """
        Get the target fps that best spans the videoand has the most frames sampled
        """
        num_frames_sampled = 0
        selected_target_fps = None
        for target_fps in candidate_target_fps:
            step_size = max(int(video_fps / target_fps), 1)
            num_frames_sampled_at_fps = int(total_frames / step_size)
            if num_frames_sampled == 0:
                if (
                    "uniform" in frame_sample_mode
                    and num_frames_sampled_at_fps > max_frames
                ):
                    break
                selected_target_fps = target_fps
                num_frames_sampled = num_frames_sampled_at_fps

            else:
                # the candidate sampling fps increases so frame count can't decrease
                assert num_frames_sampled <= num_frames_sampled_at_fps
                if num_frames_sampled_at_fps > max_frames:
                    # choose the sampling fps that spans the video
                    continue

                elif num_frames_sampled_at_fps > num_frames_sampled:
                    # both are less than max_frames; choose the one with higher
                    # density of frames sampled
                    selected_target_fps = target_fps
                    num_frames_sampled = num_frames_sampled_at_fps
        return selected_target_fps