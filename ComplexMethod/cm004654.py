def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] | None = None,
        **kwargs: Unpack[Cohere2VisionProcessorKwargs],
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
        elif not isinstance(text, (list, tuple)):
            text = [text]

        output_kwargs = self._merge_kwargs(
            Cohere2VisionProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        # Process images
        image_inputs = {}
        if images is not None:
            image_inputs = self.image_processor(images=images, **output_kwargs["images_kwargs"])
            batch_num_patches = iter(image_inputs.pop("num_patches"))
            processed_text = []
            for sample in text:
                while self.image_token in sample:
                    num_patches = next(batch_num_patches)
                    img_patches_per_tile = int(self.patch_size**2)

                    img_string = f"{self.boi_token}"
                    for idx in range(1, num_patches):
                        img_string += "<placeholder>" * img_patches_per_tile + self.img_line_break_token
                    img_string += "<placeholder>" * img_patches_per_tile + self.img_line_break_token
                    img_string += f"{self.eoi_token}"

                    sample = sample.replace(self.image_token, img_string, 1)
                processed_text.append(sample)
            text = [sample.replace("<placeholder>", self.image_token) for sample in processed_text]

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        return_mm_token_type_ids = output_kwargs["text_kwargs"].pop("return_mm_token_type_ids", False)
        text_inputs = self.tokenizer(text, **output_kwargs["text_kwargs"], return_tensors=None)

        if return_mm_token_type_ids:
            text_inputs["mm_token_type_ids"] = self.create_mm_token_type_ids(text_inputs["input_ids"])
        return BatchFeature(data={**text_inputs, **image_inputs}, tensor_type=return_tensors)