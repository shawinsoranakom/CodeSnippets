def _regularize_videos(self, videos: list["VideoInput"], **kwargs) -> "RegularizedVideoOutput":
        results, fps_per_video, durations, frames_indices = [], [], [], []
        for video in videos:
            frames: list[ImageObject] = []
            if _check_video_is_nested_images(video):
                # we assume already sample frames from videos
                for frame in video:
                    if not is_valid_image(frame) and not isinstance(frame, dict) and not os.path.exists(frame):
                        raise ValueError("Invalid image found in video frames.")

                frames = video
                fps_per_video.append(kwargs.get("video_fps", 2.0))
                durations.append(len(frames) / kwargs.get("video_fps", 2.0))
                frames_indices.append(list(range(len(frames))))
            else:
                container = av.open(video, "r")
                video_stream = next(stream for stream in container.streams if stream.type == "video")
                sample_indices = self._get_video_sample_indices(video_stream, **kwargs)
                original_fps = float(video_stream.average_rate)
                # for qwen3vl video timestamp calculation
                frames_indices.append([idx / original_fps * kwargs.get("video_fps", 2.0) for idx in sample_indices]) # hack usage when do_sample_frames=False
                container.seek(0)
                for frame_idx, frame in enumerate(container.decode(video_stream)):
                    if frame_idx in sample_indices:
                        frames.append(frame.to_image())

                if video_stream.duration is None:
                    fps_per_video.append(kwargs.get("video_fps", 2.0))
                    durations.append(len(frames) / kwargs.get("video_fps", 2.0))
                else:
                    fps_per_video.append(len(sample_indices) / float(video_stream.duration * video_stream.time_base))
                    durations.append(float(video_stream.duration * video_stream.time_base))

            if len(frames) % 2 != 0:
                frames.append(frames[-1])

            frames = self._regularize_images(frames, **kwargs)["images"]
            results.append(frames)

        return {"videos": results, "fps_per_video": fps_per_video, "durations": durations, "frames_indices": frames_indices}