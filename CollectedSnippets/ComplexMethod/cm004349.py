def apply_transcription_request(
        self,
        audio: str | list[str] | AudioInput,
        prompt: str | list[str] | None = None,
        **kwargs: Unpack[GlmAsrProcessorKwargs],
    ) -> BatchFeature:
        """
        Prepare inputs for automatic speech recognition without manually writing the default transcription prompt.

        Args:
            audio (`str`, `list[str]`, `np.ndarray`, `torch.Tensor`, `list[np.ndarray]`, `list[torch.Tensor]`):
                Audio to transcribe. Strings are interpreted as local paths or URLs and will be loaded automatically by
                the chat template loader; NumPy arrays and PyTorch tensors are forwarded directly.
            prompt (`str` or `list[str]`, *optional*):
                Custom prompt(s) to include in the user turn. A list must be the same length as the batch. When `None`,
                each sample uses `"Transcribe the input speech."`.
            **kwargs:
                Additional keyword arguments forwarded to [`~GlmAsrProcessor.apply_chat_template`] (for example
                `text_kwargs`, `audio_kwargs`, ...).

        Returns:
            [`BatchFeature`]: Processor outputs ready to be passed to [`GlmAsrForConditionalGeneration.generate`].

        """

        if isinstance(audio, str):
            audio_items: list[str | np.ndarray] = [audio]
        elif isinstance(audio, (list, tuple)) and audio and all(isinstance(el, str) for el in audio):
            audio_items = list(audio)
        else:
            audio_items = list(make_list_of_audio(audio))
            if is_torch_available():
                audio_items = [el.detach().cpu().numpy() if isinstance(el, torch.Tensor) else el for el in audio_items]

        batch_size = len(audio_items)
        if batch_size == 0:
            raise ValueError("`audio` must contain at least one sample.")

        if prompt is None:
            prompts = [self.default_transcription_prompt] * batch_size
        elif isinstance(prompt, str):
            prompts = [prompt] * batch_size
        elif isinstance(prompt, (list, tuple)):
            if len(prompt) != batch_size:
                raise ValueError(
                    f"Received {len(prompt)} prompt(s) for {batch_size} audio sample(s); counts must match."
                )
            prompts = []
            for item in prompt:
                if item is None:
                    prompts.append(self.default_transcription_prompt)
                elif isinstance(item, str):
                    prompts.append(item)
                else:
                    raise TypeError("Each prompt must be a string or `None`.")
        else:
            raise TypeError("`prompt` must be a string, a sequence of strings, or `None`.")

        conversations = [
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "audio", "path": audio_item}
                        if isinstance(audio_item, str)
                        else {"type": "audio", "audio": audio_item},
                        {"type": "text", "text": prompt_text},
                    ],
                }
            ]
            for prompt_text, audio_item in zip(prompts, audio_items)
        ]

        return self.apply_chat_template(
            conversations,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            **kwargs,
        )