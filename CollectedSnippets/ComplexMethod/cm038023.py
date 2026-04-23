def forward(
        self,
        input_ids: torch.Tensor,
        positions: torch.Tensor,
        intermediate_tensors: IntermediateTensors | None = None,
        inputs_embeds: torch.Tensor | None = None,
        **kwargs: object,
    ) -> torch.Tensor | IntermediateTensors:
        if intermediate_tensors is not None:
            inputs_embeds = None

        # Build IntermediateTensors from pre-allocated persistent buffers.
        # Always pass deepstack when inputs_embeds is non-None (prefill path),
        # including during CUDA graph capture (buffers are zero → no-op injection).
        # This ensures the graph captures the injection code path.
        if (
            inputs_embeds is not None
            and get_pp_group().is_first_rank
            and self._ds_layer_indices
        ):
            ds: IntermediateTensors | None = IntermediateTensors(
                {
                    f"ds_{llm_layer}": self._ds_buffers[lvl]
                    for lvl, llm_layer in enumerate(self._ds_layer_indices)
                }
            )
        else:
            ds = None

        hidden_states = self.language_model.model(
            input_ids=input_ids,
            positions=positions,
            intermediate_tensors=intermediate_tensors,
            inputs_embeds=inputs_embeds,
            deepstack_input_embeds=ds,
        )

        # Clear buffers after use so stale features don't leak into the next request.
        if (
            inputs_embeds is not None
            and get_pp_group().is_first_rank
            and self._ds_num_tokens > 0
        ):
            n = self._ds_num_tokens
            for buf in self._ds_buffers:
                buf[:n].zero_()
            self._ds_num_tokens = 0

        return hidden_states