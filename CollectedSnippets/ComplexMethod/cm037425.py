def gather_mm_embeddings(
        self,
        req_ids: list[str],
        total_num_scheduled_tokens: int,
        num_scheduled_tokens: np.ndarray,
        query_start_loc: np.ndarray,
        prefill_lens: np.ndarray,
        computed_prefill_lens: np.ndarray,
    ) -> tuple[list[torch.Tensor], torch.Tensor]:
        is_prefilling = (computed_prefill_lens < prefill_lens).tolist()
        all_decode = not any(is_prefilling)
        if all_decode:
            # All decode requests, so no need to gather any embeddings.
            return [], torch.zeros(
                total_num_scheduled_tokens, dtype=torch.bool, device=self.device
            )

        query_start = computed_prefill_lens.tolist()
        query_end = (computed_prefill_lens + num_scheduled_tokens).tolist()

        mm_embeds: list[torch.Tensor] = []
        is_mm_embed = torch.zeros(
            total_num_scheduled_tokens, dtype=torch.bool, device="cpu"
        )
        for i, req_id in enumerate(req_ids):
            if not is_prefilling[i]:
                # OPTIMIZATION: Skip decode requests.
                continue

            mm_features = self.encoder_cache.mm_features[req_id]
            for mm_feature in mm_features:
                pos_info = mm_feature.mm_position
                start_pos = pos_info.offset
                num_encoder_tokens = pos_info.length

                if start_pos >= query_end[i]:
                    # The encoder output is not needed in this step.
                    break
                if start_pos + num_encoder_tokens <= query_start[i]:
                    # The encoder output is already processed and stored
                    # in the decoder's KV cache.
                    continue

                start_idx = max(query_start[i] - start_pos, 0)
                end_idx = min(query_end[i] - start_pos, num_encoder_tokens)
                assert start_idx < end_idx
                curr_embeds_start, curr_embeds_end = (
                    pos_info.get_embeds_indices_in_range(start_idx, end_idx)
                )
                # If there are no embeddings in the current range, we skip
                # gathering the embeddings.
                if curr_embeds_start == curr_embeds_end:
                    continue

                mm_hash = mm_feature.identifier
                encoder_output = self.encoder_cache.encoder_outputs.get(mm_hash, None)
                assert encoder_output is not None, f"Encoder cache miss for {mm_hash}."

                if (is_embed := pos_info.is_embed) is not None:
                    is_embed = is_embed[start_idx:end_idx]
                    mm_embeds_item = encoder_output[curr_embeds_start:curr_embeds_end]
                else:
                    mm_embeds_item = encoder_output[start_idx:end_idx]

                req_start_pos = query_start_loc[i] + start_pos - query_start[i]
                is_mm_embed[req_start_pos + start_idx : req_start_pos + end_idx] = (
                    True if is_embed is None else is_embed
                )
                mm_embeds.append(mm_embeds_item)

        return mm_embeds, is_mm_embed