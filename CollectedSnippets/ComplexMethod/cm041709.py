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
        messages = deepcopy(messages)

        image_processor: BaseImageProcessor = getattr(processor, "image_processor")

        merge_length: int = getattr(image_processor, "merge_size") ** 2
        if self.expand_mm_tokens:
            mm_inputs = self._get_mm_inputs(images, videos, audios, processor)
            image_grid_thw = mm_inputs.get("image_grid_thw", [])
            video_grid_thw = mm_inputs.get("video_grid_thw", [])
        else:
            image_grid_thw = [None] * len(images)
            video_grid_thw = [None] * len(videos)

        image_idx, video_idx = 0, 0
        for message in messages:
            content = message["content"]
            image_token = self.image_token or "<|IMAGE_PLACEHOLDER|>"
            video_token = self.video_token or "<|VIDEO_PLACEHOLDER|>"
            while IMAGE_PLACEHOLDER in content:
                image_seqlen = image_grid_thw[image_idx].prod() // merge_length if self.expand_mm_tokens else 1
                content = content.replace(
                    IMAGE_PLACEHOLDER,
                    f"Picture {image_idx + 1}:<|IMAGE_START|>{image_token * image_seqlen}<|IMAGE_END|>",
                    1,
                )
                image_idx += 1
            while VIDEO_PLACEHOLDER in content:
                video_seqlen = video_grid_thw[video_idx].prod() // merge_length if self.expand_mm_tokens else 1
                content = content.replace(
                    VIDEO_PLACEHOLDER,
                    f"Video {video_idx + 1}:<|VIDEO_START|>{video_token * video_seqlen}<|VIDEO_END|>",
                    1,
                )
                video_idx += 1
            message["content"] = content
        return messages