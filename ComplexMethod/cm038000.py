def _get_video_second_idx_glm4v(
        self, metadata: dict[str, Any], total_frames: int
    ) -> list[int]:
        video_processor = self.get_video_processor()

        video_fps = metadata.get("fps", video_processor.fps)
        meta_frames = metadata.get("total_num_frames", total_frames)
        max_frame_idx = meta_frames - 1
        duration = metadata.get("duration", round(max_frame_idx / video_fps) + 1)
        do_sample_frames = metadata["do_sample_frames"]
        if not do_sample_frames:
            frame_indices = metadata["frames_indices"]
        else:
            if duration <= video_processor.max_duration:
                n = int(math.floor(duration * video_processor.fps))
                frame_indices = [
                    min(
                        max_frame_idx,
                        int(math.ceil(i * video_fps / video_processor.fps)),
                    )
                    for i in range(n)
                ]
            else:
                num_samples = int(video_processor.max_duration * video_processor.fps)
                if num_samples >= meta_frames:
                    frame_indices = list(range(meta_frames))
                else:
                    target_seconds = np.linspace(
                        0, duration, num_samples, endpoint=True
                    )
                    frame_indices = [
                        min(max_frame_idx, int(math.ceil(t * video_fps)))
                        for t in target_seconds
                    ]

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
        for idx in range(0, len(timestamps_list)):
            selected_timestamps.append(timestamps_list[idx])
        return selected_timestamps