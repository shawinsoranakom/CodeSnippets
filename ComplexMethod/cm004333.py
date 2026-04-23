def _prepare_input_videos(
        self,
        videos: VideoInput,
        input_data_format: str | ChannelDimension | None = None,
        device: str | None = None,
        video_metadata: list[VideoMetadata] | None = None,
        draw_on_frames: bool = True,
    ) -> list["torch.Tensor"]:
        """
        Prepare the input videos for processing.
        """
        processed_videos = []
        for video, metadata in zip(videos, video_metadata):
            # Check for attributes that are necessary to draw timestamps on frames
            if draw_on_frames:
                if metadata is None:
                    raise ValueError("Need video metadata to process videos in Ernie 4.5 VL using `draw_on_frames`")
                elif metadata.fps is None:
                    metadata.fps = 24
                    logger.warning_once(
                        "Could not infer the fps of a video due to the metadata not being available, "
                        "defaulting to `24`. Please provide `video_metadata` for more accurate results."
                    )

            # `make_batched_videos` always returns a 4D array per video
            if isinstance(video, np.ndarray):
                # not using F.to_tensor as it doesn't handle (C, H, W) numpy arrays
                video = torch.from_numpy(video).contiguous()

            # Infer the channel dimension format if not provided
            if input_data_format is None:
                input_data_format = infer_channel_dimension_format(video)

            if input_data_format == ChannelDimension.LAST:
                video = video.permute(0, 3, 1, 2).contiguous()

            # specific to ernie, draws timestamps on each frame (if enabled)
            if draw_on_frames:
                if is_tracing(video):
                    raise RuntimeError(
                        "Using `torch.compile` is not compatible with drawing on frames. "
                        "Either don't use `torch.compile` or don't draw on frames via the kwarg `draw_on_frames=False`."
                    )

                for idx, frame in enumerate(video):
                    video[idx] = self._render_image_with_timestamp(
                        frame, self._convert_timestamp(metadata.timestamps[idx])
                    )

            # last frame is copied if uneven (mitigating issues for temporal patch size)
            if video.shape[0] % 2 != 0:
                video = torch.cat((video, video[-1].detach().clone()[None, ...]), dim=0)

            if device is not None:
                video = video.to(device)

            processed_videos.append(video)
        return processed_videos