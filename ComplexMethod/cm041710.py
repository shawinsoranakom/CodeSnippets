def _regularize_videos(self, videos: list["VideoInput"], **kwargs) -> "RegularizedVideoOutput":
        r"""Regularize videos, also tracking per-video FPS and frame indices for timestamp generation."""
        results, fps_per_video, durations, frames_indices = [], [], [], []
        for video in videos:
            frames: list[ImageObject] = []
            if _check_video_is_nested_images(video):
                frames = video
                fps_per_video.append(kwargs.get("video_fps", 2.0))
                durations.append(len(frames) / kwargs.get("video_fps", 2.0))
                frames_indices.append(list(range(len(frames))))
            else:
                container = av.open(video, "r")
                video_stream = next(stream for stream in container.streams if stream.type == "video")
                sample_indices = self._get_video_sample_indices(video_stream, **kwargs)
                original_fps = float(video_stream.average_rate)
                # for correctly calculate timestamps
                frames_indices.append([idx / original_fps * kwargs.get("video_fps", 2.0) for idx in sample_indices])
                container.seek(0)
                for frame_idx, frame in enumerate(container.decode(video_stream)):
                    if frame_idx in sample_indices:
                        frames.append(frame.to_image())

                if video_stream.duration is None:
                    durations.append(len(frames) / kwargs.get("video_fps", 2.0))
                else:
                    durations.append(float(video_stream.duration * video_stream.time_base))

            frames = self._regularize_images(frames, **kwargs)["images"]
            results.append(frames)

        return {"videos": results, "fps_per_video": fps_per_video, "durations": durations, "frames_indices": frames_indices}