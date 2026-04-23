def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        **kwargs: Unpack[Florence2ProcessorKwargs],
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
        if images is None and text is None:
            raise ValueError("You have to specify at least one of `images` or `text`.")

        output_kwargs = self._merge_kwargs(
            Florence2ProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        image_inputs = {}
        if images is not None:
            image_inputs = self.image_processor(images, **output_kwargs["images_kwargs"])

        if text is None:
            logger.warning_once("You are using Florence-2 without a text prefix.")
            text = [""] * (1 if not isinstance(images, list) else len(images))
        elif isinstance(text, str):
            text = [text]

        if not isinstance(text, list) or not all(isinstance(token, str) for token in text):
            raise ValueError("`text` must be a string or list of strings.")

        if isinstance(images, list) and len(images) != len(text):
            raise ValueError(f"Number of images ({len(images)}) must match number of texts ({len(text)}).")

        prompt_strings = self._construct_prompts(text)

        # Add image tokens and special tokens if images are provided
        if image_inputs.get("pixel_values") is not None:
            # Replace the image token with the expanded image token sequence
            expanded_image_prompts = []
            for sample in prompt_strings:
                sample = (
                    self.image_token * self.num_image_tokens
                    + self.tokenizer.bos_token
                    + sample
                    + self.tokenizer.eos_token
                )
                expanded_image_prompts.append(sample)
            prompt_strings = expanded_image_prompts

        # Construct and tokenize prompts
        output_kwargs["text_kwargs"].pop("add_special_tokens", None)
        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        return_mm_token_type_ids = output_kwargs["text_kwargs"].pop("return_mm_token_type_ids", False)
        text_inputs = self.tokenizer(
            prompt_strings, **output_kwargs["text_kwargs"], add_special_tokens=False, return_tensors=None
        )
        self._check_special_mm_tokens(prompt_strings, text_inputs, modalities=["image"])

        if return_mm_token_type_ids:
            text_inputs["mm_token_type_ids"] = self.create_mm_token_type_ids(text_inputs["input_ids"])
        return BatchFeature(data={**image_inputs, **text_inputs}, tensor_type=return_tensors)