def process_messages(
        self,
        messages: list[dict[str, str]],
        images: list["ImageInput"],
        videos: list["VideoInput"],
        audios: list["AudioInput"],
        processor: Optional["MMProcessor"],
    ) -> list[dict[str, str]]:
        self._validate_input(processor, images, videos, audios)
        self._validate_messages(messages, images, videos, audios)
        num_image_tokens, num_video_tokens = 0, 0
        messages = deepcopy(messages)
        image_processor: BaseImageProcessor = getattr(processor, "image_processor")
        video_processor: BaseImageProcessor = getattr(processor, "video_processor")

        image_merge_length: int = getattr(image_processor, "merge_size") ** 2
        video_merge_length: int = getattr(video_processor, "merge_size") ** 2
        if self.expand_mm_tokens:
            mm_inputs = self._get_mm_inputs(images, videos, audios, processor)
            image_grid_thw = mm_inputs.get("image_grid_thw", [])
            video_grid_thw = mm_inputs.get("video_grid_thw", [])
            num_frames = video_grid_thw[0][0] if len(video_grid_thw) > 0 else 0  # hard code for now
            video_metadata = mm_inputs.get("video_metadata", [])

        else:
            image_grid_thw = [None] * len(images)
            video_grid_thw = [None] * len(videos)
            num_frames = 0
            timestamps = [0]

        for idx, message in enumerate(messages):
            content = message["content"]
            while IMAGE_PLACEHOLDER in content:
                image_seqlen = (
                    image_grid_thw[num_image_tokens].prod() // image_merge_length if self.expand_mm_tokens else 1
                )
                content = content.replace(
                    IMAGE_PLACEHOLDER,
                    f"{self.vision_bos_token}{self.image_token * image_seqlen}{self.vision_eos_token}",
                    1,
                )
                num_image_tokens += 1

            while VIDEO_PLACEHOLDER in content:
                if self.expand_mm_tokens:
                    metadata = video_metadata[idx]
                    timestamps = processor._calculate_timestamps(
                        metadata.frames_indices,
                        metadata.fps,
                        video_processor.merge_size,
                    )
                    video_structure = ""
                    for frame_index in range(num_frames):
                        video_seqlen = (
                            video_grid_thw[num_video_tokens][1:].prod() // video_merge_length
                            if self.expand_mm_tokens
                            else 1
                        )
                        timestamp_sec = timestamps[frame_index]
                        frame_structure = (
                            f"<{timestamp_sec:.1f} seconds>"
                            f"{self.vision_bos_token}{self.video_token * video_seqlen}{self.vision_eos_token}"
                        )
                        video_structure += frame_structure
                else:
                    video_structure = f"{self.vision_bos_token}{self.video_token}{self.vision_eos_token}"

                content = content.replace(VIDEO_PLACEHOLDER, video_structure, 1)
                num_video_tokens += 1

            message["content"] = content

        return messages