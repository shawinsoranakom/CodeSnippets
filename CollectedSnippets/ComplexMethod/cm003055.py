def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        videos: VideoInput | None = None,
        **kwargs: Unpack[LlavaNextVideoProcessorKwargs],
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

        output_kwargs = self._merge_kwargs(
            LlavaNextVideoProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )
        if images is not None:
            image_inputs = self.image_processor(images, **output_kwargs["images_kwargs"])
        else:
            image_inputs = {}

        if videos is not None:
            videos_inputs = self.video_processor(videos, **output_kwargs["videos_kwargs"])
        else:
            videos_inputs = {}

        if isinstance(text, str):
            text = [text]
        elif not isinstance(text, list) and not isinstance(text[0], str):
            raise TypeError("Invalid input text. Please provide a string, or a list of strings")

        if image_inputs:
            image_sizes = iter(image_inputs["image_sizes"])
            height, width = get_image_size(to_numpy_array(image_inputs["pixel_values"][0][0]))
            prompt_strings = []
            for sample in text:
                while self.image_token in sample:
                    image_size = next(image_sizes)
                    if not isinstance(image_size, (list, tuple)):
                        # cast to list to avoid numerical precision errors when calculating unpadding
                        image_size = image_size.tolist()
                    orig_height, orig_width = image_size
                    num_image_tokens = self._get_number_of_features(orig_height, orig_width, height, width)
                    if self.vision_feature_select_strategy == "default":
                        num_image_tokens -= 1
                    sample = sample.replace(self.image_token, "<placeholder>" * num_image_tokens, 1)
                prompt_strings.append(sample)
            text = [sample.replace("<placeholder>", self.image_token) for sample in prompt_strings]

        # videos are easier, simply get frames and multiply
        if videos_inputs:
            one_video = videos_inputs.get("pixel_values_videos")[0]
            if isinstance(one_video, (list, tuple)):
                one_video = np.array(one_video)
            else:
                one_video = to_numpy_array(one_video)
            height, width = get_image_size(one_video[0])
            num_frames = one_video.shape[0]  # frame dim is always after batch dim

            # no `self.num_additional_image_tokens` added because video always has a default feature selection strategy
            num_image_tokens = (height // self.patch_size) * (width // self.patch_size)
            num_video_tokens = num_image_tokens // 4 * num_frames  # divide by 4 needed for avg pooling layer
            prompt_strings = []
            for sample in text:
                sample = sample.replace(self.video_token, self.video_token * num_video_tokens)
                prompt_strings.append(sample)
            text = prompt_strings

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        text_inputs = self.tokenizer(text, **output_kwargs["text_kwargs"])
        self._check_special_mm_tokens(text, text_inputs, modalities=["image", "video"])

        return BatchFeature(data={**text_inputs, **image_inputs, **videos_inputs}, tensor_type=return_tensors)