def _sample_frames(
        self,
        total_num_frames: int,
        video_fps: float,
        duration: float,
        frame_sample_mode: str,
        num_frames: int,
        max_fps: int,
        sampling_fps: int,
    ) -> np.ndarray:
        if frame_sample_mode == "uniform_last_frame" and max_fps is not None:
            if total_num_frames <= 2:
                indices = np.arange(total_num_frames).astype(int)
            elif duration > (num_frames - 1) / max_fps:  # -1 to include the last frame
                # uniform fallback
                indices = np.linspace(
                    0,
                    total_num_frames - 1,
                    num=min(num_frames, total_num_frames),
                    endpoint=True,
                ).astype(int)
            else:
                float_indices = np.arange(
                    0.0,
                    stop=total_num_frames - 1,
                    step=float(video_fps / max_fps),
                )
                if np.round(float_indices[-1]) != total_num_frames - 1:
                    float_indices = np.concatenate(
                        [float_indices, [total_num_frames - 1]], axis=0
                    )
                indices = np.round(float_indices).astype(int)
                assert indices[-1] < total_num_frames
                assert len(float_indices) <= num_frames
        elif frame_sample_mode == "uniform_last_frame":
            indices = np.linspace(
                0,
                total_num_frames - 1,
                num=min(num_frames, total_num_frames),
                endpoint=True,
            ).astype(int)
        elif frame_sample_mode == "fps":
            candidate_target_fps = get_candidate_target_fps(video_fps, sampling_fps)
            selected_target_fps = get_target_fps(
                video_fps,
                num_frames,
                total_num_frames,
                frame_sample_mode,
                candidate_target_fps,
            )
            _, indices = get_frame_times_and_chosen_fps(
                selected_target_fps,
                total_num_frames,
                num_frames,
                video_fps,
            )
        else:
            raise NotImplementedError(frame_sample_mode)

        return indices