def __call__(
        self,
        raw_speech: np.ndarray | list[float] | list[np.ndarray] | list[list[float]],
        padding: bool | str | PaddingStrategy = "longest",
        max_length: int | None = 480_000,
        truncation: bool = True,
        pad_to_multiple_of: int | None = 128,
        return_tensors: str | TensorType | None = None,
        return_attention_mask: bool | None = True,
        **kwargs,
    ) -> BatchFeature:
        """Creates a batch of MEL spectrograms from the provided raw speech.

        This implementation uses a different algorithm for windowing and preemphasis compared to the built-in
        `transformers.audio_utils.spectrogram()` function that _will_ result in different outputs. Consider this
        carefully when selecting an audio feature extractor, especially with pre-trained models.

        Args:
            raw_speech:
                The audio for which MEL spectrograms are created.
            padding (`Union[bool, str, PaddingStrategy]`, *optional*, defaults to `"longest"`):
                The padding strategy to use for batches of audio with different lengths.
            max_length (`int`, *optional*, defaults to 480000):
                If provided, defines the maximum length of the audio to allow. Audio longer than this will be
                truncated if `truncation=True`.
            truncation (`bool`, *optional*, defaults to `True`):
                Whether or not to truncate audio above `max_length`.
            pad_to_multiple_of (`int`, *optional*, defaults to 128):
                When padding, pad to a multiple of this value. The default value is defined for optimal TPU support.
            return_tensors (`Union[str, TensorType]`, *optional*, defaults to `None`):
                The type of tensors to return (e.g., NumPy, or Torch).
            return_attention_mask (`bool`, *optional*, defaults to `True`):
                Whether to return the attention mask for the generated MEL spectrograms.
        """

        is_batched_numpy = isinstance(raw_speech, np.ndarray) and len(raw_speech.shape) > 1
        is_batched_sequence = isinstance(raw_speech, Sequence) and isinstance(raw_speech[0], (np.ndarray, Sequence))
        is_batched = is_batched_numpy or is_batched_sequence

        if is_batched:
            raw_speech = [np.asarray([rs]).T for rs in raw_speech]
        elif not is_batched and not isinstance(raw_speech, np.ndarray):
            raw_speech = np.asarray(raw_speech)

        if not is_batched:  # always return a batch
            raw_speech = [np.asarray([raw_speech])]

        batched_speech = self.pad(
            BatchFeature({"input_features": raw_speech}),
            padding=padding,
            max_length=max_length,
            truncation=truncation,
            pad_to_multiple_of=pad_to_multiple_of,
            return_attention_mask=return_attention_mask,
        )

        prepared_speech = []
        prepared_speech_mask = []
        for speech, mask in zip(batched_speech.input_features, batched_speech.attention_mask):
            speech, mask = self._extract_spectrogram(speech.T, mask)
            prepared_speech.append(speech.astype(np.float32))
            prepared_speech_mask.append(mask)

        prepared_speech = [speech * mask[..., None] for speech, mask in zip(prepared_speech, prepared_speech_mask)]

        return BatchFeature(
            {"input_features": prepared_speech, "input_features_mask": prepared_speech_mask},
            tensor_type=return_tensors,
        )