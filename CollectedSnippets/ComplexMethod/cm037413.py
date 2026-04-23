def _dummy_run(
        self,
        num_tokens: int,
        *args,
        skip_attn: bool = False,
        uniform_decode: bool = False,
        skip_eplb: bool = False,
        is_profile: bool = False,
        **kwargs,
    ) -> tuple[torch.Tensor | None, torch.Tensor | None]:
        if skip_attn and not is_profile:
            raise ValueError(
                "skip_attn must only be True for initial memory profiling."
            )

        # Create a dummy scheduler output.
        num_reqs = min(num_tokens, self.max_num_reqs)
        if uniform_decode:
            # HACK(lucas): for now since the worker is shared between MRV1 and MRV2,
            # and for spec-decode with MTP we want to make sure the dummy runs use
            # 1+num_speculative_tokens we use max here, this will likely be eventually
            # changed in the worker: https://github.com/vllm-project/vllm/pull/35243
            num_tokens = max(num_tokens, self.decode_query_len)
            num_reqs = num_tokens // self.decode_query_len
            assert num_tokens % self.decode_query_len == 0
        num_tokens_per_request = [num_tokens // num_reqs] * num_reqs
        num_tokens_per_request[-1] += num_tokens % num_reqs

        assert sum(num_tokens_per_request) == num_tokens
        num_scheduled_tokens = {
            f"_dummy_req_{i}": n for i, n in enumerate(num_tokens_per_request)
        }
        dummy_scheduler_output = SchedulerOutput.make_empty()
        dummy_scheduler_output.total_num_scheduled_tokens = num_tokens
        dummy_scheduler_output.num_scheduled_tokens = num_scheduled_tokens

        # Disable any use of KVConnector for dummy runs.
        self.kv_connector.set_disabled(True)

        # Get the intermediate tensors for the dummy run.
        intermediate_tensors = None
        if not self.is_first_pp_rank:
            assert self.intermediate_tensors is not None
            intermediate_tensors = self.intermediate_tensors[:num_tokens]

        # Execute the model.
        self.execute_model(
            dummy_scheduler_output,
            intermediate_tensors=intermediate_tensors,
            dummy_run=True,
            skip_attn_for_dummy_run=skip_attn,
            is_profile=is_profile,
        )
        self.kv_connector.set_disabled(False)

        # Non-last PP ranks don't produce output for sampling.
        if not self.is_last_pp_rank:
            return None, None

        assert self.execute_model_state is not None
        input_batch = self.execute_model_state.input_batch
        attn_metadata = self.execute_model_state.attn_metadata
        slot_mappings_by_layer = self.execute_model_state.slot_mappings_by_layer
        hidden_states = self.execute_model_state.hidden_states
        aux_hidden_states = self.execute_model_state.aux_hidden_states
        self.execute_model_state = None

        # dummy run the eagle speculator's propose to ensure DP/EP sync.
        if self.speculator is not None:
            assert self.sampler is not None
            mm_inputs: tuple[list[torch.Tensor], torch.Tensor] | None = None
            if self.speculator.supports_mm_inputs:
                mm_inputs = (
                    [],
                    torch.zeros(
                        input_batch.num_tokens,
                        dtype=torch.bool,
                        device=self.device,
                    ),
                )
            self.speculator.propose(
                input_batch=input_batch,
                attn_metadata=attn_metadata,
                slot_mappings=slot_mappings_by_layer,
                last_hidden_states=hidden_states,
                aux_hidden_states=aux_hidden_states,
                num_sampled=torch.ones(
                    input_batch.num_reqs, dtype=torch.int32, device=self.device
                ),
                num_rejected=torch.zeros(
                    input_batch.num_reqs, dtype=torch.int32, device=self.device
                ),
                last_sampled=self.req_states.last_sampled_tokens,
                next_prefill_tokens=self.req_states.next_prefill_tokens,
                temperature=self.sampler.sampling_states.temperature.gpu,
                seeds=self.sampler.sampling_states.seeds.gpu,
                dummy_run=True,
                skip_attn_for_dummy_run=skip_attn,
                mm_inputs=mm_inputs,
                is_profile=is_profile,
            )

        assert hidden_states is not None  # Last PP rank always has hidden_states
        sample_hidden_states = hidden_states[input_batch.logits_indices]
        return hidden_states, sample_hidden_states