def __call__(
        self,
        images: ImageInput | list[ImageInput] | list[list[ImageInput]] | None = None,
        text: TextInput | list[TextInput] | None = None,
        **kwargs: Unpack[Lfm2VlProcessorKwargs],
    ) -> BatchEncoding:
        if text is None and images is None:
            raise ValueError("You must provide one of `text` or `images`.")

        if images is not None and text is None:
            raise ValueError(
                "You must provide `text` when `images` is provided. Minimal text consists of a single image token."
            )

        output_kwargs = self._merge_kwargs(
            Lfm2VlProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        if isinstance(text, str):
            text = [text]
        elif not isinstance(text, list) and not isinstance(text[0], str):
            raise TypeError("Invalid input text. Please provide a string, or a list of strings")

        n_images_in_text = [sample.count(self.image_token) for sample in text]
        if sum(n_images_in_text) > 0 and images is None:
            raise ValueError(f"We detected {sum(n_images_in_text)} tokens in the text but no images were passed")

        inputs = {}
        use_image_special_tokens = output_kwargs["text_kwargs"].pop("use_image_special_tokens")

        if images is not None:
            images = self.image_processor.fetch_images(images)
            batched_images = make_nested_list_of_images(images)
            vision_inputs = self.image_processor(batched_images, **output_kwargs["images_kwargs"])

            n_images_in_images = [len(sublist) for sublist in batched_images]
            if n_images_in_images != n_images_in_text:
                raise ValueError(
                    f"The number of images in the text {n_images_in_text} and images {n_images_in_images} should be the same."
                )

            text = self.expand_text_with_placeholders(
                text,
                batched_images,
                image_rows=vision_inputs.pop("image_rows"),
                image_cols=vision_inputs.pop("image_cols"),
                image_sizes=vision_inputs.pop("image_sizes"),
                use_image_special_tokens=use_image_special_tokens,
                **output_kwargs["images_kwargs"],
            )
            inputs.update(vision_inputs)

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)

        text_inputs = self.tokenizer(text, **output_kwargs["text_kwargs"])
        inputs.update(text_inputs)

        return BatchFeature(inputs, tensor_type=return_tensors)