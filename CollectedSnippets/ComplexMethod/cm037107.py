def __call__(
        self,
        text: str | list[str] | None = None,
        images: Image.Image | list[Image.Image] | None = None,
        videos: tuple[npt.NDArray, dict[str, Any]]
        | list[tuple[npt.NDArray, dict[str, Any]]]
        | None = None,
        audios: AudioItem | list[AudioItem] | None = None,
        *,
        return_tensors: str | TensorType | None = None,
        max_num_tiles: int | None = None,
        **kwargs,
    ) -> BatchFeature:
        # Use default if not provided
        if max_num_tiles is None:
            max_num_tiles = self.max_num_tiles

        text = self._make_batch_input(text)
        images = self._make_batch_input(images)
        videos = self._make_batch_input(videos)
        audios = self._make_batch_input(audios)

        text, image_inputs = self._preprocess_image(
            text=text,
            images=images,
            max_num_tiles=max_num_tiles,
        )

        text, video_inputs = self._preprocess_video(
            text=text,
            videos=videos,
        )

        text, audio_inputs = self._preprocess_audio(
            text=text,
            audios=audios,
        )

        text_inputs = self.tokenizer(text, add_special_tokens=False)

        combined_inputs = {**text_inputs, **video_inputs, **audio_inputs}
        frames_indices = combined_inputs.get("frames_indices")
        ragged_frames_indices = (
            isinstance(frames_indices, list)
            and len({len(frame_indices) for frame_indices in frames_indices}) > 1
        )
        if ragged_frames_indices:
            combined_inputs.pop("frames_indices")

        if self.dynamic_tiler is None:
            batch = BatchFeature(
                {**combined_inputs, **image_inputs},
                tensor_type=return_tensors,
            )
        else:
            batch = BatchFeature(combined_inputs, tensor_type=return_tensors)
            # allow images to be exempt from the BatchFeature validation:
            # We will .stack() them in _parse_and_validate_image_input
            batch.update(image_inputs)
        if ragged_frames_indices:
            assert isinstance(frames_indices, list)
            batch["frames_indices"] = [
                torch.as_tensor(frame_indices, dtype=torch.int64)
                for frame_indices in frames_indices
            ]
        return batch