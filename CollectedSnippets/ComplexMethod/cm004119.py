def __call__(
        self,
        text: TextInput | list[TextInput],
        audio: AudioInput,
        output_labels: bool | None = False,
        **kwargs: Unpack[VibeVoiceAsrProcessorKwargs],
    ) -> BatchFeature:
        """
        Main method to process text inputs with optional audio samples for ASR.

        This method processes text inputs (typically prepared by apply_chat_template) and optional audio samples
        for transcription. It replaces the audio duration placeholder and expands audio token placeholders based
        on the actual audio length.

        Args:
            text (`str`, `List[str]`):
                The input text(s) to process, typically prepared by apply_chat_template with audio token placeholders.
            audio (`List[Union[str, np.ndarray]]`):
                Audio samples for transcription. Should match the number of audio token placeholders in text.
            output_labels (bool, *optional*, default=False):
                Whether to return labels for training.
            **kwargs:
                Additional keyword arguments passed to the tokenizer and feature extractor.

        Returns:
            [`BatchFeature`]: A dictionary with tokenized text (`input_ids`, `attention_mask`) and
            audio features (`input_features`, `input_features_mask`).
        """
        output_kwargs = self._merge_kwargs(
            VibeVoiceAsrProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        text_kwargs = output_kwargs["text_kwargs"]
        audio_kwargs = output_kwargs["audio_kwargs"]
        return_tensors = text_kwargs.get("return_tensors", None)
        if return_tensors != "pt":
            raise ValueError(f"{self.__class__.__name__} only supports `return_tensors='pt'`.")

        if isinstance(text, str):
            text = [text]
        elif not isinstance(text, (list, tuple)):
            raise ValueError("text input must be a string or list of strings")

        audio = make_list_of_audio(audio)
        if len(text) != len(audio):
            raise ValueError(f"Got {len(text)} text but {len(audio)} audios; they must match 1:1.")
        data = self.feature_extractor(audio, **audio_kwargs)

        # Replace audio duration placeholders in text
        audio_lengths = data["padding_mask"].sum(dim=-1).cpu().numpy()
        audio_durations = audio_lengths / self.feature_extractor.sampling_rate
        audio_duration_pattern = re.compile(re.escape(self.audio_duration_token))
        for i in range(len(text)):
            text[i] = audio_duration_pattern.sub(f"{audio_durations[i]:.2f}", text[i])

        # Expand audio tokens in text
        num_audio_tokens = np.ceil(audio_lengths / audio_kwargs["pad_to_multiple_of"]).astype(int).tolist()
        audio_token_pattern = re.compile(re.escape(self.audio_token))
        for i, num_tokens in enumerate(num_audio_tokens):
            text[i] = audio_token_pattern.sub(self.audio_token * num_tokens, text[i])

        text_inputs = self.tokenizer(text, **text_kwargs)
        data.update(text_inputs)

        if output_labels:
            labels = data["input_ids"].clone()
            labels[labels == self.audio_token_id] = -100
            labels[labels == self.audio_bos_token_id] = -100
            labels[labels == self.audio_eos_token_id] = -100
            labels[labels == self.tokenizer.pad_token_id] = -100
            data["labels"] = labels

        return BatchFeature(data=data, tensor_type=return_tensors)