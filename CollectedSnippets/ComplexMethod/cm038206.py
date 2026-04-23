def _get_prompt_updates(
        self,
        mm_items: MultiModalDataItems,
        hf_processor_mm_kwargs: Mapping[str, object],
        out_mm_kwargs: MultiModalKwargsItems,
    ) -> Sequence[PromptUpdate]:
        processor = self.info.get_hf_processor(**hf_processor_mm_kwargs)
        tokenizer = self.info.get_tokenizer()
        vocab = tokenizer.get_vocab()
        config = self.info.get_hf_config()

        audio_token = getattr(processor, "audio_token", "<|pad|>")
        audio_token_id = vocab.get(audio_token)
        if audio_token_id is None:
            audio_token_id = processor.audio_token_id

        merge_factor = getattr(config, "merge_factor", DEFAULT_MERGE_FACTOR)
        conv_params = getattr(config, "conv_params", DEFAULT_CONV_PARAMS)
        out_mm_data = out_mm_kwargs.get_data()
        feature_attention_mask = out_mm_data.get("feature_attention_mask")
        chunk_counts = out_mm_data.get("chunk_counts")

        # Pre-compute audio output lengths if feature_attention_mask is available
        audio_output_lengths: list[int] = []
        if feature_attention_mask is not None:
            # Compute output lengths for all audio items
            from .glmasr_utils import (
                _as_list_chunk_counts,
                _get_audio_output_lengths_from_mask,
            )

            if chunk_counts is not None:
                start_idx = 0
                for count in _as_list_chunk_counts(chunk_counts):
                    end_idx = start_idx + count
                    mask = feature_attention_mask[start_idx:end_idx]
                    if isinstance(mask, list):
                        mask = torch.stack(mask)

                    lengths = _get_audio_output_lengths_from_mask(
                        mask, merge_factor, conv_params
                    )
                    audio_output_lengths.append(int(lengths.sum().item()))
                    start_idx = end_idx
            else:
                # Single chunk per audio
                for idx in range(len(feature_attention_mask)):
                    mask = feature_attention_mask[idx : idx + 1]
                    if isinstance(mask, list):
                        mask = torch.tensor(mask).unsqueeze(0)
                    lengths = _get_audio_output_lengths_from_mask(
                        mask, merge_factor, conv_params
                    )
                    audio_output_lengths.append(int(lengths.sum().item()))

        def get_replacement_glmasr(item_idx: int):
            # Use pre-computed lengths if available, otherwise fall back to audio_embeds
            if audio_output_lengths:
                num_features = audio_output_lengths[item_idx]
            else:
                audio_embeds = out_mm_data.get("audio_embeds")
                if audio_embeds is not None:
                    embed = audio_embeds[item_idx]
                    num_features = embed.shape[0]
                else:
                    raise ValueError(
                        "Either feature_attention_mask or audio_embeds must be provided"
                    )

            if num_features == 0:
                raise ValueError("Audio is too short")

            audio_tokens = [audio_token_id] * int(num_features)
            return PromptUpdateDetails.select_token_id(
                audio_tokens,
                embed_token_id=audio_token_id,
            )

        return [
            PromptReplacement(
                modality="audio",
                target=audio_token,
                replacement=get_replacement_glmasr,
            )
        ]