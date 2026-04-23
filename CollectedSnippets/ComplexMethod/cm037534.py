def load_base64(
        self, media_type: str, data: str
    ) -> tuple[npt.NDArray, dict[str, Any]]:
        if media_type.lower() == "video/jpeg":
            load_frame = partial(
                self.image_io.load_base64,
                "image/jpeg",
            )

            if self.num_frames > 0:
                frame_parts = data.split(",", self.num_frames)[: self.num_frames]
            elif self.num_frames == 0:
                raise ValueError("num_frames must be greater than 0 or -1")
            else:
                frame_parts = data.split(",")

            frames = np.stack(
                [np.asarray(load_frame(frame_data)) for frame_data in frame_parts]
            )
            total = int(frames.shape[0])
            fps = float(self.kwargs.get("fps", 1))

            # validate and extract frames_indices
            frames_indices = self.kwargs.get("frames_indices")
            if frames_indices is not None:
                if not (
                    isinstance(frames_indices, list)
                    and all(isinstance(i, int) for i in frames_indices)
                ):
                    raise ValueError("frames_indices must be a list of integers")
                if len(frames_indices) != total:
                    raise ValueError(
                        f"frames_indices length ({len(frames_indices)}) must "
                        f"match number of frames sent ({total})"
                    )
            else:
                frames_indices = list(range(total))

            # validate and extract total_num_frames
            total_num_frames = self.kwargs.get("total_num_frames", total)
            if not isinstance(total_num_frames, int) or total_num_frames < 1:
                raise ValueError("total_num_frames must be a positive integer")
            if total_num_frames < total:
                raise ValueError(
                    f"total_num_frames ({total_num_frames}) must be >= "
                    f"number of frames sent ({total})"
                )

            # validate and extract duration
            duration = self.kwargs.get("duration")
            if duration is not None:
                if not isinstance(duration, (int, float)) or duration < 0:
                    raise ValueError("duration must be a non-negative number")
            else:
                duration = total_num_frames / fps if fps > 0 else 0.0

            metadata = {
                "total_num_frames": total_num_frames,
                "fps": fps,
                "duration": duration,
                "video_backend": "jpeg_sequence",
                "frames_indices": frames_indices,
                "do_sample_frames": self.kwargs.get("do_sample_frames", False),
            }
            return frames, metadata

        return self.load_bytes(pybase64.b64decode(data))