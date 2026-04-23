def __call__(
        self,
        text=None,
        voice_preset=None,
        return_tensors="pt",
        max_length=256,
        add_special_tokens=False,
        return_attention_mask=True,
        return_token_type_ids=False,
        **kwargs,
    ) -> BatchEncoding:
        r"""
        voice_preset (`str`, `dict[np.ndarray]`):
            The voice preset, i.e the speaker embeddings. It can either be a valid voice_preset name, e.g
            `"en_speaker_1"`, or directly a dictionary of `np.ndarray` embeddings for each submodel of `Bark`. Or
            it can be a valid file name of a local `.npz` single voice preset containing the keys
            `"semantic_prompt"`, `"coarse_prompt"` and `"fine_prompt"`.

        Returns:
            [`BatchEncoding`]: A [`BatchEncoding`] object containing the output of the `tokenizer`.
            If a voice preset is provided, the returned object will include a `"history_prompt"` key
            containing a [`BatchFeature`], i.e the voice preset with the right tensors type.
        """
        if voice_preset is not None and not isinstance(voice_preset, dict):
            if (
                isinstance(voice_preset, str)
                and self.speaker_embeddings is not None
                and voice_preset in self.speaker_embeddings
            ):
                voice_preset = self._load_voice_preset(voice_preset)

            else:
                if isinstance(voice_preset, str) and not voice_preset.endswith(".npz"):
                    voice_preset = voice_preset + ".npz"

                voice_preset = np.load(voice_preset)

        if voice_preset is not None:
            self._validate_voice_preset_dict(voice_preset, **kwargs)
            voice_preset = BatchFeature(data=voice_preset, tensor_type=return_tensors)

        encoded_text = self.tokenizer(
            text,
            return_tensors=return_tensors,
            padding="max_length",
            max_length=max_length,
            return_attention_mask=return_attention_mask,
            return_token_type_ids=return_token_type_ids,
            add_special_tokens=add_special_tokens,
            **kwargs,
        )

        if voice_preset is not None:
            encoded_text["history_prompt"] = voice_preset

        return encoded_text