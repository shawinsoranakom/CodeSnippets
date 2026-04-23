def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] | None = None,
        **kwargs: Unpack[Llama4ProcessorKwargs],
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
            Llama4ProcessorKwargs,
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
            image_height, image_width = image_inputs["pixel_values"][0].shape[-2:]
            num_patches_per_chunk = int(
                (image_height // self.patch_size) * (image_width // self.patch_size) // self.downsample_ratio
            )
            aspect_ratios = image_inputs.pop("aspect_ratios")

            total_placeholders = sum(prompt.count(self.fake_image_token) for prompt in text)
            if total_placeholders != len(images):
                raise ValueError(
                    f"Found {total_placeholders} placeholders across the batch, "
                    f"but have {len(images)} flattened images."
                )

            image_index = 0
            processed_text = []
            for prompt in text:
                placeholder_count = prompt.count(self.fake_image_token)
                if placeholder_count == 0:
                    # do nothing if there is no image
                    processed_text.append(prompt)
                    continue
                prompt_splits = prompt.split(self.fake_image_token)
                new_prompt = []
                for local_image_index, split_part in enumerate(prompt_splits):
                    new_prompt.append(split_part)
                    if local_image_index < placeholder_count:
                        tokens_for_this_image = self._prompt_split_image(
                            aspect_ratios[image_index], num_patches_per_chunk
                        )
                        image_index += 1
                        new_prompt.append(tokens_for_this_image)
                processed_text.append("".join(new_prompt))

            if image_index != len(images):
                raise ValueError("Number of image placeholders in the prompt does not match the number of images.")

            text = processed_text

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        text_inputs = self.tokenizer(text, **output_kwargs["text_kwargs"])
        self._check_special_mm_tokens(text, text_inputs, modalities=["image"])

        return BatchFeature(data={**text_inputs, **image_inputs}, tensor_type=return_tensors)