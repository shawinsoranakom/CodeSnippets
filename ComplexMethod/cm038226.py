def fast_prefill_forward(
        self,
        input_ids: torch.Tensor | None,
        positions: torch.Tensor,
        inputs_embeds: torch.Tensor | None = None,
        per_layer_inputs: torch.Tensor | None = None,
        **kwargs,
    ) -> torch.Tensor:
        logits_indices_padded, num_logits_indices = None, None
        attn_metadata = get_forward_context().attn_metadata

        # attn_metadata is None during dummy runs
        if self.fast_prefill_enabled and attn_metadata is not None:
            assert isinstance(attn_metadata, dict)
            # Last layer is a KV sharing layer
            layer_attn_metadata = attn_metadata[
                self.layers[-1].self_attn.attn.layer_name
            ]
            if isinstance(layer_attn_metadata, KVSharingFastPrefillMetadata):
                logits_indices_padded = layer_attn_metadata.logits_indices_padded
                num_logits_indices = layer_attn_metadata.num_logits_indices

        # Copy inputs for cudagraph
        batch_size = positions.size(0)
        self.positions[:batch_size].copy_(positions)
        self_decoder_hidden_states, per_layer_inputs_adjusted = self.self_decoder(
            input_ids=input_ids,
            positions=self.positions[:batch_size],
            inputs_embeds=inputs_embeds,
            per_layer_inputs=per_layer_inputs,
            **kwargs,
        )

        if logits_indices_padded is None:
            logits_indices_padded = torch.arange(
                positions.size(0),
                dtype=positions.dtype,
                device=positions.device,
            )

        # NOTE(sarckk): There is currently a bug caused by
        # vLLM converting output of last piecewise CUDA graph
        # to weakref, causing memory to be prematurely freed
        # when there are multiple compilation units
        # Keep .clone() until fix in
        # https://github.com/vllm-project/vllm/pull/22282
        hidden_states = self_decoder_hidden_states.clone()

        # Copy inputs for cudagraph
        num_padded_logits_indices = logits_indices_padded.size(0)
        self.positions[:num_padded_logits_indices].copy_(
            positions[logits_indices_padded]
        )
        self.hidden_states[:num_padded_logits_indices].copy_(
            self_decoder_hidden_states[logits_indices_padded]
        )
        self.per_layer_inputs[:num_padded_logits_indices].copy_(
            per_layer_inputs_adjusted[logits_indices_padded]
        )
        cross_decoder_hidden_states = self.cross_decoder(
            positions=self.positions[:num_padded_logits_indices],
            hidden_states=self.hidden_states[:num_padded_logits_indices],
            per_layer_inputs=self.per_layer_inputs[:num_padded_logits_indices],
            **kwargs,
        )

        if num_logits_indices is not None:
            assert num_logits_indices > 0
            # Merge cross-decoder and self-decoder hidden states
            hidden_states[logits_indices_padded[:num_logits_indices]] = (
                cross_decoder_hidden_states[:num_logits_indices]
            )
        else:
            hidden_states = cross_decoder_hidden_states

        return hidden_states