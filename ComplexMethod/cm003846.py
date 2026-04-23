def __call__(
        self,
        images: ImageInput | list[ImageInput] | list[list[ImageInput]] = None,
        text: Union[TextInput, "PreTokenizedInput", list[TextInput], list["PreTokenizedInput"]] = None,
        videos: VideoInput | None = None,
        **kwargs: Unpack[SmolVLMProcessorKwargs],
    ) -> BatchEncoding:
        if text is None and images is None and videos is None:
            raise ValueError("You must provide one of `text`, `images` or `videos'.")

        if text is None and ((images is None) ^ (videos is not None)):
            raise ValueError("You must specify exactly one of `images` or `videos`")

        output_kwargs = self._merge_kwargs(
            SmolVLMProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        if text is not None:
            if isinstance(text, str):
                text = [text]
            elif not isinstance(text, list) and not isinstance(text[0], str):
                raise ValueError("Invalid input text. Please provide a string, or a list of strings")
            n_images_in_text = sum(sample.count(self.image_token) for sample in text)
            if n_images_in_text > 0 and (images is None and videos is None):
                raise ValueError(f"We detected {n_images_in_text} tokens in the text but no images/videos were passed")

        inputs = {}
        # Images and videos are mutually exclusive, so process one which is present
        if images is not None:
            images = self.image_processor.fetch_images(images)
            images = make_nested_list_of_images(images)
            vision_inputs = self.image_processor(images, **output_kwargs["images_kwargs"])

            image_rows = vision_inputs.pop("rows", None)
            image_cols = vision_inputs.pop("cols", None)
            inputs.update(vision_inputs)

            if text is not None:
                n_images_in_text = [sample.count(self.image_token) for sample in text]
                n_images_in_images = [len(sublist) for sublist in images]
                if n_images_in_images != n_images_in_text:
                    raise ValueError(
                        f"The number of images in the text {n_images_in_text} and images {n_images_in_images} should be the same."
                    )
                # Set default values for image_rows and image_cols if not provided
                if image_rows is None:
                    image_rows = [[0] * n_images for n_images in n_images_in_text]
                if image_cols is None:
                    image_cols = [[0] * n_images for n_images in n_images_in_text]
                text = self.expand_text_with_image_tokens(text, image_rows=image_rows, image_cols=image_cols)

        elif videos is not None:
            vision_inputs = self.video_processor(videos, **output_kwargs["videos_kwargs"])
            if text is not None:
                n_videos_in_text = [sample.count(self.video_token) for sample in text]
                n_videos_in_videos = [len(sublist) for sublist in videos]
                if n_videos_in_videos != n_videos_in_text:
                    raise ValueError(
                        f"The number of videos in the text {n_videos_in_text} and videos {n_videos_in_videos} should be the same."
                    )
                text = self.expand_text_with_video_tokens(text, vision_inputs)

            # If user has not requested video metadata, pop it. By default metadata
            # is always returned to expand video tokens correctly
            if not kwargs.get("return_metadata"):
                vision_inputs.pop("video_metadata")
            inputs.update(vision_inputs)

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)

        if text is not None:
            text_inputs = self.tokenizer(text, **output_kwargs["text_kwargs"])
            self._check_special_mm_tokens(text, text_inputs, modalities=["image"])
            inputs.update(text_inputs)

        return BatchFeature(inputs, tensor_type=return_tensors)