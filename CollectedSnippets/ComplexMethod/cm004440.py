def __call__(
        self,
        audio: np.ndarray | list[float] | list[np.ndarray] | list[list[float]] | None = None,
        audio_target: np.ndarray | list[float] | list[np.ndarray] | list[list[float]] | None = None,
        padding: bool | str | PaddingStrategy = False,
        max_length: int | None = None,
        truncation: bool = False,
        pad_to_multiple_of: int | None = None,
        return_attention_mask: bool | None = None,
        return_tensors: str | TensorType | None = None,
        sampling_rate: int | None = None,
        **kwargs,
    ) -> BatchFeature:
        """
        Main method to featurize and prepare for the model one or several sequence(s).

        Pass in a value for `audio` to extract waveform features. Pass in a value for `audio_target` to extract log-mel
        spectrogram features.

        Args:
            audio (`np.ndarray`, `list[float]`, `list[np.ndarray]`, `list[list[float]]`, *optional*):
                The sequence or batch of sequences to be processed. Each sequence can be a numpy array, a list of float
                values, a list of numpy arrays or a list of list of float values. This outputs waveform features. Must
                be mono channel audio, not stereo, i.e. single float per timestep.
            audio_target (`np.ndarray`, `list[float]`, `list[np.ndarray]`, `list[list[float]]`, *optional*):
                The sequence or batch of sequences to be processed as targets. Each sequence can be a numpy array, a
                list of float values, a list of numpy arrays or a list of list of float values. This outputs log-mel
                spectrogram features.
            padding (`bool`, `str` or [`~utils.PaddingStrategy`], *optional*, defaults to `False`):
                Select a strategy to pad the returned sequences (according to the model's padding side and padding
                index) among:

                - `True` or `'longest'`: Pad to the longest sequence in the batch (or no padding if only a single
                  sequence if provided).
                - `'max_length'`: Pad to a maximum length specified with the argument `max_length` or to the maximum
                  acceptable input length for the model if that argument is not provided.
                - `False` or `'do_not_pad'` (default): No padding (i.e., can output a batch with sequences of different
                  lengths).
            max_length (`int`, *optional*):
                Maximum length of the returned list and optionally padding length (see above).
            truncation (`bool`):
                Activates truncation to cut input sequences longer than *max_length* to *max_length*.
            pad_to_multiple_of (`int`, *optional*):
                If set will pad the sequence to a multiple of the provided value.

                This is especially useful to enable the use of Tensor Cores on NVIDIA hardware with compute capability
                `>= 7.5` (Volta), or on TPUs which benefit from having sequence lengths be a multiple of 128.
            return_attention_mask (`bool`, *optional*):
                Whether to return the attention mask. If left to the default, will return the attention mask according
                to the specific feature_extractor's default.

                [What are attention masks?](../glossary#attention-mask)

            return_tensors (`str` or [`~utils.TensorType`], *optional*):
                If set, will return tensors instead of list of python integers. Acceptable values are:

                - `'pt'`: Return PyTorch `torch.Tensor` objects.
                - `'np'`: Return Numpy `np.ndarray` objects.
            sampling_rate (`int`, *optional*):
                The sampling rate at which the `audio` or `audio_target` input was sampled. It is strongly recommended
                to pass `sampling_rate` at the forward call to prevent silent errors.
        """
        if audio is None and audio_target is None:
            raise ValueError("You must provide either `audio` or `audio_target` values.")

        if sampling_rate is not None:
            if sampling_rate != self.sampling_rate:
                raise ValueError(
                    f"The model corresponding to this feature extractor: {self} was trained using a sampling rate of"
                    f" {self.sampling_rate}. Please make sure that the provided audio input was sampled with"
                    f" {self.sampling_rate} and not {sampling_rate}."
                )
        else:
            logger.warning(
                f"It is strongly recommended to pass the `sampling_rate` argument to `{self.__class__.__name__}()`. "
                "Failing to do so can result in silent errors that might be hard to debug."
            )

        if audio is not None:
            inputs = self._process_audio(
                audio,
                False,
                padding,
                max_length,
                truncation,
                pad_to_multiple_of,
                return_attention_mask,
                return_tensors,
                **kwargs,
            )
        else:
            inputs = None

        if audio_target is not None:
            inputs_target = self._process_audio(
                audio_target,
                True,
                padding,
                max_length,
                truncation,
                pad_to_multiple_of,
                return_attention_mask,
                return_tensors,
                **kwargs,
            )

            if inputs is None:
                return inputs_target
            else:
                inputs["labels"] = inputs_target["input_values"]
                decoder_attention_mask = inputs_target.get("attention_mask")
                if decoder_attention_mask is not None:
                    inputs["decoder_attention_mask"] = decoder_attention_mask

        return inputs