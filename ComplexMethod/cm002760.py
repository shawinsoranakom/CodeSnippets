def __call__(
        self,
        raw_speech: np.ndarray | list[float] | list[np.ndarray] | list[list[float]],
        sampling_rate: int | None = None,
        padding: bool | str | PaddingStrategy = True,
        max_length: int | None = None,
        truncation: bool = True,
        pad_to_multiple_of: int | None = None,
        return_noise: bool = True,
        generator: np.random.Generator | None = None,
        pad_end: bool = False,
        pad_length: int | None = None,
        do_normalize: str | None = None,
        return_attention_mask: bool | None = None,
        return_tensors: str | TensorType | None = None,
    ) -> BatchFeature:
        """
        Main method to featurize and prepare for the model one or several sequence(s).

        Args:
            raw_speech (`np.ndarray`, `list[float]`, `list[np.ndarray]`, `list[list[float]]`):
                The sequence or batch of sequences to be padded. Each sequence can be a numpy array, a list of float
                values, a list of numpy arrays or a list of list of float values. Must be mono channel audio, not
                stereo, i.e. single float per timestep.
            sampling_rate (`int`, *optional*):
                The sampling rate at which the `raw_speech` input was sampled. It is strongly recommended to pass
                `sampling_rate` at the forward call to prevent silent errors and allow automatic speech recognition
                pipeline.
            padding (`bool`, `str` or [`~utils.PaddingStrategy`], *optional*, defaults to `True`):
                Select a strategy to pad the input `raw_speech` waveforms (according to the model's padding side and
                padding index) among:

                - `True` or `'longest'`: Pad to the longest sequence in the batch (or no padding if only a single
                  sequence if provided).
                - `'max_length'`: Pad to a maximum length specified with the argument `max_length` or to the maximum
                  acceptable input length for the model if that argument is not provided.
                - `False` or `'do_not_pad'` (default): No padding (i.e., can output a batch with sequences of different
                  lengths).

                If `pad_end = True`, that padding will occur before the `padding` strategy is applied.
            max_length (`int`, *optional*):
                Maximum length of the returned list and optionally padding length (see above).
            truncation (`bool`, *optional*, defaults to `True`):
                Activates truncation to cut input sequences longer than `max_length` to `max_length`.
            pad_to_multiple_of (`int`, *optional*):
                If set will pad the sequence to a multiple of the provided value.

                This is especially useful to enable the use of Tensor Cores on NVIDIA hardware with compute capability
                `>= 7.5` (Volta), or on TPUs which benefit from having sequence lengths be a multiple of 128.
            return_noise (`bool`, *optional*, defaults to `True`):
                Whether to generate and return a noise waveform for use in [`UnivNetModel.forward`].
            generator (`numpy.random.Generator`, *optional*, defaults to `None`):
                An optional `numpy.random.Generator` random number generator to use when generating noise.
            pad_end (`bool`, *optional*, defaults to `False`):
                Whether to pad the end of each waveform with silence. This can help reduce artifacts at the end of the
                generated audio sample; see https://github.com/seungwonpark/melgan/issues/8 for more details. This
                padding will be done before the padding strategy specified in `padding` is performed.
            pad_length (`int`, *optional*, defaults to `None`):
                If padding the end of each waveform, the length of the padding in spectrogram frames. If not set, this
                will default to `self.config.pad_end_length`.
            do_normalize (`bool`, *optional*):
                Whether to perform Tacotron 2 normalization on the input. Normalizing can help to significantly improve
                the performance for some models. If not set, this will default to `self.config.do_normalize`.
            return_attention_mask (`bool`, *optional*):
                Whether to return the attention mask. If left to the default, will return the attention mask according
                to the specific feature_extractor's default.

                [What are attention masks?](../glossary#attention-mask)

            return_tensors (`str` or [`~utils.TensorType`], *optional*):
                If set, will return tensors instead of list of python integers. Acceptable values are:

                - `'pt'`: Return PyTorch `torch.np.array` objects.
                - `'np'`: Return Numpy `np.ndarray` objects.
        """
        do_normalize = do_normalize if do_normalize is not None else self.do_normalize

        if sampling_rate is not None:
            if sampling_rate != self.sampling_rate:
                raise ValueError(
                    f"The model corresponding to this feature extractor: {self.__class__.__name__} was trained using a"
                    f" sampling rate of {self.sampling_rate}. Please make sure that the provided `raw_speech` input"
                    f" was sampled with {self.sampling_rate} and not {sampling_rate}."
                )
        else:
            logger.warning(
                f"It is strongly recommended to pass the `sampling_rate` argument to `{self.__class__.__name__}()`. "
                "Failing to do so can result in silent errors that might be hard to debug."
            )

        is_batched_numpy = isinstance(raw_speech, np.ndarray) and len(raw_speech.shape) > 1
        if is_batched_numpy and len(raw_speech.shape) > 2:
            raise ValueError(f"Only mono-channel audio is supported for input to {self}")
        is_batched = is_batched_numpy or (
            isinstance(raw_speech, (list, tuple)) and (isinstance(raw_speech[0], (np.ndarray, tuple, list)))
        )

        if is_batched:
            raw_speech = [np.asarray(speech, dtype=np.float32) for speech in raw_speech]
        elif not is_batched and not isinstance(raw_speech, np.ndarray):
            raw_speech = np.asarray(raw_speech, dtype=np.float32)
        elif isinstance(raw_speech, np.ndarray) and raw_speech.dtype is np.dtype(np.float64):
            raw_speech = raw_speech.astype(np.float32)

        # always return batch
        if not is_batched:
            raw_speech = [np.asarray(raw_speech, dtype=np.float32)]

        # Pad end to reduce artifacts
        if pad_end:
            pad_length = pad_length if pad_length is not None else self.pad_end_length
            raw_speech = [
                np.pad(waveform, (0, pad_length * self.hop_length), constant_values=self.padding_value)
                for waveform in raw_speech
            ]

        batched_speech = BatchFeature({"input_features": raw_speech})

        padded_inputs = self.pad(
            batched_speech,
            padding=padding,
            max_length=max_length if max_length is not None else self.num_max_samples,
            truncation=truncation,
            pad_to_multiple_of=pad_to_multiple_of,
            return_attention_mask=return_attention_mask,
        )

        # make sure list is in array format
        # input_features = padded_inputs.get("input_features").transpose(2, 0, 1)
        input_features = padded_inputs.get("input_features")

        mel_spectrograms = [self.mel_spectrogram(waveform) for waveform in input_features]

        if isinstance(input_features[0], list):
            batched_speech["input_features"] = [np.asarray(mel, dtype=np.float32) for mel in mel_spectrograms]
        else:
            batched_speech["input_features"] = [mel.astype(np.float32) for mel in mel_spectrograms]

        # convert attention_mask to correct format
        attention_mask = padded_inputs.get("attention_mask")
        if attention_mask is not None:
            batched_speech["padding_mask"] = [np.asarray(array, dtype=np.int32) for array in attention_mask]

        if return_noise:
            noise = [
                self.generate_noise(spectrogram.shape[0], generator)
                for spectrogram in batched_speech["input_features"]
            ]
            batched_speech["noise_sequence"] = noise

        if do_normalize:
            batched_speech["input_features"] = [
                self.normalize(spectrogram) for spectrogram in batched_speech["input_features"]
            ]

        if return_tensors is not None:
            batched_speech = batched_speech.convert_to_tensors(return_tensors)

        return batched_speech