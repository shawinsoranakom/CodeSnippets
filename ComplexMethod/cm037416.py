def sample_tokens(
        self, grammar_output: GrammarOutput | None
    ) -> AsyncOutput | ModelRunnerOutput | None:
        if self.execute_model_state is None:
            # The prior execute_model call must have failed.
            return None

        input_batch = self.execute_model_state.input_batch
        attn_metadata = self.execute_model_state.attn_metadata
        slot_mappings_by_layer = self.execute_model_state.slot_mappings_by_layer
        hidden_states = self.execute_model_state.hidden_states
        aux_hidden_states = self.execute_model_state.aux_hidden_states
        kv_connector_output = self.execute_model_state.kv_connector_output
        self.execute_model_state = None

        if not self.is_last_pp_rank:
            # Non-last PP rank: hidden_states is None because this rank produced
            # IntermediateTensors instead of final hidden states. Receive the
            # sampled tokens broadcast from the last rank and update local state.
            sampled, num_sampled, num_rejected = pp_receive(
                input_batch.num_reqs, max_sample_len=self.num_speculative_steps + 1
            )
            self.postprocess(input_batch, sampled, num_sampled, num_rejected)
            return None

        # Last rank: sample tokens
        sampler_output, num_sampled, num_rejected = self.sample(
            hidden_states, input_batch, grammar_output
        )

        if self.use_pp:
            # Broadcast to non-last PP ranks (handles spec decode multi-token).
            pp_broadcast(sampler_output.sampled_token_ids, num_sampled, num_rejected)

        assert self.prompt_logprobs_worker is not None
        prompt_logprobs_dict = self.prompt_logprobs_worker.compute_prompt_logprobs(
            self.model.compute_logits,
            hidden_states,
            input_batch,
            self.req_states.all_token_ids.gpu,
            self.req_states.num_computed_tokens.gpu,
            self.req_states.prompt_len.np,
            self.req_states.prefill_len.np,
            self.req_states.num_computed_prefill_tokens,
        )

        # Prepare the model runner output.
        model_runner_output = ModelRunnerOutput(
            req_ids=input_batch.req_ids,
            # NOTE(woosuk): req_id_to_index is unused in this model runner.
            # Only for compatibility with the existing model runner and scheduler.
            req_id_to_index={req_id: i for i, req_id in enumerate(input_batch.req_ids)},
            sampled_token_ids=None,  # type: ignore
            prompt_logprobs_dict=prompt_logprobs_dict,  # type: ignore[arg-type]
            kv_connector_output=kv_connector_output,
        )
        async_output = AsyncOutput(
            model_runner_output=model_runner_output,
            sampler_output=sampler_output,
            num_sampled_tokens=num_sampled,
            main_stream=self.main_stream,
            copy_stream=self.output_copy_stream,
        )

        mm_inputs: tuple[list[torch.Tensor], torch.Tensor] | None = None
        if self.speculator is not None and self.speculator.supports_mm_inputs:
            # Get cached multimodal embeddings for draft forward.
            # NOTE: This is done here because postprocess updates
            # num_computed_prefill_tokens.
            prefill_lens = self.req_states.prefill_len.np[input_batch.idx_mapping_np]
            computed_prefill_lens = self.req_states.num_computed_prefill_tokens[
                input_batch.idx_mapping_np
            ]
            mm_inputs = self.model_state.encoder_runner.gather_mm_embeddings(
                input_batch.req_ids,
                input_batch.num_tokens,
                input_batch.num_scheduled_tokens,
                input_batch.query_start_loc_np,
                prefill_lens,
                computed_prefill_lens + 1,  # +1 to consider the skew in eagle
            )

        # Postprocess results and update request states.
        # NOTE: This is intentionally done after creating the AsyncOutput,
        # ensuring that `copy_event` is recorded before calling postprocess.
        # This sequencing may slightly reduce latency as async D2H copy does not
        # need to wait for the postprocess to finish.
        self.postprocess(
            input_batch, sampler_output.sampled_token_ids, num_sampled, num_rejected
        )

        if self.speculator is not None:
            assert self.sampler is not None
            draft_tokens = self.speculator.propose(
                input_batch,
                attn_metadata,
                slot_mappings_by_layer,
                hidden_states,
                aux_hidden_states,
                num_sampled,
                num_rejected,
                self.req_states.last_sampled_tokens,
                self.req_states.next_prefill_tokens,
                self.sampler.sampling_states.temperature.gpu,
                self.sampler.sampling_states.seeds.gpu,
                mm_inputs=mm_inputs,
            )
            self.req_states.draft_tokens[input_batch.idx_mapping] = draft_tokens
            self.draft_tokens_handler.set_draft_tokens(input_batch, draft_tokens)

        if self.use_async_scheduling:
            return async_output
        return async_output.get_output()