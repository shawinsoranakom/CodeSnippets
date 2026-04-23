def _call_hf_processor(
        self,
        prompt: str,
        mm_data: dict[str, object],
        mm_kwargs: Mapping[str, Any],
        tok_kwargs: Mapping[str, object],
    ) -> BatchFeature:
        audios = mm_data.pop("audios", [])
        if audios:
            mm_data["audio"] = audios

        if not mm_data.get("audio", []):
            prompt_ids = self.info.get_tokenizer().encode(prompt)
            prompt_ids = self._apply_hf_processor_tokens_only(prompt_ids)
            return BatchFeature(dict(input_ids=[prompt_ids]), tensor_type="pt")

        processor = self.info.get_hf_processor(**mm_kwargs)
        feature_extractor = processor.feature_extractor
        mm_kwargs = dict(
            **mm_kwargs,
            sampling_rate=feature_extractor.sampling_rate,
        )

        audio_list = mm_data.get("audio")
        if not isinstance(audio_list, list):
            audio_list = [audio_list]

        chunk_counts = []
        sampling_rate = feature_extractor.sampling_rate
        chunk_length = feature_extractor.chunk_length
        window_size = int(sampling_rate * chunk_length)
        max_windows = int(processor.max_audio_len // chunk_length)

        for audio in audio_list:
            # audio is numpy array or list
            n_samples = len(audio) if isinstance(audio, list) else audio.shape[0]

            n_win = max(1, (n_samples + window_size - 1) // window_size)
            if n_win > max_windows:
                n_win = max_windows
            chunk_counts.append(n_win)

        outputs = super()._call_hf_processor(
            prompt=prompt,
            mm_data=mm_data,
            mm_kwargs=mm_kwargs,
            tok_kwargs=tok_kwargs,
        )

        if "input_features_mask" in outputs:
            outputs["feature_attention_mask"] = outputs.pop("input_features_mask")

        outputs["chunk_counts"] = torch.tensor(chunk_counts, dtype=torch.long)

        return outputs