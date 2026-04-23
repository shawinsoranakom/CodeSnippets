def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        **kwargs: Unpack[LlavaNextProcessorKwargs],
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
            raise ValueError("You have to specify at least images or text.")

        output_kwargs = self._merge_kwargs(
            LlavaNextProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )
        if images is not None:
            image_inputs = self.image_processor(images, **output_kwargs["images_kwargs"])
        else:
            image_inputs = {}

        if isinstance(text, str):
            text = [text]
        elif not isinstance(text, list) and not isinstance(text[0], str):
            raise TypeError("Invalid input text. Please provide a string, or a list of strings")

        prompt_strings = text
        if image_inputs:
            image_sizes = iter(image_inputs["image_sizes"])
            height, width = get_image_size(to_numpy_array(image_inputs["pixel_values"][0][0]))
            prompt_strings = []
            for sample in text:
                while self.image_token in sample:
                    image_size = next(image_sizes)
                    if not isinstance(image_size, (list, tuple)):
                        # cast to list to avoid numerical precision errors when calculating unpadding
                        image_size = image_size.tolist()
                    orig_height, orig_width = image_size
                    num_image_tokens = self._get_number_of_features(orig_height, orig_width, height, width)
                    if self.vision_feature_select_strategy == "default":
                        num_image_tokens -= 1
                    sample = sample.replace(self.image_token, "<placeholder>" * num_image_tokens, 1)
                prompt_strings.append(sample)
            prompt_strings = [sample.replace("<placeholder>", self.image_token) for sample in prompt_strings]

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        return_mm_token_type_ids = output_kwargs["text_kwargs"].pop("return_mm_token_type_ids", None)
        text_inputs = self.tokenizer(prompt_strings, **output_kwargs["text_kwargs"])
        self._check_special_mm_tokens(prompt_strings, text_inputs, modalities=["image"])

        if return_mm_token_type_ids:
            text_inputs["mm_token_type_ids"] = self.create_mm_token_type_ids(text_inputs["input_ids"])
        return BatchFeature(data={**text_inputs, **image_inputs}, tensor_type=return_tensors)