def _get_video_second_idx_glm46v(
        self, metadata: dict[str, Any], total_frames: int
    ) -> list[int]:
        video_processor = self.get_video_processor()

        video_fps = metadata["fps"]
        meta_frames = metadata.get("total_num_frames", total_frames)
        max_frame_idx = meta_frames - 1
        duration = metadata.get("duration", round(max_frame_idx / video_fps) + 1)

        do_sample_frames = metadata.get("do_sample_frames", True)
        if not do_sample_frames:
            frame_indices = metadata["frames_indices"]
        else:
            DYNAMIC_FPS_THRES = {30: 3, 300: 1, 2400: 0.5}
            MAX_FRAME_COUNT_DYNAMIC = 640
            MAX_DURATION = 2400

            effective_duration = min(duration, MAX_DURATION)
            if effective_duration <= 30:
                target_fps = DYNAMIC_FPS_THRES[30]
            elif effective_duration <= 300:
                target_fps = DYNAMIC_FPS_THRES[300]
            else:
                target_fps = DYNAMIC_FPS_THRES[2400]

            temporal_patch_size = getattr(video_processor, "temporal_patch_size", 1)
            extract_t = int(effective_duration * target_fps * temporal_patch_size)
            extract_t = min(extract_t, MAX_FRAME_COUNT_DYNAMIC)

            duration_per_frame = 1 / video_fps
            timestamps = [i * duration_per_frame for i in range(meta_frames)]
            max_second = int(duration)

            if meta_frames < extract_t:
                frame_indices = np.linspace(
                    0, meta_frames - 1, extract_t, dtype=int
                ).tolist()
            else:
                frame_indices = []
                current_second = 0.0
                inv_fps = 1 / (temporal_patch_size * target_fps)
                for frame_index in range(meta_frames):
                    if timestamps[frame_index] >= current_second:
                        current_second += inv_fps
                        frame_indices.append(frame_index)
                        if current_second >= max_second:
                            break

            if len(frame_indices) < extract_t:
                if len(frame_indices) == 0:
                    start, end = 0, max(meta_frames - 1, 0)
                else:
                    start, end = frame_indices[0], frame_indices[-1]
                frame_indices = np.linspace(start, end, extract_t, dtype=int).tolist()
            elif len(frame_indices) > extract_t:
                frame_indices = np.linspace(
                    0, meta_frames - 1, extract_t, dtype=int
                ).tolist()

        seen, uniq = set(), []
        for idx in frame_indices:
            if idx not in seen:
                seen.add(idx)
                uniq.append(idx)

        if len(uniq) & 1:
            uniq.append(uniq[-1])

        frame_indices = uniq
        full_second_idxs = [int(idx / video_fps) for idx in frame_indices]
        timestamps_list = full_second_idxs[::2]
        selected_timestamps = []
        for idx in range(len(timestamps_list)):
            selected_timestamps.append(timestamps_list[idx])
        return selected_timestamps