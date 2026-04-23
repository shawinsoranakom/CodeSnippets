def __call__(
        self,
        text: TextInput
        | PreTokenizedInput
        | list[TextInput]
        | list[PreTokenizedInput]
        | None = None,
        audio: AudioInput | None = None,
        return_tensors: str = "pt",
        **kwargs,
    ) -> BatchFeature:
        if text is not None:
            if not isinstance(text, list):
                text = [text]

            text_inputs = self.tokenizer(
                text, return_tensors=return_tensors, padding=True
            )
        else:
            text_inputs = {}

        if audio is not None:
            # Ensure audio is a list
            if isinstance(audio, np.ndarray):
                audio = [audio]

            # Pad audio to hop length (required by WhisperFeatureExtractor)
            hop_length = self.feature_extractor.hop_length
            padded_audio = []
            for aud in audio:
                length = aud.shape[-1]
                if length % hop_length != 0:
                    pad_length = hop_length - (length % hop_length)
                    aud = np.pad(
                        aud, (0, pad_length), mode="constant", constant_values=0
                    )
                padded_audio.append(aud)

            # Use feature_extractor directly like Qwen3ASR does
            audio_inputs = self.feature_extractor(
                padded_audio,
                sampling_rate=16000,
                padding=True,
                return_attention_mask=True,
                return_tensors=return_tensors,
            )
            # Rename to match Kimi-Audio expectations
            if "input_features" in audio_inputs:
                audio_inputs["whisper_input_features"] = audio_inputs.pop(
                    "input_features"
                )
            if "attention_mask" in audio_inputs:
                audio_inputs["feature_attention_mask"] = audio_inputs.pop(
                    "attention_mask"
                )
        else:
            audio_inputs = {}

        return BatchFeature(
            data={**text_inputs, **audio_inputs},
            tensor_type=return_tensors,
        )