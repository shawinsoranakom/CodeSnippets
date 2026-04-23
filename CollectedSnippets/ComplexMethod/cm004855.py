def __call__(
        self,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        images: ImageInput | None = None,
        **kwargs: Unpack[DeepseekVLHybridProcessorKwargs],
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
        output_kwargs = self._merge_kwargs(
            DeepseekVLHybridProcessorKwargs, tokenizer_init_kwargs=self.tokenizer.init_kwargs, **kwargs
        )
        if text is None and images is None:
            raise ValueError("You must specify either text or images.")

        if text is not None:
            if isinstance(text, str):
                text = [text]
            elif not (isinstance(text, (list, tuple)) and all(isinstance(t, str) for t in text)):
                raise ValueError("Invalid input text. Please provide a string, or a list of strings")

        prompt_strings = []
        one_img_tokens = self.image_token * self.num_image_tokens
        for prompt in text:
            prompt = prompt.replace(self.image_token, one_img_tokens)
            prompt_strings.append(prompt)

        data = self.tokenizer(prompt_strings, **output_kwargs["text_kwargs"])

        # process images if pixel_values are provided
        if images is not None:
            inputs = self.image_processor(images, **output_kwargs["images_kwargs"])
            data["pixel_values"] = inputs["pixel_values"]
            data["high_res_pixel_values"] = inputs["high_res_pixel_values"]

        return BatchFeature(data=data)