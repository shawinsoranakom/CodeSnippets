def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.LongTensor | None = None,
        cache_params: xLSTMCache | None = None,
        use_cache: bool | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple | xLSTMOutput:
        r"""
        cache_params (`xLSTMCache`, *optional*):
            The xLSTMCache that carries the RNN states.
        """
        # Resolved here (not just by @capture_outputs) because the chunked inference path below
        # is incompatible with hidden state collection and we need the value to pick the right branch.
        output_hidden_states = kwargs.get("output_hidden_states")
        if output_hidden_states is None:
            output_hidden_states = self.config.output_hidden_states

        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        if inputs_embeds is None:
            inputs_embeds = self.embeddings(input_ids)

        if use_cache and cache_params is None:
            cache_params = xLSTMCache(
                self.config, inputs_embeds.size(0), device=inputs_embeds.device, dtype=inputs_embeds.dtype
            )

        hidden_states = inputs_embeds

        if (
            not self.training
            and self.config.max_inference_chunksize < hidden_states.shape[1]
            and not output_hidden_states
        ):
            offset = 0
            with torch.no_grad():
                if cache_params is None:
                    cache_params = xLSTMCache(config=self.config, max_batch_size=hidden_states.shape[0])
                final_state = torch.zeros_like(hidden_states)
                while offset < hidden_states.shape[1]:
                    hidden_states_chunk = hidden_states[
                        :, offset : min(offset + self.config.max_inference_chunksize, hidden_states.shape[1])
                    ]
                    for layer_idx, xlstm_block in enumerate(self.blocks):
                        hidden_states_chunk, rnn_state = xlstm_block(
                            hidden_states_chunk,
                            state=cache_params.rnn_state[layer_idx],
                        )
                        for state_idx in range(len(cache_params.rnn_state[layer_idx])):
                            local_rnn_state = rnn_state[state_idx]
                            cache_params.rnn_state[layer_idx][state_idx].copy_(local_rnn_state)
                        cache_params.rnn_state_initial = False
                    final_state[
                        :, offset : min(offset + self.config.max_inference_chunksize, hidden_states.shape[1])
                    ] = hidden_states_chunk
                    offset += self.config.max_inference_chunksize
                hidden_states = final_state
        else:
            for layer_idx, xlstm_block in enumerate(self.blocks):
                hidden_states, rnn_state = xlstm_block(
                    hidden_states,
                    cache_params.rnn_state[layer_idx] if cache_params is not None else None,
                )

                if cache_params:
                    for state_idx in range(len(cache_params.rnn_state[layer_idx])):
                        local_rnn_state = rnn_state[state_idx]
                        cache_params.rnn_state[layer_idx][state_idx].copy_(local_rnn_state)
                    cache_params.rnn_state_initial = False

        if use_cache:
            cache_params.seqlen_offset += inputs_embeds.shape[1]

        hidden_states = self.out_norm(hidden_states)

        return xLSTMOutput(
            last_hidden_state=hidden_states,
            cache_params=cache_params,
        )