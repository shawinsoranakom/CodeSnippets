def _decode_and_sample_videos(
        self,
        videos: VideoInput,
        video_metadata: VideoMetadata | dict,
        do_sample_frames: bool | None = None,
        sample_indices_fn: Callable | None = None,
    ) -> list["torch.Tensor"]:
        """
        Decode input videos and sample frames if needed.
        """
        videos = make_batched_videos(videos)
        video_metadata = make_batched_metadata(videos, video_metadata=video_metadata)

        # Only sample frames if an array video is passed, otherwise first decode -> then sample
        if is_valid_video(videos[0]) and do_sample_frames:
            sampled_videos = []
            sampled_metadata = []
            for video, metadata in zip(videos, video_metadata):
                indices = sample_indices_fn(metadata=metadata)
                metadata.frames_indices = indices
                sampled_videos.append(video[indices])
                sampled_metadata.append(metadata)
            videos = sampled_videos
            video_metadata = sampled_metadata
        elif not is_valid_video(videos[0]):
            if isinstance(videos[0], list):
                # Videos sometimes are passed as a list of image URLs, especially through templates
                videos = [
                    torch.stack([self.process_image(image) for image in images], dim=0)
                    for images in self.fetch_images(videos)
                ]
                if do_sample_frames:
                    raise ValueError(
                        "Sampling frames from a list of images is not supported! Set `do_sample_frames=False`."
                    )
            else:
                videos, video_metadata = self.fetch_videos(videos, sample_indices_fn=sample_indices_fn)

        return videos, video_metadata