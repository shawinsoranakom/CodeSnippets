def propose(
        self,
        input_batch: InputBatch,
        attn_metadata: dict[str, Any],
        slot_mappings: dict[str, torch.Tensor],
        # [num_tokens, hidden_size]
        last_hidden_states: torch.Tensor,
        # num_layers x [num_tokens, hidden_size]
        aux_hidden_states: list[torch.Tensor] | None,
        # [num_reqs]
        num_sampled: torch.Tensor,
        # [num_reqs]
        num_rejected: torch.Tensor,
        # [max_num_reqs]
        last_sampled: torch.Tensor,
        # [max_num_reqs]
        next_prefill_tokens: torch.Tensor,
        # [max_num_reqs]
        temperature: torch.Tensor,
        # [max_num_reqs]
        seeds: torch.Tensor,
        num_tokens_across_dp: torch.Tensor | None = None,
        dummy_run: bool = False,
        skip_attn_for_dummy_run: bool = False,
        mm_inputs: tuple[list[torch.Tensor], torch.Tensor] | None = None,
        is_profile: bool = False,
    ) -> torch.Tensor:
        num_tokens = input_batch.num_tokens_after_padding
        num_reqs = input_batch.num_reqs
        max_query_len = input_batch.num_scheduled_tokens.max()

        # NOTE(woosuk): To avoid CPU-GPU synchronization without CPU knowing the
        # number of rejected tokens, we maintain the size of eagle's input_ids and
        # hidden_states the same as the target model's. This means, we pad each
        # request's query length to include any rejected positions. By doing so,
        # we can also reuse the attention metadata (e.g., query_start_loc,
        # seq_lens) of the target model.
        if aux_hidden_states:
            assert self.method == "eagle3"
            hidden_states = self.model.combine_hidden_states(
                torch.cat(aux_hidden_states, dim=-1)
            )
        else:
            hidden_states = last_hidden_states
        self.hidden_states[:num_tokens].copy_(hidden_states)

        # Copy temperature, seeds, and idx mapping to the pre-allocated buffers.
        # NOTE(woosuk): For draft sampling, we only consider the temperature
        # and ignore the other sampling parameters such as top_k and top_p,
        # for simplicity and performance.
        # While this may slightly degrade the acceptance rate, it does not
        # affect the output distribution after rejection sampling.
        self.temperature.copy_(temperature)
        self.seeds.copy_(seeds)
        self.idx_mapping[:num_reqs].copy_(input_batch.idx_mapping)

        # Get the input ids and last token indices for the speculator.
        prepare_eagle_inputs(
            self.input_buffers,
            input_batch,
            self.last_token_indices,
            num_sampled,
            num_rejected,
            last_sampled,
            next_prefill_tokens,
            self.max_num_reqs,
        )

        # When all requests are decoding (no true prefills), each has
        # num_speculative_steps + 1 tokens, enabling FULL graph replay.
        # Mixed or prefill-only batches fall back to PIECEWISE.
        prefill_batch_desc, num_tokens_across_dp = dispatch_cg_and_sync_dp(
            self.prefill_cudagraph_manager,
            num_reqs,
            num_tokens,
            get_uniform_token_count(num_reqs, num_tokens, max_query_len),
            dp_size=self.dp_size,
            dp_rank=self.dp_rank,
            need_eager=is_profile,
        )

        if prefill_batch_desc.cg_mode == CUDAGraphMode.FULL:
            # It is necessary to rebuild the attention metadata when
            # replaying the FULL graph so that any attention metadata
            # builder state is updated.
            self._build_draft_attn_metadata(
                num_reqs=num_reqs,
                num_reqs_padded=prefill_batch_desc.num_reqs or num_reqs,
                num_tokens_padded=prefill_batch_desc.num_tokens,
                max_query_len=self.num_speculative_steps + 1,
            )
            # Replay the full graph for draft prefill.
            assert self.prefill_cudagraph_manager is not None
            self.prefill_cudagraph_manager.run_fullgraph(prefill_batch_desc)
        else:
            # The target model's attention metadata and slot mappings
            # can directly be used for draft prefill, because of the
            # identical batch shape and KV cache layout.
            self.prefill(
                num_reqs,
                prefill_batch_desc.num_tokens,
                attn_metadata,
                slot_mappings,
                num_tokens_across_dp=num_tokens_across_dp,
                cudagraph_runtime_mode=prefill_batch_desc.cg_mode,
                mm_inputs=mm_inputs,
            )

        if self.num_speculative_steps == 1:
            # Early exit.
            return self.draft_tokens[:num_reqs, :1]

        # Prepare the inputs for the decode steps.
        prepare_eagle_decode(
            self.draft_tokens[:num_reqs, 0],
            input_batch.seq_lens,
            num_rejected,
            self.input_buffers,
            self.max_model_len,
            self.max_num_reqs,
        )

        # Each request produces exactly 1 token per draft generation step,
        # enabling FULL graph replay.
        decode_batch_desc, num_tokens_across_dp = dispatch_cg_and_sync_dp(
            self.decode_cudagraph_manager,
            num_reqs,
            num_reqs,
            uniform_token_count=1,
            dp_size=self.dp_size,
            dp_rank=self.dp_rank,
            need_eager=is_profile,
        )

        attn_metadata_updated = None
        slot_mappings_updated = None
        if not (dummy_run and skip_attn_for_dummy_run):
            # Build attention metadata and slot mappings for the draft
            # decode steps. It is necessary to rebuild the attention
            # metadata even when replaying the FULL graph so that any
            # attention metadata builder state is updated.
            slot_mappings = self.block_tables.compute_slot_mappings(
                self.idx_mapping[:num_reqs],
                self.input_buffers.query_start_loc[: num_reqs + 1],
                self.input_buffers.positions[:num_reqs],
                decode_batch_desc.num_tokens,
            )
            slot_mappings_updated = build_slot_mappings_by_layer(
                slot_mappings, self.kv_cache_config
            )
            attn_metadata_updated = self._build_draft_attn_metadata(
                num_reqs=num_reqs,
                num_reqs_padded=decode_batch_desc.num_reqs or num_reqs,
                num_tokens_padded=decode_batch_desc.num_tokens,
                max_query_len=1,
            )

        if decode_batch_desc.cg_mode == CUDAGraphMode.FULL:
            # Replay the full graph for draft generation.
            assert self.decode_cudagraph_manager is not None
            self.decode_cudagraph_manager.run_fullgraph(decode_batch_desc)
        else:
            self.generate_draft(
                num_reqs,
                decode_batch_desc.num_tokens,
                attn_metadata_updated,
                slot_mappings_updated,
                num_tokens_across_dp=num_tokens_across_dp,
                cudagraph_runtime_mode=decode_batch_desc.cg_mode,
            )
        return self.draft_tokens[:num_reqs]