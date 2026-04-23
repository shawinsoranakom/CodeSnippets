def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] | None = None,
        **kwargs: Unpack[MllamaProcessorKwargs],
    ) -> BatchFeature:
        r"""
        Returns:
            [`BatchFeature`]: A [`BatchFeature`] with the following fields:

            - **input_ids** -- List of token ids to be fed to a model. Returned when `text` is not `None`.
            - **attention_mask** -- List of indices specifying which tokens should be attended to by the model (when
              `return_attention_mask=True` or if *"attention_mask"* is in `self.model_input_names` and if `text` is not
              `None`).
            - **pixel_values** -- Pixel values to be fed to a model. Returned when `images` is not `None`.
            TODO: add aspect_ratio_ids and aspect_ratio_mask and cross_attention_mask
        """
        if text is None and images is None:
            raise ValueError("You must specify either text or images.")

        output_kwargs = self._merge_kwargs(
            MllamaProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )
        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)

        data = {}
        if text is not None:
            if isinstance(text, str):
                text = [text]
            elif not (isinstance(text, (list, tuple)) and all(isinstance(t, str) for t in text)):
                raise ValueError("Invalid input text. Please provide a string, or a list of strings")
            n_images_in_text = [t.count(self.image_token) for t in text]
            text = [build_string_from_input(text_item, self.bos_token, self.image_token) for text_item in text]
            encoding = self.tokenizer(text, **output_kwargs["text_kwargs"])
            self._check_special_mm_tokens(text, encoding, modalities=["image"])
            n_images_in_ids = [token_ids.count(self.image_token_id) for token_ids in encoding["input_ids"]]
            data.update(encoding)

        n_images_in_images = [0]
        if images is not None:
            images = self.image_processor.fetch_images(images)
            images = make_nested_list_of_images(images)
            n_images_in_images = [len(sample) for sample in images]

        if text is not None:
            if any(batch_img == 0 for batch_img in n_images_in_text) and not all(
                batch_img == 0 for batch_img in n_images_in_text
            ):
                raise ValueError(
                    "If a batch of text is provided, there should be either no images or at least one image per sample"
                )
            if sum(n_images_in_text) > 0 and (
                n_images_in_images != n_images_in_text or n_images_in_ids != n_images_in_images
            ):
                if images is None:
                    raise ValueError("No image were provided, but there are image tokens in the prompt")
                else:
                    add_message = ""
                    if sum(n_images_in_images) == sum(n_images_in_text) and n_images_in_images != n_images_in_text:
                        add_message = "Make sure to pass your images as a nested list, where each sub-list holds images per batch"
                    elif n_images_in_ids != n_images_in_images:
                        add_message = "If you activated truncation with `max_length`, increase the `max_length` so image tokens aren't cropped."

                    raise ValueError(
                        f"The number of image tokens in each text ({n_images_in_text}) should be the same as the "
                        f"number of provided images per batch ({n_images_in_images}). {add_message}"
                    )

        if images is not None:
            image_features = self.image_processor(images, **output_kwargs["images_kwargs"])
            num_tiles = image_features.pop("num_tiles")
            data.update(image_features)

        # Create cross attention mask
        if images is not None and text is not None:
            cross_attention_token_mask = [
                get_cross_attention_token_mask(token_ids, self.image_token_id) for token_ids in encoding["input_ids"]
            ]
            cross_attention_mask = convert_sparse_cross_attention_mask_to_dense(
                cross_attention_token_mask,
                num_tiles=num_tiles,
                max_num_tiles=self.image_processor.max_image_tiles,
                length=max(len(input_ids) for input_ids in encoding["input_ids"]),
            )
            data["cross_attention_mask"] = cross_attention_mask

        return BatchFeature(data=data, tensor_type=return_tensors)