def __call__(
        self,
        raw_audio: np.ndarray | list[float] | list[np.ndarray] | list[list[float]] | str | list[str],
        padding: bool | str | PaddingStrategy | None = None,
        truncation: bool | None = False,
        max_length: int | None = None,
        return_tensors: str | TensorType | None = None,
        sampling_rate: int | None = None,
    ) -> BatchFeature:
        from_file = False
        if isinstance(raw_audio, str):
            raw_audio = [raw_audio]

        if isinstance(raw_audio, (list, tuple)) and isinstance(raw_audio[0], str):
            loaded = []
            for audio_file in raw_audio:
                loaded.append(load_audio(audio_file, self.sampling_rate))
            raw_audio = loaded
            from_file = True

        if sampling_rate is not None:
            if sampling_rate != self.sampling_rate:
                raise ValueError(
                    f"The model corresponding to this feature extractor: {self} was trained using a sampling rate of"
                    f" {self.sampling_rate}. Please make sure that the provided audio input was sampled with"
                    f" {self.sampling_rate} and not {sampling_rate}."
                )
        elif not from_file:
            logger.warning(
                f"It is strongly recommended to pass the `sampling_rate` argument to `{self.__class__.__name__}()`. "
                "Failing to do so can result in silent errors that might be hard to debug."
            )

        if padding and truncation:
            raise ValueError("Both padding and truncation were set. Make sure you only set one.")
        elif padding is None:
            # by default let's pad the inputs
            padding = True

        is_batched = bool(
            isinstance(raw_audio, (list, tuple)) and (isinstance(raw_audio[0], (np.ndarray, tuple, list)))
        )

        if is_batched:
            raw_audio = [np.asarray(audio, dtype=np.float32).T for audio in raw_audio]
        elif not is_batched and not isinstance(raw_audio, np.ndarray):
            raw_audio = np.asarray(raw_audio, dtype=np.float32)
        elif isinstance(raw_audio, np.ndarray) and raw_audio.dtype is np.dtype(np.float64):
            raw_audio = raw_audio.astype(np.float32)

        # always return batch
        if not is_batched:
            raw_audio = [np.asarray(raw_audio).T]

        if isinstance(raw_audio, list):
            raw_audio = [self._reflect_pad(x) for x in raw_audio]
        else:
            raw_audio = self._reflect_pad(raw_audio)

        # verify inputs are valid
        for example in raw_audio:
            if example.ndim > 2:
                raise ValueError(f"Expected input shape (channels, length) but got shape {example.shape}")
            if self.feature_size == 1 and example.ndim != 1:
                raise ValueError(f"Expected mono audio but example has {example.shape[-1]} channels")
            if self.feature_size == 2:
                raise ValueError("Stereo audio isn't supported for now")

        input_values = BatchFeature({"input_values": raw_audio})

        # normal padding on batch
        padded_inputs = self.pad(
            input_values,
            max_length=max_length,
            truncation=truncation,
            padding=padding,
            return_attention_mask=padding,
            pad_to_multiple_of=self.hop_length,
        )
        if padding:
            padded_inputs["padding_mask"] = padded_inputs.pop("attention_mask")
        if padding:
            padded_inputs.input_values = padded_inputs.input_values[:, np.newaxis, :]

        input_values = []
        for example in padded_inputs.pop("input_values"):
            if self.feature_size == 1:
                example = example[..., None]
            input_values.append(example.T)

        padded_inputs["input_values"] = input_values
        if return_tensors is not None:
            padded_inputs = padded_inputs.convert_to_tensors(return_tensors)

        return padded_inputs