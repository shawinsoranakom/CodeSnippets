def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        **kwargs: Unpack[GlmImageProcessorKwargs],
    ) -> BatchFeature:
        """
        Main method to prepare for the model one or several sequences(s) and image(s). This method forwards the `text`
        and `kwargs` arguments to PreTrainedTokenizerFast's [`~PreTrainedTokenizerFast.__call__`] if `text` is not `None` to encode
        the text.

        Args:
            images (`PIL.Image.Image`, `np.ndarray`, `torch.Tensor`, `List[PIL.Image.Image]`, `List[np.ndarray]`, `List[torch.Tensor]`):
                The image or batch of images to be prepared. Each image can be a PIL image, NumPy array or PyTorch
                tensor. Both channels-first and channels-last formats are supported.
            text (`str`, `List[str]`, `List[List[str]]`):
                The sequence or batch of sequences to be encoded. Each sequence can be a string or a list of strings
                (pretokenized string). If the sequences are provided as list of strings (pretokenized), you must set
                `is_split_into_words=True` (to lift the ambiguity with a batch of sequences).
            return_tensors (`str` or [`~utils.TensorType`], *optional*):
                If set, will return tensors of a particular framework. Acceptable values are:
                - `'pt'`: Return PyTorch `torch.Tensor` objects.
                - `'np'`: Return NumPy `np.ndarray` objects.

        Returns:
            [`BatchFeature`]: A [`BatchFeature`] with the following fields:

            - **input_ids** -- List of token ids to be fed to a model. Returned when `text` is not `None`.
            - **attention_mask** -- List of indices specifying which tokens should be attended to by the model (when
              `return_attention_mask=True` or if *"attention_mask"* is in `self.model_input_names` and if `text` is not
              `None`).
            - **pixel_values** -- Pixel values to be fed to a model. Returned when `images` is not `None`.
            - **image_grid_thw** -- List of image 3D grid in LLM. Returned when `images` is not `None`.
        """
        output_kwargs = self._merge_kwargs(
            GlmImageProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        target_h = output_kwargs["images_kwargs"].pop("target_h", None)
        target_w = output_kwargs["images_kwargs"].pop("target_w", None)
        is_text_to_image = images is None

        if images is not None:
            image_inputs = self.image_processor(images=images, **output_kwargs["images_kwargs"])
            image_grid_thw = image_inputs["image_grid_thw"]
        else:
            image_inputs = {}
            image_grid_thw = None

        # Handle text=None case (image-only processing)
        if text is None:
            if images is None:
                raise ValueError("You must provide at least one of `text` or `images`.")
            return image_inputs

        if not isinstance(text, list):
            text = [text]

        batch_size = len(text)
        text = text.copy()  # below lines change text in-place

        # Count images per sample by counting image tokens in each text
        images_per_sample = []
        for i in range(batch_size):
            images_per_sample.append(text[i].count(self.image_token))

        # Replace image tokens with the correct number of placeholder tokens
        if not is_text_to_image:
            index = 0
            for i in range(batch_size):
                while self.image_token in text[i]:
                    grid = image_grid_thw[index]
                    num_image_tokens = int(grid[1] * grid[2])
                    text[i] = text[i].replace(self.image_token, "<|placeholder|>" * num_image_tokens, 1)
                    index += 1
                text[i] = text[i].replace("<|placeholder|>", self.image_token)

        # Build prompt with target shape and combine grids in a single loop
        # Format: [sample0_source_grids..., sample0_target_grids, sample1_source_grids..., sample1_target_grids, ...]
        # Note: In i2i mode, batches are homogeneous (same number of source images per sample)
        num_source_images = images_per_sample[0] if images_per_sample else 0

        # Validate homogeneity for i2i mode
        if not is_text_to_image and images_per_sample and len(set(images_per_sample)) != 1:
            raise ValueError(
                f"In image-to-image mode, all samples must have the same number of source images. "
                f"Got different counts: {images_per_sample}"
            )

        all_grids = []
        for i in range(batch_size):
            text[i], token_h, token_w, prev_h, prev_w = self._build_prompt_with_target_shape(
                text[i], height=target_h, width=target_w, is_text_to_image=is_text_to_image
            )
            # Add source grids for this sample (i2i mode only)
            if not is_text_to_image and num_source_images > 0:
                start_idx = i * num_source_images
                all_grids.append(image_grid_thw[start_idx : start_idx + num_source_images])
            # Add target grid for this sample
            all_grids.append(
                self._build_target_image_grid_thw(
                    token_h=token_h,
                    token_w=token_w,
                    prev_token_h=prev_h,
                    prev_token_w=prev_w,
                    is_text_to_image=is_text_to_image,
                )
            )
        image_inputs["image_grid_thw"] = torch.cat(all_grids, dim=0)

        # Store images_per_sample for later use (add target images count)
        # Each sample will have: source_images + target_images (typically 2 for t2i, 1 for i2i)
        num_target_grids = 2 if is_text_to_image else 1
        image_inputs["images_per_sample"] = torch.tensor(
            [num_source_images + num_target_grids] * batch_size, dtype=torch.long
        )

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        return_mm_token_type_ids = output_kwargs["text_kwargs"].pop("return_mm_token_type_ids", False)
        text_inputs = self.tokenizer(text, **output_kwargs["text_kwargs"])

        self._check_special_mm_tokens(text, text_inputs, modalities=["image"])

        if return_mm_token_type_ids:
            text_inputs["mm_token_type_ids"] = self.create_mm_token_type_ids(text_inputs["input_ids"])
        return BatchFeature(data={**text_inputs, **image_inputs}, tensor_type=return_tensors)