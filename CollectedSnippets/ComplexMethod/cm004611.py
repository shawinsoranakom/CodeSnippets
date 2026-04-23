def __call__(
        self,
        raw_speech: AudioInput,
        sampling_rate: int | None = None,
        pad_to_multiple_of: int | None = None,
        padding: str | None = "longest",
        max_length: int | None = None,
        truncation: bool = False,
        return_tensors: str | TensorType | None = None,
        return_attention_mask: bool | None = True,
        device: str | None = "cpu",
        **kwargs,
    ) -> BatchFeature:
        """
        Main method to featurize and prepare for the model one or several audio sequence(s). Implementation uses PyTorch for
        the STFT computation if available, otherwise a slower NumPy based one.

        Args:
            raw_speech (`np.ndarray`, `torch.Tensor`, `list[np.ndarray]`, `list[torch.Tensor]`):
                The sequence or batch of sequences to be processed. Each sequence can be a numpy array or PyTorch tensor.
                For batched inputs, sequences can be a list of numpy arrays or PyTorch tensors, or a single numpy array or
                PyTorch tensor with first dimension being the batch size.
            sampling_rate (`int`, *optional*):
                The sampling rate at which the `raw_speech` input was sampled. It is strongly recommended to pass
                `sampling_rate` at the forward call to prevent silent errors.
            pad_to_multiple_of (`int`, *optional*, defaults to None):
                If set will pad the sequence to a multiple of the provided value.
            padding (`str`, *optional*, defaults to "longest"):
                Padding strategy. Can be "longest" to pad to the longest sequence in the batch, or a specific length.
            max_length (`int`, *optional*):
                Maximum length of the returned list and optionally padding length.
            truncation (`bool`, *optional*, defaults to False):
                Activates truncation to cut input sequences longer than *max_length* to *max_length*.
            return_tensors (`str` or [`~utils.TensorType`], *optional*):
                If set, will return tensors instead of numpy arrays. Acceptable values are:
                - `'pt'`: Return PyTorch `torch.Tensor` objects.
                - `'np'`: Return Numpy `np.ndarray` objects.
            return_attention_mask (`bool`, *optional*, defaults to `True`):
                Whether to return the extracted audio input features' attention mask.
            device (`str`, *optional*, defaults to "cpu"):
                Specifies the device for computation of the audio features. (e.g., "cpu", "cuda")

        Returns:
            [`BatchFeature`]: A [`BatchFeature`] with the following fields:
                - **audio_input_features** -- Audio features extracted from the raw audio input, shape (batch_size, max_feature_length, feature_size).
                - **audio_lengths** -- Length of each audio sample in the batch, shape (batch_size,).
                - **audio_attention_mask** -- Attention mask for the audio input, shape (batch_size, max_feature_length).
                If `return_tensors` is not specified, the fields will be PyTorch tensors if PyTorch is available, otherwise NumPy arrays.
        """
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

        # Convert to torch tensor
        if isinstance(raw_speech, np.ndarray):
            raw_speech = torch.tensor(raw_speech)
        elif isinstance(raw_speech, (list, tuple)) and isinstance(raw_speech[0], np.ndarray):
            raw_speech = [torch.tensor(speech) for speech in raw_speech]

        is_batched_torch = isinstance(raw_speech, torch.Tensor) and len(raw_speech.shape) > 1
        if is_batched_torch and len(raw_speech.shape) > 2:
            logger.warning(
                f"Only mono-channel audio is supported for input to {self.__class__.__name__}. "
                "We will take the mean of the channels to convert to mono."
            )
            raw_speech = raw_speech.mean(-1)

        is_batched_sequence = isinstance(raw_speech, (list, tuple))
        if is_batched_sequence:
            for speech in raw_speech:
                if len(speech.shape) > 1:
                    logger.warning(
                        f"Only mono-channel audio is supported for input to {self.__class__.__name__}. "
                        "We will take the mean of the channels to convert to mono."
                    )
                    speech = speech.mean(-1)

        if is_batched_torch or is_batched_sequence:
            raw_speech = [speech[:, None].to(torch.float32) for speech in raw_speech]
        else:
            raw_speech = [raw_speech[:, None].to(torch.float32)]

        audio_lengths = [len(speech) for speech in raw_speech]

        # convert into correct format for padding
        batched_speech = BatchFeature(data={"audio_input_features": raw_speech, "audio_lengths": audio_lengths})
        padded_inputs = self.pad(
            batched_speech,
            padding=padding,
            max_length=max_length,
            truncation=truncation,
            pad_to_multiple_of=pad_to_multiple_of,
            return_tensors="pt",
        )
        input_features = padded_inputs.audio_input_features.squeeze(-1)
        audio_lengths = padded_inputs.audio_lengths

        input_features = self._torch_extract_fbank_features(input_features, audio_lengths, device)

        feature_lengths = (audio_lengths - self.win_length) // self.hop_length + 1
        feature_lengths = feature_lengths * self.audio_feat_stride
        audio_embed_sizes = self._compute_audio_embed_size(feature_lengths)

        feature_attention_mask = (
            torch.arange(0, feature_lengths.max()) if is_torch_available() else np.arange(0, feature_lengths.max())
        )
        feature_attention_mask = (
            feature_attention_mask[None, :] < feature_lengths[:, None] if len(feature_lengths) > 1 else None
        )

        data = {
            "audio_input_features": input_features,
            "audio_embed_sizes": audio_embed_sizes,
        }
        if feature_attention_mask is not None and return_attention_mask:
            data["audio_attention_mask"] = feature_attention_mask

        return BatchFeature(data=data, tensor_type=return_tensors)