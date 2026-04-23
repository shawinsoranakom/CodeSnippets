def forward(
        self,
        input_ids: torch.Tensor | None,
        positions: torch.Tensor,
        intermediate_tensors: IntermediateTensors | None = None,
        inputs_embeds: torch.Tensor | None = None,
        deepstack_input_embeds: IntermediateTensors | None = None,
    ) -> torch.Tensor | IntermediateTensors:
        if get_pp_group().is_first_rank:
            if inputs_embeds is not None:
                hidden_states = inputs_embeds
            else:
                hidden_states = self.embed_input_ids(input_ids)
                hidden_states = hidden_states * self.config.embedding_multiplier
        else:
            assert intermediate_tensors is not None
            hidden_states = intermediate_tensors["hidden_states"]
            # Recover deepstack features forwarded from the previous PP rank.
            if deepstack_input_embeds is None:
                ds_keys = [
                    k for k in intermediate_tensors.tensors if k.startswith("ds_")
                ]
                if ds_keys:
                    deepstack_input_embeds = IntermediateTensors(
                        {k: intermediate_tensors[k] for k in ds_keys}
                    )

        for layer_idx, layer in islice(
            enumerate(self.layers), self.start_layer, self.end_layer
        ):
            if deepstack_input_embeds is not None:
                key = f"ds_{layer_idx}"
                if key in deepstack_input_embeds.tensors:
                    feat = deepstack_input_embeds[key]
                    # Resize to match hidden_states in case of CUDA graph padding
                    num_tokens = hidden_states.size(0)
                    buf_len = feat.shape[0]
                    if buf_len != num_tokens:
                        feat = torch.nn.functional.pad(
                            feat[:num_tokens],
                            (0, 0, 0, max(0, num_tokens - buf_len)),
                        )
                    hidden_states = hidden_states + feat
            hidden_states = layer(positions, hidden_states)

        if not get_pp_group().is_last_rank:
            # Forward hidden_states and any deepstack features for later ranks.
            it = {"hidden_states": hidden_states}
            if deepstack_input_embeds is not None:
                remaining = {
                    k: v
                    for k, v in deepstack_input_embeds.tensors.items()
                    if int(k.split("_")[1]) >= self.end_layer
                }
                it.update(remaining)
            return IntermediateTensors(it)

        hidden_states = self.norm(hidden_states)
        return hidden_states