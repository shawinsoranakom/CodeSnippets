def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        videos: VideoInput | None = None,
        **kwargs: Unpack[LlavaOnevisionProcessorKwargs],
    ) -> BatchFeature:
        r"""
        Returns:
            [`BatchFeature`]: A [`BatchFeature`] with the following fields:

            - **input_ids** -- List of token ids to be fed to a model. Returned when `text` is not `None`.
            - **attention_mask** -- List of indices specifying which tokens should be attended to by the model (when
              `return_attention_mask=True` or if *"attention_mask"* is in `self.model_input_names` and if `text` is not
              `None`).
            - **pixel_values** -- Pixel values to be fed to a model. Returned when `images` is not `None`.
            - **pixel_values_videos** -- Pixel values of a video input to be fed to a model. Returned when `videos` is not `None`.
            - **image_sizes** -- Size of each image that will be used to unpad an image. Returned when `images` is not `None`.
        """

        output_kwargs = self._merge_kwargs(
            LlavaOnevisionProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        if isinstance(text, str):
            text = [text]
        elif not isinstance(text, list) and not isinstance(text[0], str):
            raise TypeError("Invalid input text. Please provide a string, or a list of strings")

        image_inputs = video_inputs = {}

        if images is not None:
            image_inputs = self.image_processor(images, **output_kwargs["images_kwargs"])

            batch_num_images = iter(image_inputs["batch_num_images"])
            image_sizes = iter(image_inputs["image_sizes"])
            height, width = get_image_size(
                to_numpy_array(image_inputs["pixel_values"][0][0]),
                channel_dim=output_kwargs["images_kwargs"].get("data_format"),
            )
            text, num_image_tokens = self._expand_image_tokens(
                text, image_sizes, height, width, self.image_token, batch_num_images
            )

        if videos is not None:
            video_inputs = self.video_processor(videos, **output_kwargs["videos_kwargs"])

            one_video = video_inputs.get("pixel_values_videos")[0]
            if isinstance(video_inputs.get("pixel_values_videos")[0], (list, tuple)):
                one_video = np.array(one_video)
            else:
                one_video = to_numpy_array(one_video)
            height, width = get_image_size(one_video[0], channel_dim=output_kwargs["images_kwargs"].get("data_format"))
            num_frames = one_video.shape[0]  # frame dim is always after batch dim
            patches_height_width = int(math.sqrt(self.num_image_tokens))
            pooled_height_width = math.ceil(patches_height_width / 2)
            num_video_tokens = (num_frames * pooled_height_width * pooled_height_width) + 1  # +1 for newline token
            text = [sample.replace(self.video_token, self.video_token * num_video_tokens) for sample in text]

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        return_mm_token_type_ids = output_kwargs["text_kwargs"].pop("return_mm_token_type_ids", None)
        text_inputs = self.tokenizer(text, **output_kwargs["text_kwargs"])
        self._check_special_mm_tokens(text, text_inputs, modalities=["image"])

        if return_mm_token_type_ids:
            text_inputs["mm_token_type_ids"] = self.create_mm_token_type_ids(text_inputs["input_ids"])
        return BatchFeature(data={**text_inputs, **image_inputs, **video_inputs}, tensor_type=return_tensors)