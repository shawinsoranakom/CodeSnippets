def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        videos: VideoInput | None = None,
        **kwargs: Unpack[Glm46VProcessorKwargs],
    ) -> BatchFeature:
        r"""
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
        """
        output_kwargs = self._merge_kwargs(
            Glm46VProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )
        if images is not None:
            image_inputs = self.image_processor(images=images, **output_kwargs["images_kwargs"])
            image_grid_thw = image_inputs["image_grid_thw"]
        else:
            image_inputs = {}
            image_grid_thw = None

        if videos is not None:
            videos_inputs = self.video_processor(videos=videos, **output_kwargs["videos_kwargs"])
            # If user has not requested video metadata, pop it
            if not kwargs.get("return_metadata"):
                video_metadata = videos_inputs.pop("video_metadata")
            else:
                video_metadata = videos_inputs["video_metadata"]
            video_grid_thw = videos_inputs["video_grid_thw"]
        else:
            videos_inputs = {}
            video_grid_thw = None

        if not isinstance(text, list):
            text = [text]

        text = text.copy()  # below lines change text in-place
        if image_grid_thw is not None:
            merge_length = self.image_processor.merge_size**2
            index = 0
            for i in range(len(text)):
                while self.image_token in text[i]:
                    num_image_tokens = image_grid_thw[index].prod() // merge_length
                    text[i] = text[i].replace(self.image_token, "<|placeholder|>" * num_image_tokens, 1)
                    index += 1
                text[i] = text[i].replace("<|placeholder|>", self.image_token)

        if video_grid_thw is not None:
            merge_length = self.video_processor.merge_size**2
            video_index = 0
            for i in range(len(text)):
                while self.video_token in text[i]:
                    num_frames = video_grid_thw[video_index][0]
                    video_structure = ""

                    metadata = video_metadata[video_index]
                    if metadata.fps is None:
                        logger.warning_once(
                            "SmolVLM requires frame timestamps to construct prompts, but the `fps` of the input video could not be inferred. "
                            "Probably `video_metadata` was missing from inputs and you passed pre-sampled frames. "
                            "Defaulting to `fps=24`. Please provide `video_metadata` for more accurate results."
                        )
                    metadata.fps = 24 if metadata.fps is None else metadata.fps
                    timestamps = metadata.timestamps[::2]  # mrope

                    unique_timestamps = []
                    for idx in range(0, len(timestamps)):
                        unique_timestamps.append(timestamps[idx])

                    selected_timestamps = unique_timestamps[:num_frames]
                    while len(selected_timestamps) < num_frames:
                        selected_timestamps.append(selected_timestamps[-1] if selected_timestamps else 0)

                    for frame_idx in range(num_frames):
                        timestamp_sec = selected_timestamps[frame_idx]
                        frame_structure = self.replace_frame_token_id(timestamp_sec)
                        video_structure += frame_structure

                    text[i] = text[i].replace(self.video_token, video_structure, 1)
                    num_image_tokens = (
                        video_grid_thw[video_index].prod() // merge_length // video_grid_thw[video_index][0]
                    )
                    for frame_idx in range(num_frames):
                        if self.image_token in text[i]:
                            text[i] = text[i].replace(self.image_token, "<|placeholder|>" * num_image_tokens, 1)

                    video_index += 1

                text[i] = text[i].replace("<|placeholder|>", self.image_token)
        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        return_mm_token_type_ids = output_kwargs["text_kwargs"].pop("return_mm_token_type_ids", False)
        text_inputs = self.tokenizer(text, **output_kwargs["text_kwargs"])
        self._check_special_mm_tokens(text, text_inputs, modalities=["image", "video"])

        if return_mm_token_type_ids:
            text_inputs["mm_token_type_ids"] = self.create_mm_token_type_ids(text_inputs["input_ids"])
        return BatchFeature(data={**text_inputs, **image_inputs, **videos_inputs}, tensor_type=return_tensors)