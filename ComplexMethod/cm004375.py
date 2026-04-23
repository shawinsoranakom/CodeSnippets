def __call__(
        self,
        images: ImageInput | None = None,
        text: str | list[str] | TextInput | PreTokenizedInput | None = None,
        **kwargs: Unpack[FuyuProcessorKwargs],
    ) -> "FuyuBatchFeature":
        r"""
        Returns:
            [`FuyuBatchEncoding`]: A [`FuyuBatchEncoding`] with the following fields:

            - **input_ids** -- Tensor of token ids to be fed to a model. Returned when `text` is not `None`.
            - **image_patches** -- List of Tensor of image patches. Returned when `images` is not `None`.
            - **image_patches_indices** -- Tensor of indices where patch embeddings have to be inserted by the model.
            - **attention_mask** -- List of indices specifying which tokens should be attended to by the model when
              `return_attention_mask=True`.
        """
        requires_backends(self, ["torch"])

        # --- Check input validity ---
        if text is None and images is None:
            raise ValueError("You have to specify either text or images. Both cannot be None.")

        output_kwargs = self._merge_kwargs(
            FuyuProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )
        return_mm_token_type_ids = output_kwargs["text_kwargs"].pop("return_mm_token_type_ids", False)

        if not output_kwargs["text_kwargs"].setdefault("return_attention_mask", True):
            raise ValueError("`return_attention_mask=False` is not supported for this model.")

        if text is not None and images is None:
            logger.warning("You are processing a text with no associated image. Make sure it is intended.")
            text_encoding = self.tokenizer(text, **output_kwargs["text_kwargs"])
            return text_encoding

        if text is None and images is not None:
            logger.warning("You are processing an image with no associated text. Make sure it is intended.")
            prompts = [[""]]
        if text is not None and images is not None:
            if isinstance(text, str):
                prompts = [[text]]
            elif isinstance(text, list):
                prompts = [[text_seq] for text_seq in text]

        # --- Preprocess images using self.image_processor ---

        # FIXME - We hard code "pt" here because the rest of the processing assumes torch tensors
        output_kwargs["images_kwargs"]["return_tensors"] = "pt"
        image_encoding = self.image_processor.preprocess(images, **output_kwargs["images_kwargs"])
        batch_images = image_encoding["images"]
        image_unpadded_heights = image_encoding["image_unpadded_heights"]
        image_unpadded_widths = image_encoding["image_unpadded_widths"]
        scale_factors = image_encoding["image_scale_factors"]
        self.subsequence_length = 1  # Each batch contains only one sequence.
        self.batch_size = len(batch_images)

        # --- Use self.tokenizer to get the ids of special tokens to insert into image ids ---

        tensor_batch_images = torch.stack([img[0] for img in batch_images if img]).unsqueeze(1)

        # --- Use self.image_processor again to obtain the full token ids and batch inputs ---
        all_encodings = []

        for prompt, scale_factor, image_unpadded_height, image_unpadded_width, tensor_batch_image in zip(
            prompts, scale_factors, image_unpadded_heights, image_unpadded_widths, tensor_batch_images
        ):
            sample_encoding = self.get_sample_encoding(
                prompts=[prompt],
                scale_factors=[scale_factor],
                image_unpadded_heights=torch.tensor([image_unpadded_height]),
                image_unpadded_widths=torch.tensor([image_unpadded_width]),
                image_placeholder_id=self.image_token_id,
                image_newline_id=self.image_newline_id,
                tensor_batch_images=tensor_batch_image.unsqueeze(0),
            )
            all_encodings.append(sample_encoding)

        batch_encoding = self._left_pad_inputs_with_attention_mask(
            model_inputs=all_encodings, return_attention_mask=True
        )
        if return_mm_token_type_ids:
            batch_encoding["mm_token_type_ids"] = self.create_mm_token_type_ids(batch_encoding["input_ids"])
            batch_encoding["mm_token_type_ids"] = torch.tensor(batch_encoding["mm_token_type_ids"])
        return FuyuBatchFeature(data=batch_encoding)