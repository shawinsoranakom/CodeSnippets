def forward(
        self,
        input_ids: torch.Tensor | None,
        positions: torch.Tensor,
        intermediate_tensors: IntermediateTensors | None,
        inputs_embeds: torch.Tensor | None = None,
    ) -> torch.Tensor | IntermediateTensors:
        if get_pp_group().is_first_rank:
            if inputs_embeds is not None:
                hidden_states = inputs_embeds
            else:
                hidden_states = self.embed_input_ids(input_ids)
            residual = None
        else:
            assert intermediate_tensors is not None
            hidden_states = intermediate_tensors["hidden_states"]
            residual = intermediate_tensors["residual"]

        cla_factor = _get_cla_factor(self.config)
        prev_kv_states = None
        aux_hidden_states = self._maybe_add_hidden_state([], 0, hidden_states, residual)
        for i, layer in enumerate(
            islice(self.layers, self.start_layer, self.end_layer)
        ):
            hidden_states, residual, kv_states = layer(
                positions,
                hidden_states,
                residual,
                prev_kv_states,
            )

            if getattr(self.config, "use_cla", False) and i % cla_factor == 0:
                prev_kv_states = kv_states
            else:
                prev_kv_states = None

            self._maybe_add_hidden_state(
                aux_hidden_states, i + 1, hidden_states, residual
            )

        if not get_pp_group().is_last_rank:
            return IntermediateTensors(
                {"hidden_states": hidden_states, "residual": residual}
            )

        hidden_states, _ = self.norm(hidden_states, residual)

        if len(aux_hidden_states) > 0:
            return hidden_states, aux_hidden_states
        return hidden_states