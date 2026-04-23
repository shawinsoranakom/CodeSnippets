def get_dummy_mm_data(
        self,
        seq_len: int,
        mm_counts: Mapping[str, int],
        mm_options: Mapping[str, BaseDummyOptions],
    ) -> MultiModalDataDict:
        num_images = mm_counts.get("image", 0)
        num_videos = mm_counts.get("video", 0)

        dummy_images = []
        dummy_videos = []

        if num_images > 0:
            target_width, target_height = self.info.get_image_size_with_most_features()

            image_overrides = mm_options.get("image")

            dummy_images = self._get_dummy_images(
                width=target_width,
                height=target_height,
                num_images=num_images,
                overrides=image_overrides,
            )

        if num_videos > 0:
            processor = self.info.get_hf_processor()
            video_size = processor.video_processor.size
            target_num_frames = self.info.get_num_frames_with_most_features(
                seq_len, mm_counts
            )

            video_overrides = mm_options.get("video")

            if video_overrides:
                assert isinstance(video_overrides, VideoDummyOptions)
                num_frames_override = video_overrides.num_frames
                if num_frames_override:
                    if num_frames_override > target_num_frames:
                        logger.warning(
                            "video.num_frames override (%d) exceeds model's "
                            "maximum number of frames (%d), will be ignored",
                            num_frames_override,
                            target_num_frames,
                        )
                    if num_frames_override < 2:
                        logger.warning(
                            "video.num_frames override (%d) cannot be less "
                            "than 2, will be ignored",
                            num_frames_override,
                        )
                    target_num_frames = min(target_num_frames, num_frames_override)

            dummy_videos = self._get_dummy_videos(
                width=video_size["width"],
                height=video_size["height"],
                num_frames=target_num_frames,
                num_videos=num_videos,
            )

        return {
            "image": dummy_images,
            "video": dummy_videos,
        }