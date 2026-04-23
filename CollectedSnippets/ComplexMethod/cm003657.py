def __call__(
        self,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        images: ImageInput | None = None,
        videos: ImageInput | None = None,
        padding: bool | str | PaddingStrategy = False,
        truncation: bool | str | TruncationStrategy | None = None,
        max_length: int | None = None,
        return_tensors: str | TensorType | None = TensorType.PYTORCH,
    ) -> BatchFeature:
        r"""
        padding (`bool`, `str` or [`~utils.PaddingStrategy`], *optional*, defaults to `False`):
            Select a strategy to pad the returned sequences (according to the model's padding side and padding
            index) among:
            - `True` or `'longest'`: Pad to the longest sequence in the batch (or no padding if only a single
                sequence if provided).
            - `'max_length'`: Pad to a maximum length specified with the argument `max_length` or to the maximum
                acceptable input length for the model if that argument is not provided.
            - `False` or `'do_not_pad'` (default): No padding (i.e., can output a batch with sequences of different
                lengths).
        truncation (`bool`, *optional*):
            Activates truncation to cut input sequences longer than `max_length` to `max_length`.
        max_length (`int`, *optional*):
            Maximum length of the returned list and optionally padding length (see above).

        Returns:
            [`BatchFeature`]: A [`BatchFeature`] with the following fields:

            - **input_ids** -- List of token ids to be fed to a model. Returned when `text` is not `None`.
            - **attention_mask** -- List of indices specifying which tokens should be attended to by the model (when
              `return_attention_mask=True` or if *"attention_mask"* is in `self.model_input_names` and if `text` is not
              `None`).
            - **pixel_values** -- Pixel values to be fed to a model. Returned when `images` is not `None`.
            - **pixel_values_videos** -- Pixel values to be fed to a model. Returned when `videos` is not `None`.
        """

        if isinstance(text, str):
            text = [text]
        elif not isinstance(text, list) and not isinstance(text[0], str):
            raise TypeError("Invalid input text. Please provide a string, or a list of strings")

        data = {}
        if images is not None:
            encoded_images = self.image_processor(images=images, return_tensors=return_tensors)
            data.update(encoded_images)

            height, width = get_image_size(to_numpy_array(encoded_images.get("pixel_values_images")[0]))
            num_image_tokens = (height // self.patch_size) * (width // self.patch_size)
            num_image_tokens += self.num_additional_image_tokens
            if self.vision_feature_select_strategy == "default":
                num_image_tokens -= 1
            text = [sample.replace(self.image_token, self.image_token * num_image_tokens) for sample in text]

        if videos is not None:
            encoded_videos = self.video_processor(videos=videos, return_tensors=return_tensors)
            data.update(encoded_videos)

            one_video = encoded_videos.get("pixel_values_videos")[0]
            if isinstance(encoded_videos.get("pixel_values_videos")[0], (list, tuple)):
                one_video = np.array(one_video)
            else:
                one_video = to_numpy_array(one_video)
            height, width = get_image_size(one_video[0])
            num_frames = one_video.shape[0]  # frame dim is always after batch dim

            num_image_tokens = (height // self.patch_size) * (width // self.patch_size)
            num_image_tokens += self.num_additional_image_tokens
            num_video_tokens = num_image_tokens * num_frames
            text = [sample.replace(self.video_token, self.video_token * num_video_tokens) for sample in text]

        text_inputs = self.tokenizer(
            text,
            return_tensors=None,
            padding=padding,
            truncation=truncation,
            max_length=max_length,
        )
        self._check_special_mm_tokens(text, text_inputs, modalities=["image", "video"])

        data.update(text_inputs)

        return BatchFeature(data=data, tensor_type=return_tensors)