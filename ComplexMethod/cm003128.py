def __call__(
        self,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        images: ImageInput | None = None,
        videos: VideoInput | None = None,
        audio: AudioInput | None = None,
        **kwargs: Unpack[Qwen2_5OmniProcessorKwargs],
    ) -> BatchFeature:
        if text is None:
            raise ValueError("You need to specify either a `text` input to process.")

        output_kwargs = self._merge_kwargs(
            Qwen2_5OmniProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        seconds_per_chunk = output_kwargs["videos_kwargs"].pop("seconds_per_chunk")
        position_id_per_seconds = output_kwargs["videos_kwargs"].pop("position_id_per_seconds")
        use_audio_in_video = output_kwargs["videos_kwargs"].pop("use_audio_in_video")

        if audio is not None:
            output_kwargs["audio_kwargs"]["padding"] = "max_length"  # Support "max_length" padding only here
            audio_inputs = self.feature_extractor(audio, **output_kwargs["audio_kwargs"])
            audio_inputs["feature_attention_mask"] = audio_inputs.pop(
                "attention_mask"
            )  # rename feature_attention_mask to prevent conflicts later on
            audio_inputs["input_features"] = audio_inputs.pop(
                "input_features"
            )  # rename input_features to prevent conflicts later on
            input_lengths = (audio_inputs["feature_attention_mask"].sum(-1) - 1) // 2 + 1
            audio_lengths = iter((input_lengths - 2) // 2 + 1)
        else:
            audio_inputs = {}
            audio_lengths = iter([])

        if images is not None:
            images_inputs = self.image_processor(images=images, **output_kwargs["images_kwargs"])
            image_grid_thw = iter(images_inputs["image_grid_thw"])
        else:
            images_inputs = {}
            image_grid_thw = iter([])

        if videos is not None:
            videos_inputs = self.video_processor(videos=videos, **output_kwargs["videos_kwargs"])

            fps = output_kwargs["videos_kwargs"].get("fps", 2.0)
            video_grid_thw = videos_inputs["video_grid_thw"]
            second_per_grid_ts = [self.video_processor.temporal_patch_size / fps] * len(video_grid_thw)
            videos_inputs["video_second_per_grid"] = second_per_grid_ts

            video_grid_thw = iter(video_grid_thw)
            video_second_per_grid = iter(second_per_grid_ts)
        else:
            videos_inputs = {}
            video_grid_thw = iter([])
            video_second_per_grid = iter([])

        if not isinstance(text, list):
            text = [text]

        if images is not None or videos is not None or audio is not None:
            text = self.replace_multimodal_special_tokens(
                text,
                audio_lengths,
                image_grid_thw,
                video_grid_thw,
                video_second_per_grid=video_second_per_grid,
                use_audio_in_video=use_audio_in_video,
                position_id_per_seconds=position_id_per_seconds,
                seconds_per_chunk=seconds_per_chunk,
            )

        texts_inputs = self.tokenizer(text, **output_kwargs["text_kwargs"])

        return BatchFeature(
            data={**texts_inputs, **images_inputs, **videos_inputs, **audio_inputs},
            tensor_type=kwargs.get("return_tensors"),
        )