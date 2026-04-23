def __call__(
        self,
        images: ImageInput = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        videos: VideoInput = None,
        **kwargs: Unpack[VideoLlama3ProcessorKwargs],
    ) -> BatchFeature:
        output_kwargs = self._merge_kwargs(
            VideoLlama3ProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        image_inputs = videos_inputs = {}
        if images is not None:
            image_inputs = self.image_processor(images=images, **output_kwargs["images_kwargs"])
            image_grid_thw = image_inputs["image_grid_thw"]
            image_merge_sizes = image_inputs["image_merge_sizes"]
        else:
            image_grid_thw = image_merge_sizes = []

        if videos is not None:
            videos_inputs = self.video_processor(videos=videos, **output_kwargs["videos_kwargs"])
            num_video_tokens = [
                grid_thw.prod() // merge_size**2
                for grid_thw, merge_size in zip(videos_inputs["video_grid_thw"], videos_inputs["video_merge_sizes"])
            ]
            video_compression_masks = videos_inputs["video_compression_mask"].split(num_video_tokens)
            if not kwargs.get("return_metadata"):
                video_metadata = videos_inputs.pop("video_metadata")
            else:
                video_metadata = videos_inputs["video_metadata"]
            timestamps = []
            for metadata in video_metadata:
                if metadata.fps is None:
                    logger.warning_once(
                        "VideoLLaMA4 requires frame timestamps to construct prompts, but the `fps` of the input video could not be inferred. "
                        "Probably `video_metadata` was missing from inputs and you passed pre-sampled frames. "
                        "Defaulting to `fps=1`. Please provide `video_metadata` for more accurate results."
                    )
                metadata.fps = 1 if metadata.fps is None else metadata.fps
                timestamps.append(metadata.timestamps)
        else:
            video_compression_masks = timestamps = []

        if not isinstance(text, list):
            text = [text]

        text = text.copy()  # below lines change text in-place

        if images is not None:
            image_index = 0
            for i in range(len(text)):
                while self.image_token in text[i]:
                    num_image_tokens = image_grid_thw[image_index].prod() // (image_merge_sizes[image_index] ** 2)
                    text[i] = text[i].replace(self.image_token, "<|placeholder|>" * num_image_tokens, 1)
                    image_index += 1
                text[i] = text[i].replace("<|placeholder|>", self.image_token)

        if videos is not None:
            video_index = 0
            for i in range(len(text)):
                while self.video_token in text[i]:
                    frame_compression_masks = video_compression_masks[video_index].split(
                        len(video_compression_masks[video_index]) // len(timestamps[video_index])
                    )
                    num_frame_tokens = [x.sum() for x in frame_compression_masks]
                    frame_prompts = [
                        f"Time {t:.1f}s:" + "<|placeholder|>" * n
                        for n, t in zip(num_frame_tokens, timestamps[video_index])
                    ]
                    text[i] = text[i].replace(self.video_token, ",".join(frame_prompts), 1)
                    video_index += 1
                text[i] = text[i].replace("<|placeholder|>", self.video_token)

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        return_mm_token_type_ids = output_kwargs["text_kwargs"].pop("return_mm_token_type_ids", False)
        text_inputs = self.tokenizer(text, **output_kwargs["text_kwargs"], return_tensors=None)
        self._check_special_mm_tokens(text, text_inputs, modalities=["image", "video"])

        if return_mm_token_type_ids:
            text_inputs["mm_token_type_ids"] = self.create_mm_token_type_ids(text_inputs["input_ids"])
        return BatchFeature(data={**text_inputs, **image_inputs, **videos_inputs}, tensor_type=return_tensors)