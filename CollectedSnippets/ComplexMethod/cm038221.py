def forward(
        self,
        input_ids: torch.Tensor | None,
        positions: torch.Tensor,
        intermediate_tensors: IntermediateTensors | None,
        inputs_embeds: torch.Tensor | None = None,
        per_layer_inputs: torch.Tensor | None = None,
        **kwargs,
    ) -> torch.Tensor | IntermediateTensors | tuple[torch.Tensor, list[torch.Tensor]]:
        if self.fast_prefill_enabled:
            hidden_states = self.fast_prefill_forward(
                input_ids,
                positions,
                inputs_embeds,
                per_layer_inputs,
                **kwargs,
            )
            hidden_states = self.norm(hidden_states)
            return hidden_states

        # Normal (non-fast-prefill) path with PP support
        if get_pp_group().is_first_rank:
            if inputs_embeds is not None:
                hidden_states = inputs_embeds
                # When called from the multimodal wrapper, raw PLE
                # embeddings are pre-computed and passed explicitly.
                # Project them through per_layer_model_projection.
                per_layer_inputs = self.project_per_layer_inputs(
                    hidden_states, per_layer_inputs
                )
            else:
                hidden_states = self.embed_input_ids(input_ids)
                # Compute per-layer inputs for PLE
                per_layer_embeds = self.get_per_layer_inputs(input_ids)
                per_layer_inputs = self.project_per_layer_inputs(
                    hidden_states, per_layer_embeds
                )
            residual = None
        else:
            assert intermediate_tensors is not None
            hidden_states = intermediate_tensors["hidden_states"]
            residual = intermediate_tensors["residual"]
            per_layer_inputs = intermediate_tensors.get("per_layer_inputs")

        aux_hidden_states = self._maybe_add_hidden_state([], 0, hidden_states, residual)
        for layer_idx, layer in enumerate(
            islice(self.layers, self.start_layer, self.end_layer)
        ):
            # Extract the per-layer embedding for this specific layer
            if per_layer_inputs is not None:
                actual_layer_idx = self.start_layer + layer_idx
                layer_per_input = per_layer_inputs[
                    :, actual_layer_idx, :
                ]  # (num_tokens, per_layer_dim)
            else:
                layer_per_input = None
            hidden_states, residual = layer(
                positions,
                hidden_states,
                residual,
                per_layer_input=layer_per_input,
                **kwargs,
            )
            self._maybe_add_hidden_state(
                aux_hidden_states, layer_idx + 1, hidden_states, residual
            )
        if not get_pp_group().is_last_rank:
            return IntermediateTensors(
                {
                    "hidden_states": hidden_states,
                    "residual": residual,
                    "per_layer_inputs": per_layer_inputs,
                }
            )
        # Gemma4 incorporates residual into hidden_states directly
        # Apply norm without residual fusion when possible.
        if residual is None:
            hidden_states = self.norm(hidden_states)
        else:
            hidden_states, _ = self.norm(hidden_states, residual)

        if len(aux_hidden_states) > 0:
            return hidden_states, aux_hidden_states
        return hidden_states