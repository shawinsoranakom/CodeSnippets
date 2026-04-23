def __call__(
        self,
        images: ImageInput = None,
        videos: np.ndarray | list[ImageInput] = None,
        text: TextInput
        | PreTokenizedInput
        | list[TextInput]
        | list[PreTokenizedInput] = None,
        **kwargs: Unpack[Ovis2_5ProcessorKwargs],
    ) -> BatchFeature:
        """
        Main method to prepare for the model one or several sequences(s)
        and image(s). This method forwards the `text`and `kwargs` arguments
        to Qwen2TokenizerFast's [`~Qwen2TokenizerFast.__call__`] if `text`
        is not `None` to encode the text. To prepare the vision inputs,
        this method forwards the `vision_infos` and `kwrags` arguments to
        Qwen2VLImageProcessor's [`~Qwen2VLImageProcessor.__call__`]
        if `vision_infos` is not `None`.
            Args:
                images (`PIL.Image.Image`, `np.ndarray`, `torch.Tensor`,
                    `list[PIL.Image.Image]`, `list[np.ndarray]`,
                    `list[torch.Tensor]`):
                    The image or batch of images to be prepared.
                    Each image can be a PIL image, NumPy array or PyTorch
                    tensor. Both channels-first and channels-last formats
                    are supported.
                text (`str`, `list[str]`, `list[list[str]]`):
                    The sequence or batch of sequences to be encoded.
                    Each sequence can be a string or a list of strings
                    (pretokenized string). If the sequences are provided as
                    list of strings (pretokenized), you must set
                    `is_split_into_words=True` (to lift the ambiguity with
                    a batch of sequences).
                videos (`np.ndarray`, `torch.Tensor`, `list[np.ndarray]`,
                    `list[torch.Tensor]`):
                    The image or batch of videos to be prepared. Each video
                    can be a 4D NumPy array or PyTorch tensor, or a nested
                    list of 3D frames. Both channels-first and channels-last
                    formats are supported.
                return_tensors (`str` or [`~utils.TensorType`], *optional*):
                    If set, will return tensors of a particular framework.
                    Acceptable values are:
                    - `'tf'`: Return TensorFlow `tf.constant` objects.
                    - `'pt'`: Return PyTorch `torch.Tensor` objects.
                    - `'np'`: Return NumPy `np.ndarray` objects.
                    - `'jax'`: Return JAX `jnp.ndarray` objects.
            Returns:
                [`BatchFeature`]: A [`BatchFeature`] with the following fields:
                - **input_ids** -- list of token ids to be fed to a model.
                  Returned when `text` is not `None`.
                - **attention_mask** -- list of indices specifying which tokens
                  should be attended to by the model (when
                  `return_attention_mask=True` or if *"attention_mask"*
                  is in `self.model_input_names` and if `text` is not `None`).
                - **pixel_values** -- Pixel values to be fed to a model.
                  Returned when `images` is not `None`.
                - **pixel_values_videos** -- Pixel values of videos to be fed to
                  a model. Returned when `videos` is not `None`.
                - **image_grid_thw** -- list of image 3D grid in LLM. Returned
                  when `images` is not `None`.
                - **video_grid_thw** -- list of video 3D grid in LLM. Returned
                  when `videos` is not `None`.
                - **second_per_grid_ts** -- list of video seconds per time grid.
                  Returned when `videos` is not `None`.
        """
        output_kwargs = self._merge_kwargs(
            Ovis2_5ProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )
        # Process all images first
        visual_features = {}
        output = BatchFeature()
        if images is not None:
            processed_images = []
            image_placeholders_list = []
            grids = []
            # Process each image
            for image in images if isinstance(images, list) else [images]:
                pixel_values, image_placeholders, grid = self.preprocess_multidata(
                    images=image,
                    **output_kwargs["images_kwargs"],
                )
                processed_images.append(pixel_values)
                image_placeholders_list.append(image_placeholders)
                grids.append(grid)

            # assign all processed images
            if processed_images:
                visual_features["image_placeholders"] = image_placeholders_list
            output["pixel_values"] = processed_images
            output["grids"] = grids

        if videos is not None:
            processed_videos = []
            videos_placeholders_list = []
            grids = []
            # Process each video
            for video in videos if isinstance(videos, list) else [videos]:
                pixel_values, video_placeholders, grid = self.preprocess_multidata(
                    video=video,
                    **output_kwargs["videos_kwargs"],
                )
                processed_videos.append(pixel_values)
                videos_placeholders_list.append(video_placeholders)
                grids.append(grid)
            # assign all processed videos
            if processed_videos:
                visual_features["video_placeholders"] = videos_placeholders_list
            output["video_pixel_values"] = processed_videos
            output["video_grids"] = grids

        # Process text input
        if text is not None:
            if not isinstance(text, list):
                text = [text]
            tokenized_batched_text = self._tokenize_with_visual_symbol(text)
            image_token_id = self.get_token_value("image_token")
            video_token_id = self.get_token_value("video_token")
            replaced_ids_list = []
            image_idx = 0
            video_idx = 0
            for ids_tensor in tokenized_batched_text:
                has_image_tokens = (
                    image_token_id in ids_tensor
                    and "image_placeholders" in visual_features
                    and image_idx < len(visual_features["image_placeholders"])
                )
                has_video_tokens = (
                    video_token_id in ids_tensor
                    and "video_placeholders" in visual_features
                    and video_idx < len(visual_features["video_placeholders"])
                )
                if has_image_tokens or has_video_tokens:
                    # Convert to list for easier manipulation
                    ids_list = ids_tensor.tolist()
                    new_ids = []

                    # Replace placeholders
                    for token_id in ids_list:
                        if token_id == image_token_id:
                            new_ids.extend(
                                visual_features["image_placeholders"][image_idx]
                            )
                            image_idx += 1
                        elif token_id == video_token_id:
                            new_ids.extend(
                                visual_features["video_placeholders"][video_idx]
                            )
                            video_idx += 1
                        else:
                            new_ids.append(token_id)
                    # Convert back to tensor
                    ids_tensor = torch.tensor(new_ids, dtype=torch.long)
                replaced_ids_list.append(ids_tensor)
            if replaced_ids_list:
                replaced_and_tokenized_ids = torch.stack(replaced_ids_list)
            else:
                replaced_and_tokenized_ids = torch.tensor([], dtype=torch.long)
            output["input_ids"] = replaced_and_tokenized_ids

            return output
        # If only images were provided
        return BatchFeature(data=visual_features)