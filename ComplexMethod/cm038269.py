def forward(
        self,
        input_ids: torch.Tensor | None,
        positions: torch.Tensor,
        intermediate_tensors: IntermediateTensors | None = None,
        inputs_embeds: torch.Tensor | None = None,
        **kwargs,
    ) -> torch.Tensor | IntermediateTensors:
        if not self.pp_group.is_first_rank:
            assert intermediate_tensors is not None
            input_ids = None
            inputs_embeds = intermediate_tensors["hidden_states"]

        # If the model scales embeddings inside the input embedding layer we must
        # ensure they are scaled here since VocabParallelEmbedding will not do it
        if (
            self.embed_scale is not None
            and input_ids is not None
            and inputs_embeds is None
        ):
            inputs_embeds = self.embed_input_ids(input_ids)
            input_ids = None

        # Add batch dimension before entering Transformers model
        if input_ids is not None and input_ids.ndim == 1:
            # [seq_len] -> [1, seq_len]
            input_ids = input_ids[None, ...]
        if inputs_embeds is not None and inputs_embeds.ndim == 2:
            # [seq_len, hidden_size] -> [1, seq_len, hidden_size]
            inputs_embeds = inputs_embeds[None, ...]
        if positions.ndim == 1:
            # [seq_len] -> [1, seq_len]
            positions = positions[None, ...]

        outputs = self.model(
            input_ids=input_ids,
            inputs_embeds=inputs_embeds,
            use_cache=False,
            position_ids=positions,
            attention_instances=self.attention_instances,
            return_dict=False,
            **self._output_aux_hidden_states_kwargs,
            **kwargs,
        )

        # Remove batch dimension after exiting Transformers model
        hidden_states = outputs[0][0, ...]
        if self._output_aux_hidden_states_kwargs:
            aux_hidden_states = [x[0][0, ...] for x in outputs[1:]]

        if not self.pp_group.is_last_rank:
            return IntermediateTensors({"hidden_states": hidden_states})

        if self._output_aux_hidden_states_kwargs and len(aux_hidden_states) > 0:
            return hidden_states, aux_hidden_states
        return hidden_states