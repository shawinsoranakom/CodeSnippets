def __call__(
        self,
        images: ImageInput = None,
        text: TextInput
        | PreTokenizedInput
        | list[TextInput]
        | list[PreTokenizedInput] = None,
        audio=None,
        videos=None,
        **kwargs: Unpack[TarsierProcessorKwargs],
    ) -> BatchFeature:
        if images is None and text is None:
            raise ValueError("You have to specify at least one of `images` or `text`.")

        output_kwargs = self._merge_kwargs(
            TarsierProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )
        if images is not None:
            image_inputs = self.image_processor(
                images, **output_kwargs["images_kwargs"]
            )
        else:
            image_inputs = {}

        if isinstance(text, str):
            text = [text]
        elif not isinstance(text, list) and not isinstance(text[0], str):
            raise ValueError(
                "Invalid input text. Please provide a string, or a list of strings"
            )

        # try to expand inputs in processing if we have the necessary parts
        prompt_strings = text
        if image_inputs.get("pixel_values") is not None:
            # Replace the image token with the expanded image token sequence
            pixel_values = image_inputs["pixel_values"]
            height, width = get_image_size(to_numpy_array(pixel_values[0]))
            num_image_tokens = (
                (height // self.patch_size) * (width // self.patch_size + 1)
                + self.num_additional_image_tokens
                + 1
            )
            if self.vision_feature_select_strategy == "default":
                num_image_tokens -= 1

            prompt_strings = []
            for sample in text:
                sample = sample.replace(
                    self.image_token, self.image_token * num_image_tokens
                )
                prompt_strings.append(sample)

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        text_inputs = self.tokenizer(prompt_strings, **output_kwargs["text_kwargs"])
        return BatchFeature(
            data={**text_inputs, **image_inputs}, tensor_type=return_tensors
        )