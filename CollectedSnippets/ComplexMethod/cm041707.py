def _regularize_videos(self, videos: list["VideoInput"], **kwargs) -> "RegularizedVideoOutput":
        r"""Regularizes videos to avoid error. Including reading, resizing and converting."""
        results = []
        durations = []
        for video in videos:
            frames: list[ImageObject] = []
            if _check_video_is_nested_images(video):
                for frame in video:
                    if not is_valid_image(frame) and not isinstance(frame, dict) and not os.path.exists(frame):
                        raise ValueError("Invalid image found in video frames.")
                frames = video
                durations.append(len(frames) / kwargs.get("video_fps", 2.0))
            else:
                container = av.open(video, "r")
                video_stream = next(stream for stream in container.streams if stream.type == "video")
                sample_indices = self._get_video_sample_indices(video_stream, **kwargs)
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

        return {"videos": results, "durations": durations}