def apply_transcription_request(
        self,
        audio: str | list[str] | AudioInput,
        prompt: str | list[str] | None = None,
        **kwargs: Unpack[VibeVoiceAsrProcessorKwargs],
    ) -> BatchFeature:
        """
        Prepare inputs for automatic speech recognition without manually writing the chat template.

        Args:
            audio (`str`, `list[str]`, `np.ndarray`, `torch.Tensor`, `list[np.ndarray]`, `list[torch.Tensor]`):
                Audio to transcribe. Strings are interpreted as local paths or URLs and will be loaded automatically by
                the chat template loader; NumPy arrays and PyTorch tensors are forwarded directly.
            prompt (`str` or `list[str]`, *optional*):
                Custom prompt(s) to include in the user turn as extra context. A list must be the same length as the
                batch. When `None`, no additional context is provided.
            **kwargs:
                Additional keyword arguments forwarded to [`~VibeVoiceAsrProcessor.apply_chat_template`] (for example
                `text_kwargs`, `audio_kwargs`, ...).

        Returns:
            [`BatchFeature`]: Processor outputs ready to be passed to [`VibeVoiceAsrForConditionalGeneration.generate`].
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
            prompts = [None] * batch_size
        elif isinstance(prompt, str):
            prompts = [prompt] * batch_size
        elif isinstance(prompt, (list, tuple)):
            if len(prompt) != batch_size:
                raise ValueError(
                    f"Received {len(prompt)} prompt(s) for {batch_size} audio sample(s); counts must match."
                )
            prompts = list(prompt)
        else:
            raise TypeError("`prompt` must be a string, a sequence of strings, or `None`.")

        conversations = []
        for prompt_text, audio_item in zip(prompts, audio_items):
            content = []
            if isinstance(audio_item, str):
                content.append({"type": "audio", "path": audio_item})
            else:
                content.append({"type": "audio", "audio": audio_item})

            if prompt_text is not None:
                content.append({"type": "text", "text": prompt_text})

            conversations.append([{"role": "user", "content": content}])

        return self.apply_chat_template(
            conversations,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            **kwargs,
        )