def _maybe_apply_prompt_updates(
        self,
        mm_items: MultiModalDataItems,
        prompt_ids: list[int],
        mm_kwargs: MultiModalKwargsOptionalItems,
        mm_prompt_updates: MultiModalPromptUpdates,
        is_update_applied: bool,
    ) -> tuple[list[int], Mapping[str, list[PlaceholderFeaturesInfo]]]:
        audios = mm_kwargs.get("audio", [])
        assert len(audios) == 1, (
            f"Expected only one audio input for realtime, got {len(audios)}"
        )

        audio_data = audios[0]
        audio_feature_lengths = audio_data.get("audio_feature_lengths")
        if audio_feature_lengths is not None:
            if isinstance(audio_feature_lengths.data, torch.Tensor):
                audio_len = _get_feat_extract_output_lengths(
                    audio_feature_lengths.data
                ).item()
            else:
                audio_len = int(
                    _get_feat_extract_output_lengths(
                        torch.tensor(audio_feature_lengths.data)
                    ).item()
                )
        else:
            audio_len = 0

        # Get audio_pad token ID and expand placeholder in prompt_ids
        # so that MRoPE position computation matches seq_len.
        tokenizer = self.info.get_tokenizer()
        audio_pad_id = tokenizer.convert_tokens_to_ids("<|audio_pad|>")

        # Find the audio_pad token position and expand it to audio_len tokens
        expanded_ids = list[int]()
        pad_start_idx = -1
        for i, tid in enumerate(prompt_ids):
            if tid == audio_pad_id and pad_start_idx == -1:
                pad_start_idx = i
                expanded_ids.extend([audio_pad_id] * audio_len)
            else:
                expanded_ids.append(tid)

        if pad_start_idx == -1:
            pad_start_idx = 0

        features_info = PlaceholderFeaturesInfo(
            modality="audio",
            item_idx=0,
            start_idx=pad_start_idx,
            tokens=audio_len * [audio_pad_id],
            is_embed=None,
        )
        return expanded_ids, {"audio": [features_info]}