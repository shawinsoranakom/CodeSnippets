def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        **kwargs: Unpack[LightOnOcrProcessorKwargs],
    ) -> BatchFeature:
        if images is None and text is None:
            raise ValueError("You must provide either text or images")
        output_kwargs = self._merge_kwargs(
            LightOnOcrProcessorKwargs,
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

        if image_inputs.get("pixel_values") is not None:
            image_sizes_iter = iter(image_inputs["image_sizes"])
            prompt_strings = []

            for sample in text:
                replace_strings = []

                while self.image_token in sample:
                    image_height, image_width = next(image_sizes_iter)
                    num_height_tokens = image_height // self.effective_patch_size
                    num_width_tokens = image_width // self.effective_patch_size
                    num_patches = num_height_tokens * num_width_tokens

                    replace_str = self.image_token * num_patches
                    replace_strings.append(replace_str)

                    sample = sample.replace(self.image_token, "<placeholder>", 1)

                while "<placeholder>" in sample:
                    replace_str = replace_strings.pop(0)
                    sample = sample.replace("<placeholder>", replace_str, 1)

                prompt_strings.append(sample)
        else:
            prompt_strings = text

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        return_mm_token_type_ids = output_kwargs["text_kwargs"].pop("return_mm_token_type_ids", False)
        text_inputs = self.tokenizer(prompt_strings, **output_kwargs["text_kwargs"], return_tensors=None)
        self._check_special_mm_tokens(prompt_strings, text_inputs, modalities=["image"])

        if return_mm_token_type_ids:
            text_inputs["mm_token_type_ids"] = self.create_mm_token_type_ids(text_inputs["input_ids"])
        return BatchFeature(data={**text_inputs, **image_inputs}, tensor_type=return_tensors)