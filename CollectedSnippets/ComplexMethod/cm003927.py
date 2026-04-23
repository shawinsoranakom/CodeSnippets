def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        **kwargs: Unpack[ColQwen2ProcessorKwargs],
    ) -> BatchFeature:
        r"""
        Returns:
            [`BatchFeature`]: A [`BatchFeature`] with the following fields:

            - **input_ids** -- List of token ids to be fed to a model.
            - **attention_mask** -- List of indices specifying which tokens should be attended to by the model (when
              `return_attention_mask=True` or if *"attention_mask"* is in `self.model_input_names` and if `text` is not
              `None`).
            - **pixel_values** -- Pixel values to be fed to a model. Returned when `images` is not `None`.
        """
        output_kwargs = self._merge_kwargs(
            ColQwen2ProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )
        suffix = output_kwargs["text_kwargs"].pop("suffix", None)

        return_token_type_ids = suffix is not None

        if text is None and images is None:
            raise ValueError("Either text or images must be provided")
        if text is not None and images is not None:
            raise ValueError("Only one of text or images can be processed at a time")

        if images is not None:
            if is_valid_image(images):
                images = [images]
            elif isinstance(images, list) and is_valid_image(images[0]):
                pass
            elif not (isinstance(images, list) and isinstance(images[0], list) and is_valid_image(images[0][0])):
                raise ValueError("images must be an image, list of images or list of list of images")

            texts_doc = [self.visual_prompt_prefix] * len(images)

            image_inputs = self.image_processor(images=images, **output_kwargs["images_kwargs"])
            image_grid_thw = image_inputs["image_grid_thw"]

            if image_grid_thw is not None:
                merge_length = self.image_processor.merge_size**2
                index = 0
                for i in range(len(texts_doc)):
                    while self.image_token in texts_doc[i]:
                        texts_doc[i] = texts_doc[i].replace(
                            self.image_token, "<|placeholder|>" * (image_grid_thw[index].prod() // merge_length), 1
                        )
                        index += 1
                    texts_doc[i] = texts_doc[i].replace("<|placeholder|>", self.image_token)

            text_inputs = self.tokenizer(
                texts_doc,
                return_token_type_ids=False,
                **output_kwargs["text_kwargs"],
            )

            return_data = BatchFeature(data={**text_inputs, **image_inputs})

            # NOTE: The following adjustment ensures correct behavior with DDP on multiple GPUs.
            offsets = return_data["image_grid_thw"][:, 1] * return_data["image_grid_thw"][:, 2]  # (batch_size,)

            # Split the pixel_values tensor into a list of tensors, one per image
            pixel_values = list(
                torch.split(return_data["pixel_values"], offsets.tolist())
            )  # [(num_patches_image_0, pixel_values), ..., (num_patches_image_n, pixel_values)]

            # Pad the list of pixel_value tensors to the same length along the sequence dimension
            return_data["pixel_values"] = torch.nn.utils.rnn.pad_sequence(
                pixel_values, batch_first=True
            )  # (batch_size, max_num_patches, pixel_values)

            if return_token_type_ids:
                labels = return_data["input_ids"].masked_fill(return_data["token_type_ids"] == 0, -100)
                return_data.update({"labels": labels})

            return return_data

        elif text is not None:
            if isinstance(text, str):
                text = [text]
            elif not (isinstance(text, list) and isinstance(text[0], str)):
                raise ValueError("Text must be a string or a list of strings")

            if suffix is None:
                suffix = self.query_augmentation_token * 10

            texts_query: list[str] = []

            for query in text:
                augmented_query = self.query_prefix + query + suffix
                texts_query.append(augmented_query)

            batch_query = self.tokenizer(
                texts_query,
                return_token_type_ids=False,
                **output_kwargs["text_kwargs"],
            )

            return batch_query