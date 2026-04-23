def get_frame_count(self) -> int:
        """
        Returns the number of frames in the video without materializing them as
        torch tensors.
        """
        if isinstance(self.__file, io.BytesIO):
            self.__file.seek(0)

        with av.open(self.__file, mode="r") as container:
            video_stream = self._get_first_video_stream(container)
            # 1. Prefer the frames field if available and usable
            if (
                video_stream.frames
                and video_stream.frames > 0
                and not self.__start_time
                and not self.__duration
            ):
                return int(video_stream.frames)

            # 2. Try to estimate from duration and average_rate using only metadata
            if (
                getattr(video_stream, "duration", None) is not None
                and getattr(video_stream, "time_base", None) is not None
                and video_stream.average_rate
            ):
                raw_duration = float(video_stream.duration * video_stream.time_base)
                if self.__start_time < 0:
                    duration_from_start = min(raw_duration, -self.__start_time)
                else:
                    duration_from_start = raw_duration - self.__start_time
                duration_seconds = min(self.__duration, duration_from_start)
                estimated_frames = int(round(duration_seconds * float(video_stream.average_rate)))
                if estimated_frames > 0:
                    return estimated_frames

            # 3. Last resort: decode frames and count them (streaming)
            if self.__start_time < 0:
                start_time = max(self._get_raw_duration() + self.__start_time, 0)
            else:
                start_time = self.__start_time
            frame_count = 1
            start_pts = int(start_time / video_stream.time_base)
            end_pts = int((start_time + self.__duration) / video_stream.time_base)
            container.seek(start_pts, stream=video_stream)
            frame_iterator = (
                container.decode(video_stream)
                if video_stream.codec.capabilities & 0x100
                else container.demux(video_stream)
            )
            for frame in frame_iterator:
                if frame.pts >= start_pts:
                    break
            else:
                raise ValueError(f"Could not determine frame count for file '{self.__file}'\nNo frames exist for start_time {self.__start_time}")
            for frame in frame_iterator:
                if frame.pts >= end_pts:
                    break
                frame_count += 1
            return frame_count