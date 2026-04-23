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

        if attn_metadata is not None:
            assert isinstance(attn_metadata, dict)
            layer_attn_metadata = attn_metadata[
                self.layers[-1].self_attn.attn.layer_name
            ]
            if isinstance(layer_attn_metadata, KVSharingFastPrefillMetadata):
                logits_indices_padded = layer_attn_metadata.logits_indices_padded
                num_logits_indices = layer_attn_metadata.num_logits_indices

        batch_size = positions.size(0)
        self.positions[:batch_size].copy_(positions)
        self_decoder_hidden_states, per_layer_inputs = self.self_decoder(
            input_ids=input_ids,
            positions=self.positions[:batch_size],
            inputs_embeds=inputs_embeds,
            per_layer_inputs=per_layer_inputs,
            **kwargs,
        )

        if logits_indices_padded is None:
            logits_indices_padded = torch.arange(
                batch_size,
                dtype=positions.dtype,
                device=positions.device,
            )

        # NOTE: Keep .clone() until fix in
        # https://github.com/vllm-project/vllm/pull/22282
        hidden_states = self_decoder_hidden_states.clone()

        num_padded = logits_indices_padded.size(0)
        self.positions[:num_padded].copy_(positions[logits_indices_padded])
        self.hidden_states[:num_padded].copy_(
            self_decoder_hidden_states[logits_indices_padded]
        )
        if self.per_layer_inputs is not None and per_layer_inputs is not None:
            self.per_layer_inputs[:num_padded].copy_(
                per_layer_inputs[logits_indices_padded]
            )

        # Update batch_descriptor so the cross-decoder's piecewise
        # CUDAGraphWrapper dispatches to the correct (reduced) batch size.
        forward_context = get_forward_context()
        orig_batch_desc = forward_context.batch_descriptor
        if orig_batch_desc is not None:
            forward_context.batch_descriptor = replace(
                orig_batch_desc, num_tokens=num_padded
            )

        cross_per_layer = (
            self.per_layer_inputs[:num_padded]
            if self.per_layer_inputs is not None
            else None
        )
        cross_hidden_states = self.cross_decoder(
            self.positions[:num_padded],
            self.hidden_states[:num_padded],
            cross_per_layer,
            **kwargs,
        )

        # Restore the original batch_descriptor
        forward_context.batch_descriptor = orig_batch_desc

        if num_logits_indices is not None:
            assert num_logits_indices > 0
            hidden_states[logits_indices_padded[:num_logits_indices]] = (
                cross_hidden_states[:num_logits_indices]
            )
        else:
            hidden_states = cross_hidden_states

        return hidden_states