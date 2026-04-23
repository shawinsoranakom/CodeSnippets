def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] | None = None,
        **kwargs: Unpack[AyaVisionProcessorKwargs],
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
        if text is None:
            raise ValueError("You have to specify text.")

        output_kwargs = self._merge_kwargs(
            AyaVisionProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        if not isinstance(text, (list, tuple)):
            text = [text]

        # Process images
        image_inputs = {}
        if images is not None:
            images = self.image_processor.fetch_images(images)
            images = make_flat_list_of_images(images)
            image_inputs = self.image_processor(images=images, **output_kwargs["images_kwargs"])
            num_patches = image_inputs.pop("num_patches")
            image_index = 0
            processed_text = []
            for prompt in text:
                new_prompt = prompt
                while "<image>" in new_prompt:
                    # Replace the image placeholder with structured image tokens
                    image_tokens = self._prompt_split_image(num_patches[image_index])
                    new_prompt = new_prompt.replace("<image>", image_tokens, 1)
                    image_index += 1
                processed_text.append(new_prompt)

            if image_index != len(images):
                raise ValueError("Number of image placeholders in the prompt does not match the number of images.")

            text = processed_text

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        return_mm_token_type_ids = output_kwargs["text_kwargs"].pop("return_mm_token_type_ids", False)
        text_inputs = self.tokenizer(text, **output_kwargs["text_kwargs"], return_tensors=None)

        if return_mm_token_type_ids:
            text_inputs["mm_token_type_ids"] = self.create_mm_token_type_ids(text_inputs["input_ids"])
        return BatchFeature(data={**text_inputs, **image_inputs}, tensor_type=return_tensors)