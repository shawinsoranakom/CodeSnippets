def __call__(
        self,
        text: TextInput | list[TextInput],
        audio: AudioInput | None = None,
        output_labels: bool | None = False,
        **kwargs: Unpack[MusicFlamingoProcessorKwargs],
    ) -> BatchFeature:
        r"""
        Main method to prepare one or several text sequence(s) and audio waveform(s) for the model. This
        method expands `<sound>` placeholders in the text based on the post-pool frame counts of the
        audio windows, then tokenizes the provided strings as-is, and extracts log-mel features
        with [`WhisperFeatureExtractor`]. If `audio` is `None`, no audio processing is performed and
        the text is tokenized as-is (LM-only behavior).

        Args:
            text (`str` or `list[str]`):
                Input sequence or batch of sequences.
            audio (`np.ndarray` or `list[np.ndarray]`):
                Input audio or batch of audios as NumPy arrays. If provided, there must be as many `text` inputs as
                `audio` inputs.
            output_labels (bool, *optional*, default=False):
                Whether to return labels for training.

        Returns:
            [`BatchFeature`]: A dictionary with tokenized text (`input_ids`, `attention_mask`) and
            audio features (`input_features`, `input_features_mask`).
        """

        # Merge defaults with user kwargs
        call_kwargs = self._merge_kwargs(
            MusicFlamingoProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        text_kwargs = call_kwargs["text_kwargs"]
        audio_kwargs = call_kwargs["audio_kwargs"]
        return_tensors = text_kwargs.get("return_tensors")
        if return_tensors != "pt":
            raise ValueError(f"{self.__class__.__name__} only supports `return_tensors='pt'`.")

        if isinstance(text, str):
            text = [text]
        elif not (isinstance(text, (list, tuple)) and all(isinstance(t, str) for t in text)):
            raise ValueError("Invalid input text. Please provide a string, or a list of strings")

        audio_inputs = {}
        if audio is not None:
            audio = make_list_of_audio(audio)
            if len(text) != len(audio):
                raise ValueError(f"Got {len(text)} text but {len(audio)} audios; they must match 1:1.")

            # Determine number of chunks per sample, and flatten
            window_size = int(audio_kwargs["sampling_rate"] * self.feature_extractor.chunk_length)
            max_windows = int(self.max_audio_len // self.feature_extractor.chunk_length)

            per_sample_windows: list[int] = []
            flat_chunks: list[np.ndarray] = []

            for audio_el in audio:
                n_samples = int(audio_el.shape[0])
                n_win = max(1, (n_samples + window_size - 1) // window_size)
                if n_win > max_windows:
                    logger.warning(
                        f"Audio duration ({n_samples / audio_kwargs['sampling_rate']:.1f}s) exceeds {self.max_audio_len}s; truncating to first {self.max_audio_len}s."
                    )
                    n_win = max_windows
                per_sample_windows.append(n_win)

                time_cap = min(n_samples, n_win * window_size)
                for i in range(n_win):
                    start = i * window_size
                    end = min((i + 1) * window_size, time_cap)
                    flat_chunks.append(audio_el[start:end])

            # Feature extraction
            audio_inputs = self.feature_extractor(flat_chunks, **audio_kwargs)
            padding_mask = audio_inputs.pop("attention_mask")
            audio_inputs["input_features_mask"] = padding_mask

            # Expand audio tokens in text
            text = self._expand_audio_tokens(text, padding_mask, per_sample_windows)

        # Tokenize
        text_inputs = self.tokenizer(text, **text_kwargs)

        data = {**text_inputs, **audio_inputs}
        if output_labels:
            labels = data["input_ids"].clone()
            labels[self._get_audio_tokens_mask(labels)] = -100
            labels[labels == self.tokenizer.pad_token_id] = -100
            data["labels"] = labels

        return BatchFeature(data=data, tensor_type=return_tensors)