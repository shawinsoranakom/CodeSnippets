def _call_hf_processor(
        self,
        prompt: str,
        mm_data: Mapping[str, object],
        mm_kwargs: Mapping[str, object],
        tok_kwargs: Mapping[str, object],
    ) -> BatchFeature:
        tokenizer = self.info.get_tokenizer()
        input_ids = torch.tensor([tokenizer.encode(prompt, **tok_kwargs)])

        audios = mm_data.get("audios", [])
        if not audios:
            return BatchFeature({"input_ids": input_ids})

        feature_extractor = self.info.get_feature_extractor(**mm_kwargs)
        sr = int(feature_extractor.sampling_rate)
        min_samples = int(getattr(feature_extractor, "n_fft", 400) or 400)

        wavs: list[np.ndarray] = []
        speech_strs: list[str] = []

        speech_tokenizer = self.info.get_speech_tokenizer()
        pad_token = speech_tokenizer.pad_token or "<|audio_pad|>"
        for audio in audios:
            if isinstance(audio, torch.Tensor):
                audio = audio.detach().cpu().numpy()
            audio_np = np.asarray(audio, dtype=np.float32)

            if min_samples > 0 and audio_np.shape[0] < min_samples:
                audio_np = np.pad(
                    audio_np, (0, min_samples - audio_np.shape[0]), mode="constant"
                )

            wavs.append(audio_np)
            num_frames = int(
                (float(audio_np.shape[0]) / float(sr)) * float(self.info.token_fps)
            )
            speech_strs.append(pad_token * max(1, int(num_frames)))

        audio_group_size = self.info.get_audio_group_size()
        speech_inputs = speech_tokenizer(
            speech_strs,
            return_attention_mask=True,
            return_token_type_ids=False,
            padding=True,
            pad_to_multiple_of=audio_group_size,
            return_tensors="pt",
        )

        wav_inputs = feature_extractor(
            wavs,
            sampling_rate=sr,
            return_attention_mask=True,
            padding="max_length",
            return_tensors="pt",
        )

        mm_inputs: dict[str, torch.Tensor] = {
            "speech_ids": speech_inputs["input_ids"],
            "speech_attention_mask": speech_inputs["attention_mask"],
            "input_features": wav_inputs["input_features"],
            "feature_attention_mask": wav_inputs["attention_mask"],
            "feature_exist_mask": torch.ones((len(wavs),), dtype=torch.bool),
        }

        return BatchFeature({"input_ids": input_ids, **mm_inputs})