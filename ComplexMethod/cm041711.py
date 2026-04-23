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

        boi_token: str = getattr(processor, "boi_token")
        eoi_token: str = getattr(processor, "eoi_token")
        boa_token: str = getattr(processor, "boa_token")
        eoa_token: str = getattr(processor, "eoa_token")
        image_token: str = getattr(processor, "image_token")
        video_token: str = getattr(processor, "video_token")
        audio_token: str = getattr(processor, "audio_token")

        if self.expand_mm_tokens:
            mm_inputs = self._get_mm_inputs(images, videos, audios, processor)
            num_image_soft_tokens: list[int] = list(
                mm_inputs.get("num_soft_tokens_per_image", [getattr(processor, "image_seq_length", 256)] * len(images))
            )
            num_video_soft_tokens: list[int] = list(mm_inputs.get("num_soft_tokens_per_video", [1] * len(videos)))
            video_metadata = mm_inputs.get("video_metadata", [])
        else:
            num_image_soft_tokens = [1] * len(images)
            num_video_soft_tokens = [1] * len(videos)
            video_metadata = [None] * len(videos)

        audio_iter = iter(audios)
        image_iter = iter(num_image_soft_tokens)
        video_iter = iter(zip(num_video_soft_tokens, video_metadata))

        for message in messages:
            content = message["content"]

            while IMAGE_PLACEHOLDER in content:
                n = next(image_iter)
                content = content.replace(IMAGE_PLACEHOLDER, f"{boi_token}{image_token * n}{eoi_token}", 1)

            while VIDEO_PLACEHOLDER in content:
                num_soft_tokens_per_frame, metadata = next(video_iter)
                if self.expand_mm_tokens:
                    timestamp_strs = [f"{int(t // 60):02d}:{int(t % 60):02d}" for t in metadata.timestamps]
                    frame_strs = [f"{ts} {boi_token}{video_token * num_soft_tokens_per_frame}{eoi_token}" for ts in timestamp_strs]
                    video_str = " ".join(frame_strs)
                else:
                    video_str = f"{boi_token}{video_token * num_soft_tokens_per_frame}{eoi_token}"
                content = content.replace(VIDEO_PLACEHOLDER, video_str, 1)

            while AUDIO_PLACEHOLDER in content:
                current_audio = next(audio_iter)
                if self.expand_mm_tokens:
                    num_audio_tokens = processor._compute_audio_num_tokens(current_audio, processor.feature_extractor.sampling_rate)
                    audio_str = f"{boa_token}{audio_token * num_audio_tokens}{eoa_token}"
                else:
                    audio_str = f"{boa_token}{audio_token}{eoa_token}"

                content = content.replace(AUDIO_PLACEHOLDER, audio_str, 1)

            message["content"] = content

        return messages