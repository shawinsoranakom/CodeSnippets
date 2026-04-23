def embed_input_ids(
        self,
        input_ids: torch.Tensor,
        multimodal_embeddings: MultiModalEmbeddings | None = None,
        *,
        is_multimodal: torch.Tensor | None = None,
        handle_oov_mm_token: bool = True,
    ) -> torch.Tensor:
        """Merge text and vision embeddings, apply embedding_multiplier.

        HF flow:
        1. inputs_embeds = embed_tokens(input_ids)
        2. inputs_embeds.masked_fill(vision_mask, 0.0)
        3. hidden_states = inputs_embeds * embedding_multiplier
        4. layer loop injects deepstack features at target layers

        multimodal_embeddings contains packed tensors from embed_multimodal():
        shape (num_tokens_i, lm_hidden_size * num_levels). We split on dim=-1
        to get per-level features, build batch-sized buffers (zero at text
        positions), and store in self._ds_features for forward().
        """
        lm_inner = self.language_model.model

        has_vision = (
            multimodal_embeddings is not None
            and is_multimodal is not None
            and len(multimodal_embeddings) > 0
            and is_multimodal.any()
        )

        if not has_vision:
            self._ds_num_tokens = 0
            embeds = lm_inner.embed_input_ids(input_ids)
            return embeds * lm_inner.config.embedding_multiplier

        # 1. Text embeddings
        text_embeds = lm_inner.embed_input_ids(input_ids)

        # 2. Zero image positions (matches HF masked_fill(vision_mask, 0.0))
        text_embeds[is_multimodal] = 0.0

        # 3. Apply embedding_multiplier
        inputs_embeds = text_embeds * lm_inner.config.embedding_multiplier

        # 4. Split packed tensors into per-level features and build buffers.
        #    multimodal_embeddings is a list of per-image packed tensors
        #    (possibly a chunk slice from the framework's encoder cache).
        #    Concatenate along token dim → (total_mm_tokens, lm_h * num_levels).
        N, lm_h = inputs_embeds.shape
        all_packed = torch.cat(
            [t.to(dtype=inputs_embeds.dtype) for t in multimodal_embeddings],
            dim=0,
        )
        level_features = all_packed.split(lm_h, dim=-1)  # num_levels tensors

        # Ensure persistent buffers are on the right device/dtype (first call).
        buf0 = self._ds_buffers[0]
        if buf0.device != inputs_embeds.device or buf0.dtype != inputs_embeds.dtype:
            self._ds_buffers = [
                b.to(device=inputs_embeds.device, dtype=inputs_embeds.dtype)
                for b in self._ds_buffers
            ]

        for level_idx in range(len(self._ds_layer_indices)):
            target = self._ds_buffers[level_idx][:N]
            target.zero_()
            target[is_multimodal] = level_features[level_idx]

        self._ds_num_tokens = N
        return inputs_embeds