def __call__(
        self,
        images: ImageInput = None,
        text: TextInput
        | PreTokenizedInput
        | list[TextInput]
        | list[PreTokenizedInput] = None,
        **kwargs: Unpack[OvisProcessorKwargs],
    ) -> BatchFeature:
        """
        Main method to prepare for the model one or several sequences(s) and image(s). This method forwards the `text`
        and `kwargs` arguments to Qwen2TokenizerFast's [`~Qwen2TokenizerFast.__call__`] if `text` is not `None` to encode
        the text. To prepare the vision inputs, this method forwards the `vision_infos` and `kwrags` arguments to
        Qwen2VLImageProcessor's [`~Qwen2VLImageProcessor.__call__`] if `vision_infos` is not `None`.
            Args:
                images (`PIL.Image.Image`, `np.ndarray`, `torch.Tensor`, `list[PIL.Image.Image]`, `list[np.ndarray]`, `list[torch.Tensor]`):
                    The image or batch of images to be prepared. Each image can be a PIL image, NumPy array or PyTorch
                    tensor. Both channels-first and channels-last formats are supported.
                text (`str`, `list[str]`, `list[list[str]]`):
                    The sequence or batch of sequences to be encoded. Each sequence can be a string or a list of strings
                    (pretokenized string). If the sequences are provided as list of strings (pretokenized), you must set
                    `is_split_into_words=True` (to lift the ambiguity with a batch of sequences).
                videos (`np.ndarray`, `torch.Tensor`, `list[np.ndarray]`, `list[torch.Tensor]`):
                    The image or batch of videos to be prepared. Each video can be a 4D NumPy array or PyTorch
                    tensor, or a nested list of 3D frames. Both channels-first and channels-last formats are supported.
                return_tensors (`str` or [`~utils.TensorType`], *optional*):
                    If set, will return tensors of a particular framework. Acceptable values are:
                    - `'tf'`: Return TensorFlow `tf.constant` objects.
                    - `'pt'`: Return PyTorch `torch.Tensor` objects.
                    - `'np'`: Return NumPy `np.ndarray` objects.
                    - `'jax'`: Return JAX `jnp.ndarray` objects.
            Returns:
                [`BatchFeature`]: A [`BatchFeature`] with the following fields:
                - **input_ids** -- List of token ids to be fed to a model. Returned when `text` is not `None`.
                - **attention_mask** -- List of indices specifying which tokens should be attended to by the model (when
                  `return_attention_mask=True` or if *"attention_mask"* is in `self.model_input_names` and if `text` is not
                  `None`).
                - **pixel_values** -- Pixel values to be fed to a model. Returned when `images` is not `None`.
                - **pixel_values_videos** -- Pixel values of videos to be fed to a model. Returned when `videos` is not `None`.
                - **image_grid_thw** -- List of image 3D grid in LLM. Returned when `images` is not `None`.
                - **video_grid_thw** -- List of video 3D grid in LLM. Returned when `videos` is not `None`.
                - **second_per_grid_ts** -- List of video seconds per time grid. Returned when `videos` is not `None`.
        """

        max_partition = kwargs.pop("max_partition", 9)
        covering_threshold = kwargs.pop("covering_threshold", 0.9)

        output_kwargs = self._merge_kwargs(
            OvisProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        # Process all images first
        image_features = {}
        if images is not None:
            processed_images = []
            image_placeholders_list = []
            grids = []

            # Process each image
            for image in images if isinstance(images, list) else [images]:
                pixel_values, image_placeholders, grid = self.preprocess_image(
                    image=image,
                    max_partition=max_partition,
                    covering_threshold=covering_threshold,
                    **output_kwargs["images_kwargs"],
                )
                processed_images.append(pixel_values)
                image_placeholders_list.append(image_placeholders)
                grids.append(grid)

            # assign all processed images
            if processed_images:
                image_features["image_placeholders"] = image_placeholders_list

        # Process text input
        if text is not None:
            if not isinstance(text, list):
                text = [text]

            tokenized_batched_text = self._tokenize_with_image_symbol(text)
            image_token_id = self.get_token_value("image_token")
            replaced_ids_list = []
            idx = 0
            for ids_tensor in tokenized_batched_text:
                if (
                    image_token_id in ids_tensor
                    and "image_placeholders" in image_features
                ):
                    if idx < len(image_features["image_placeholders"]):
                        # Converts in list for ease of use
                        ids_list = ids_tensor.tolist()

                        new_ids = []

                        # replace placeholders
                        for i, token_id in enumerate(ids_list):
                            if token_id == image_token_id:
                                placeholder_ids = image_features["image_placeholders"][
                                    idx
                                ]
                                new_ids.extend(placeholder_ids)
                                idx += 1
                            else:
                                new_ids.append(token_id)

                        # Converts back to tensors
                        ids_tensor = torch.tensor(new_ids, dtype=torch.long)
                    else:
                        raise RuntimeError(
                            "Mismatch between the images you provided and the number of placeholder present in the text"
                        )

                replaced_ids_list.append(ids_tensor)

            if replaced_ids_list:
                replaced_and_tokenized_ids = torch.stack(replaced_ids_list)
            else:
                replaced_and_tokenized_ids = torch.tensor([], dtype=torch.long)

            # Create the output with text features
            output = BatchFeature(
                data={
                    "input_ids": replaced_and_tokenized_ids,
                }
            )

            # Add image features if present
            if image_features:
                output["pixel_values"] = processed_images
                output["grids"] = grids

            return output

        # If only images were provided
        return BatchFeature(data=image_features)