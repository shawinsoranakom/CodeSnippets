def get_dummy_mm_data(
        self,
        seq_len: int,
        mm_counts: Mapping[str, int],
        mm_options: Mapping[str, BaseDummyOptions],
    ) -> MultiModalDataDict:
        num_images = mm_counts.get("image", 0)
        num_videos = mm_counts.get("video", 0)
        image_overrides = mm_options.get("image")
        video_overrides = mm_options.get("video")

        target_image_width, target_image_height = (
            self.info.get_image_size_with_most_features()
        )

        # treat videos as special images
        target_num_frames = 2
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
        target_num_frames = max(target_num_frames, 2)

        video_processor = self.info.get_video_processor()

        mm_kwargs = self.info.ctx.get_merged_mm_kwargs({})
        video_size = mm_kwargs.get("size", video_processor.size)
        temporal_patch_size = mm_kwargs.get(
            "temporal_patch_size", video_processor.temporal_patch_size
        )

        # video_max_pixels contains the temporal compression factor,
        # so we divide by 2 to get the maximum number of image pixels.
        video_max_pixels = video_size["longest_edge"]
        target_video_width, target_video_height = (
            self.info.get_image_size_with_most_features(
                max_pixels=video_max_pixels // temporal_patch_size
            )
        )
        target_video_size, _ = self.info._get_vision_info(
            image_width=target_video_width,
            image_height=target_video_height,
            num_frames=target_num_frames,
            image_processor=video_processor,
            mm_kwargs={},
        )
        # NOTE: we need to do this check here since Qwen3-VL resizes video
        # frames depending on how many frames there are.
        target_video_width, target_video_height = (
            target_video_size.width,
            target_video_size.height,
        )
        if video_overrides:
            assert isinstance(video_overrides, VideoDummyOptions)
            width_override = video_overrides.width
            if width_override:
                if width_override > target_video_width:
                    logger.warning(
                        "video.width override (%d) exceeds model's "
                        "maximum width (%d), will be ignored",
                        width_override,
                        target_video_width,
                    )
                target_video_width = min(target_video_width, width_override)
            height_override = video_overrides.height
            if height_override:
                if height_override > target_video_height:
                    logger.warning(
                        "video.height override (%d) exceeds model's "
                        "maximum height (%d), will be ignored",
                        height_override,
                        target_video_height,
                    )
                target_video_height = min(target_video_height, height_override)

        return {
            "image": self._get_dummy_images(
                width=target_image_width,
                height=target_image_height,
                num_images=num_images,
                overrides=image_overrides,
            ),
            "video": self._get_dummy_videos(
                width=target_video_width,
                height=target_video_height,
                num_frames=target_num_frames,
                num_videos=num_videos,
            ),
        }