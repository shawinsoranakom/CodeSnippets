def __call__(
        self,
        audio: np.ndarray | list[float] | list[np.ndarray] = None,
        sampling_rate: int | list[int] | None = None,
        steps_per_beat: int = 2,
        resample: bool | None = True,
        notes: list | TensorType = None,
        padding: bool | str | PaddingStrategy = False,
        truncation: bool | str | TruncationStrategy = None,
        max_length: int | None = None,
        pad_to_multiple_of: int | None = None,
        verbose: bool = True,
        **kwargs,
    ) -> BatchFeature | BatchEncoding:
        # Since Feature Extractor needs both audio and sampling_rate and tokenizer needs both token_ids and
        # feature_extractor_output, we must check for both.
        r"""
        sampling_rate (`int` or `list[int]`, *optional*):
            The sampling rate of the input audio in Hz. This should match the sampling rate used by the feature
            extractor. If not provided, the default sampling rate from the processor configuration will be used.
        steps_per_beat (`int`, *optional*, defaults to `2`):
            The number of time steps per musical beat. This parameter controls the temporal resolution of the
            musical representation. A higher value provides finer temporal granularity but increases the sequence
            length. Used when processing audio to extract musical features.
        notes (`list` or `TensorType`, *optional*):
            Pre-extracted musical notes in MIDI format. When provided, the processor skips audio feature extraction
            and directly processes the notes through the tokenizer. Each note should be represented as a list or
            tensor containing pitch, velocity, and timing information.
        """
        if (audio is None and sampling_rate is None) and (notes is None):
            raise ValueError(
                "You have to specify at least audios and sampling_rate in order to use feature extractor or "
                "notes to use the tokenizer part."
            )

        if audio is not None and sampling_rate is not None:
            inputs = self.feature_extractor(
                audio=audio,
                sampling_rate=sampling_rate,
                steps_per_beat=steps_per_beat,
                resample=resample,
                **kwargs,
            )
        if notes is not None:
            encoded_token_ids = self.tokenizer(
                notes=notes,
                padding=padding,
                truncation=truncation,
                max_length=max_length,
                pad_to_multiple_of=pad_to_multiple_of,
                verbose=verbose,
                **kwargs,
            )

        if notes is None:
            return inputs

        elif audio is None or sampling_rate is None:
            return encoded_token_ids

        else:
            inputs["token_ids"] = encoded_token_ids["token_ids"]
            return inputs