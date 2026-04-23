def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        videos: VideoInput | None = None,
        **kwargs: Unpack[PerceptionLMProcessorKwargs],
    ) -> BatchFeature:
        r"""
        Returns:
            [`BatchFeature`]: A [`BatchFeature`] with the following fields:

            - **input_ids** -- List of token ids to be fed to a model. Returned when `text` is provided.
            - **attention_mask** -- List of indices specifying which tokens should be attended to by the model (when
              `return_attention_mask=True` or if *"attention_mask"* is in `self.model_input_names` and if `text` is provided).
            - **pixel_values** -- Pixel values to be fed to a model. Returned when `images` is provided.
            - **pixel_values_videos** -- Video pixel values to be fed to a model. Returned when `videos` is provided.
        """
        if text is None:
            raise ValueError(
                "You have to specify at least `text` input. Optionally, you can also specify `images` or `videos`."
            )

        output_kwargs = self._merge_kwargs(
            PerceptionLMProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )
        if images is not None:
            image_inputs = self.image_processor(images=images, **output_kwargs["images_kwargs"])
        else:
            image_inputs = {}

        if videos is not None:
            videos_inputs = self.video_processor(videos, **output_kwargs["videos_kwargs"])
        else:
            videos_inputs = {}

        if isinstance(text, str):
            text = [text]
        elif not isinstance(text, list) and not isinstance(text[0], str):
            raise TypeError("Invalid input text. Please provide a string, or a list of strings")

        # try to expand inputs in processing if we have the necessary parts
        prompt_strings = []

        pixel_values = iter(image_inputs.get("pixel_values", []))
        pixel_values_videos = iter(videos_inputs.get("pixel_values_videos", []))
        for sample in text:
            # Replace the media token with the expanded media token sequence
            sample = self._expand_media_tokens(sample, self.tokenizer.image_token, pixel_values)
            sample = self._expand_media_tokens(sample, self.tokenizer.video_token, pixel_values_videos)
            prompt_strings.append(sample)

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        return_mm_token_type_ids = output_kwargs["text_kwargs"].pop("return_mm_token_type_ids", False)
        text_inputs = self.tokenizer(prompt_strings, **output_kwargs["text_kwargs"], return_tensors=None)
        self._check_special_mm_tokens(prompt_strings, text_inputs, modalities=["image", "video"])

        if return_mm_token_type_ids:
            text_inputs["mm_token_type_ids"] = self.create_mm_token_type_ids(text_inputs["input_ids"])
        return BatchFeature(data={**text_inputs, **image_inputs, **videos_inputs}, tensor_type=return_tensors)