def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] | None = None,
        **kwargs: Unpack[ChameleonProcessorKwargs],
    ) -> BatchFeature:
        r"""
        Returns:
            [`BatchFeature`]: A [`BatchFeature`] with the following fields:

            - **input_ids** -- List of token ids to be fed to a model. Returned when `text` is not `None`.
            - **attention_mask** -- List of indices specifying which tokens should be attended to by the model (when
              `return_attention_mask=True` or if *"attention_mask"* is in `self.model_input_names` and if `text` is not
              `None`).
            - **pixel_values** -- Pixel values to be fed to a model. Returned when `images` is not `None`.
        """

        if isinstance(text, str):
            text = [text]
        elif not isinstance(text, list) and not isinstance(text[0], str):
            raise TypeError("Invalid input text. Please provide a string, or a list of strings")
        if text is None and images is None:
            raise ValueError("You must provide either text or images")

        output_kwargs = self._merge_kwargs(
            ChameleonProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )
        return_for_text_completion = output_kwargs["text_kwargs"].pop("return_for_text_completion", False)

        # Replace the image token with the expanded image token sequence
        prompt_strings = []
        one_img_tokens = self.image_start_token + (self.image_token * self.image_seq_length) + self.image_end_token
        for sample in text:
            sample = sample.replace(self.image_token, one_img_tokens)
            if not return_for_text_completion:
                sample += self.tokenizer.sep_token  # special Chameleon treatment to add sep for chat mode
            prompt_strings.append(sample)

        image_inputs = {}
        if images is not None:
            image_inputs = self.image_processor(images, **output_kwargs["images_kwargs"])

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        return_mm_token_type_ids = output_kwargs["text_kwargs"].pop("return_mm_token_type_ids", False)
        text_inputs = self.tokenizer(prompt_strings, **output_kwargs["text_kwargs"], return_tensors=None)
        self._check_special_mm_tokens(prompt_strings, text_inputs, modalities=["image"])

        if return_mm_token_type_ids:
            text_inputs["mm_token_type_ids"] = self.create_mm_token_type_ids(text_inputs["input_ids"])
        return BatchFeature(data={**text_inputs, **image_inputs}, tensor_type=return_tensors)