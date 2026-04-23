def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] | None = None,
        **kwargs: Unpack[Emu3ProcessorKwargs],
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
        # check if images and text inputs are reversed for BC

        if isinstance(text, str):
            text = [text]
        elif not isinstance(text, list) and not isinstance(text[0], str):
            raise TypeError("Invalid input text. Please provide a string, or a list of strings")

        output_kwargs = self._merge_kwargs(
            Emu3ProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )
        return_for_image_generation = output_kwargs["text_kwargs"].pop("return_for_image_generation", False)
        ratio = output_kwargs["images_kwargs"].pop("ratio", None)
        image_area = output_kwargs["images_kwargs"].pop("image_area", None)

        if return_for_image_generation and images is not None:
            raise ValueError("You should not provide `images` when `return_for_image_generation=True`")

        if not return_for_image_generation and text is None and images is None:
            raise ValueError("You must provide either text or images when `return_for_image_generation=False`")

        image_features = {}
        image_start_tokens = f"{self.image_start_token}"
        image_end_tokens = f"{self.eof_token}{self.image_end_token}"

        # generate text from image + text input, so we add placeholders for image tokens
        if not return_for_image_generation and images is not None:
            image_features = self.image_processor(images, **output_kwargs["images_kwargs"])
            image_sizes = iter(image_features.image_sizes)

            prompt_strings = []
            for sample in text:
                while self.image_token in sample:
                    image_size = next(image_sizes)
                    height, width = image_size
                    height = height // self.downsample_ratio
                    width = width // self.downsample_ratio
                    image_seq_length = height * (width + 1)  # +1 for extra row when converting to BPE in modeling code

                    image_placeholder = f"{image_start_tokens}{height}*{width}{self.fake_token_around_image}{'<placeholder>' * image_seq_length}{image_end_tokens}"
                    sample = sample.replace(self.image_token, image_placeholder, 1)
                    sample = f"{self.bos_token}{sample}"  # add BOS because GPT tokenizer doesn't add it
                prompt_strings.append(sample)
            text = [sample.replace("<placeholder>", self.image_token) for sample in prompt_strings]

        # generate image from text input, so we add begin-of-image tokens from where image generation starts
        elif return_for_image_generation:
            height, width = self.calculate_generate_size(ratio, image_area, self.downsample_ratio)
            image_prompt = f"{image_start_tokens}{height}*{width}{self.fake_token_around_image}"
            text = [f"{self.bos_token}{sample}{image_prompt}" for sample in text]
            image_features["image_sizes"] = [[height, width]] * len(text)

        # else just generate from text-only input, and we do no special treatment for text
        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        return_mm_token_type_ids = output_kwargs["text_kwargs"].pop("return_mm_token_type_ids", False)
        text_inputs = self.tokenizer(text, **output_kwargs["text_kwargs"], return_tensors=None)
        self._check_special_mm_tokens(text, text_inputs, modalities=["image"])

        if return_mm_token_type_ids:
            text_inputs["mm_token_type_ids"] = self.create_mm_token_type_ids(text_inputs["input_ids"])
        return BatchFeature(data={**text_inputs, **image_features}, tensor_type=return_tensors)