def _prepare_inputs(
        self,
        scheduler_output: "SchedulerOutput",
        num_scheduled_tokens: np.ndarray,
    ) -> tuple[
        torch.Tensor,
        SpecDecodeMetadata | None,
    ]:
        """
        :return: tuple[
            logits_indices, spec_decode_metadata,
        ]
        """
        total_num_scheduled_tokens = scheduler_output.total_num_scheduled_tokens
        assert total_num_scheduled_tokens > 0
        num_reqs = self.input_batch.num_reqs
        assert num_reqs > 0

        # OPTIMIZATION: Start copying the block table first.
        # This way, we can overlap the copy with the following CPU operations.
        self.input_batch.block_table.commit_block_table(num_reqs)

        # Get request indices.
        # E.g., [2, 5, 3] -> [0, 0, 1, 1, 1, 1, 1, 2, 2, 2]
        req_indices = np.repeat(self.arange_np[:num_reqs], num_scheduled_tokens)

        # cu_num_tokens: [2, 5, 3] -> [2, 7, 10]
        # self.query_pos.np[:10]: [0, 1, 0, 1, 2, 3, 4, 0, 1, 2]
        cu_num_tokens = self._get_cumsum_and_arange(
            num_scheduled_tokens, self.query_pos.np
        )

        # Get positions.
        positions_np = (
            self.input_batch.num_computed_tokens_cpu[req_indices]
            + self.query_pos.np[: cu_num_tokens[-1]]
        )

        # Calculate M-RoPE positions.
        # Only relevant for models using M-RoPE (e.g, Qwen2-VL)
        if self.uses_mrope:
            self._calc_mrope_positions(scheduler_output)

        # Calculate XD-RoPE positions.
        # Only relevant for models using XD-RoPE (e.g, HunYuan-VL)
        if self.uses_xdrope_dim > 0:
            self._calc_xdrope_positions(scheduler_output)

        # Get token indices.
        # E.g., [0, 1, 0, 1, 2, 3, 4, 0, 1, 2]
        # -> [0, 1, M, M + 1, M + 2, M + 3, M + 4, 2 * M, 2 * M + 1, 2 * M + 2]
        # where M is the max_model_len.
        token_indices = (
            positions_np + req_indices * self.input_batch.token_ids_cpu.shape[1]
        )
        token_indices_tensor = torch.from_numpy(token_indices)

        # NOTE(woosuk): We use torch.index_select instead of np.take here
        # because torch.index_select is much faster than np.take for large
        # tensors.
        torch.index_select(
            self.input_batch.token_ids_cpu_tensor.flatten(),
            0,
            token_indices_tensor,
            out=self.input_ids.cpu[:total_num_scheduled_tokens],
        )
        if self.enable_prompt_embeds:
            is_token_ids = self.input_batch.is_token_ids_tensor.flatten()
            torch.index_select(
                is_token_ids,
                0,
                token_indices_tensor,
                out=self.is_token_ids.cpu[:total_num_scheduled_tokens],
            )

        # Because we did not pre-allocate a massive prompt_embeds CPU tensor on
        # the InputBatch, we need to fill in the prompt embeds into the expected
        # spots in the GpuModelRunner's pre-allocated prompt_embeds tensor.
        if self.input_batch.req_prompt_embeds:
            output_idx = 0
            for req_idx in range(num_reqs):
                num_sched = num_scheduled_tokens[req_idx]

                # Skip if this request doesn't have embeddings
                if req_idx not in self.input_batch.req_prompt_embeds:
                    output_idx += num_sched
                    continue

                # Skip if no tokens scheduled
                if num_sched <= 0:
                    output_idx += num_sched
                    continue

                req_embeds = self.input_batch.req_prompt_embeds[req_idx]
                start_pos = self.input_batch.num_computed_tokens_cpu[req_idx]

                # Skip if trying to read beyond available embeddings
                if start_pos >= req_embeds.shape[0]:
                    output_idx += num_sched
                    continue

                # Copy available embeddings
                end_pos = start_pos + num_sched
                actual_end = min(end_pos, req_embeds.shape[0])
                actual_num_sched = actual_end - start_pos

                if actual_num_sched > 0:
                    self.inputs_embeds.cpu[
                        output_idx : output_idx + actual_num_sched
                    ].copy_(req_embeds[start_pos:actual_end])

                output_idx += num_sched

        # Prepare the attention metadata.
        self.query_start_loc.np[0] = 0
        self.query_start_loc.np[1 : num_reqs + 1] = cu_num_tokens
        # Note: pad query_start_loc to be non-decreasing, as kernels
        # like FlashAttention requires that
        self.query_start_loc.np[num_reqs + 1 :].fill(cu_num_tokens[-1])
        self.query_start_loc.copy_to_gpu()
        query_start_loc = self.query_start_loc.gpu[: num_reqs + 1]

        # Compute optimistic seq_lens (assumes all draft tokens from previous
        # iteration accepted). Store in optimistic_seq_lens_cpu for use by
        # _build_attention_metadata (max_seq_len) and discard_request_mask.
        # seq_lens (GPU) will be computed later using the same optimistic values.
        torch.add(
            self.input_batch.num_computed_tokens_cpu_tensor[:num_reqs],
            torch.from_numpy(num_scheduled_tokens),
            out=self.optimistic_seq_lens_cpu[:num_reqs],
        )
        self.optimistic_seq_lens_cpu[num_reqs:].fill_(0)

        # Build prev_positions mapping: current pos -> prev pos (-1 if new).
        # Used for gathering from previous iteration's GPU tensors.
        prev_req_id_to_index = self.input_batch.prev_req_id_to_index
        self._compute_prev_positions(num_reqs)

        num_tokens = [self.requests[r].num_tokens for r in self.input_batch.req_ids]
        num_tokens_np = np.array(num_tokens, dtype=np.int32)

        # Record which requests should not be sampled,
        # so that we could clear the sampled tokens before returning
        self.discard_request_mask.np[:num_reqs] = (
            self.optimistic_seq_lens_cpu[:num_reqs].numpy() < num_tokens_np
        )
        self.discard_request_mask.copy_to_gpu(num_reqs)

        # Sync num_accepted_tokens from CPU (set by
        # _update_states_after_model_execute for hybrid models).
        if self.num_accepted_tokens_event is not None:
            self.num_accepted_tokens_event.synchronize()
            # Async mode: condense() reordered indices, use prev_positions mapping
            if self.use_async_scheduling and prev_req_id_to_index:
                prev_idx = self.prev_positions.np[:num_reqs]
                new_mask = prev_idx < 0
                self.num_accepted_tokens.np[:num_reqs] = (
                    self.input_batch.num_accepted_tokens_cpu[
                        np.where(new_mask, 0, prev_idx)
                    ]
                )
                self.num_accepted_tokens.np[:num_reqs][new_mask] = 1
                self.input_batch.num_accepted_tokens_cpu[:num_reqs] = (
                    self.num_accepted_tokens.np[:num_reqs]
                )
            else:
                # Non-async mode: use values directly
                self.num_accepted_tokens.np[:num_reqs] = (
                    self.input_batch.num_accepted_tokens_cpu[:num_reqs]
                )
            self.num_accepted_tokens.np[num_reqs:].fill(1)
            self.num_accepted_tokens.copy_to_gpu()
        else:
            self.num_accepted_tokens.np.fill(1)
            self.num_accepted_tokens.gpu.fill_(1)

        # Update num_computed_tokens on GPU. In async spec decode,
        # CPU values are optimistic (all drafts accepted). The kernel
        # corrects on GPU using the previous step's
        # valid_sampled_token_count_gpu. Otherwise, just copy from CPU.
        if (
            self.use_async_spec_decode
            and self.valid_sampled_token_count_gpu is not None
            and prev_req_id_to_index
        ):
            self.prev_positions.copy_to_gpu(num_reqs)
            self.prev_num_draft_tokens.copy_to_gpu()
            cpu_values = self.input_batch.num_computed_tokens_cpu_tensor[:num_reqs].to(
                device=self.device, non_blocking=True
            )
            update_num_computed_tokens_for_batch_change(
                self.num_computed_tokens,
                self.num_accepted_tokens.gpu[:num_reqs],
                self.prev_positions.gpu[:num_reqs],
                self.valid_sampled_token_count_gpu,
                self.prev_num_draft_tokens.gpu,
                cpu_values,
            )
        else:
            self.num_computed_tokens[:num_reqs].copy_(
                self.input_batch.num_computed_tokens_cpu_tensor[:num_reqs],
                non_blocking=True,
            )

        self.req_indices.np[:total_num_scheduled_tokens] = req_indices
        self.req_indices.copy_to_gpu(total_num_scheduled_tokens)
        req_indices_gpu = self.req_indices.gpu[:total_num_scheduled_tokens]

        self.query_pos.copy_to_gpu(total_num_scheduled_tokens)
        self.num_scheduled_tokens.np[:num_reqs] = num_scheduled_tokens
        self.num_scheduled_tokens.copy_to_gpu(num_reqs)
        num_scheduled_tokens_gpu = self.num_scheduled_tokens.gpu[:num_reqs]
        self.positions[:total_num_scheduled_tokens] = (
            self.num_computed_tokens[req_indices_gpu].to(torch.int64)
            + self.query_pos.gpu[:total_num_scheduled_tokens]
        )
        self.seq_lens[:num_reqs] = (
            self.num_computed_tokens[:num_reqs] + num_scheduled_tokens_gpu
        )
        self.seq_lens[num_reqs:].fill_(0)

        self.input_batch.block_table.compute_slot_mapping(
            num_reqs,
            self.query_start_loc.gpu[: num_reqs + 1],
            self.positions[:total_num_scheduled_tokens],
        )

        # Copy the tensors to the GPU.
        self._prepare_input_ids(
            scheduler_output,
            num_reqs,
            total_num_scheduled_tokens,
            cu_num_tokens,
        )

        if self.uses_mrope:
            # Only relevant for models using M-RoPE (e.g, Qwen2-VL)
            self.mrope_positions.gpu[:, :total_num_scheduled_tokens].copy_(
                self.mrope_positions.cpu[:, :total_num_scheduled_tokens],
                non_blocking=True,
            )
        elif self.uses_xdrope_dim > 0:
            # Only relevant for models using XD-RoPE (e.g, HunYuan-VL)
            self.xdrope_positions.gpu[:, :total_num_scheduled_tokens].copy_(
                self.xdrope_positions.cpu[:, :total_num_scheduled_tokens],
                non_blocking=True,
            )
        if self.use_async_spec_decode and (self.uses_mrope or self.uses_xdrope_dim > 0):
            drift = self.num_computed_tokens[req_indices_gpu].to(
                torch.int64
            ) - self.input_batch.num_computed_tokens_cpu_tensor[req_indices].to(
                device=self.device, dtype=torch.int64, non_blocking=True
            )
            target = self.mrope_positions if self.uses_mrope else self.xdrope_positions
            target.gpu[:, :total_num_scheduled_tokens] += drift

        use_spec_decode = len(scheduler_output.scheduled_spec_decode_tokens) > 0
        if not use_spec_decode:
            # NOTE(woosuk): Due to chunked prefills, the batch may contain
            # partial requests. While we should not sample any token
            # from these partial requests, we do so for simplicity.
            # We will ignore the sampled tokens from the partial requests.
            # TODO: Support prompt logprobs.
            logits_indices = query_start_loc[1:] - 1
            spec_decode_metadata = None
            num_sampled_tokens = np.ones(num_reqs, dtype=np.int32)
        else:
            # Get the number of draft tokens for each request.
            # Iterate over the dictionary rather than all requests since not all
            # requests have draft tokens.
            num_draft_tokens = np.zeros(num_reqs, dtype=np.int32)
            # For chunked prefills, use -1 as mask rather than 0, as guided
            # decoding may rollback speculative tokens.
            num_decode_draft_tokens = np.full(num_reqs, -1, dtype=np.int32)
            for (
                req_id,
                draft_token_ids,
            ) in scheduler_output.scheduled_spec_decode_tokens.items():
                req_idx = self.input_batch.req_id_to_index[req_id]
                draft_len = len(draft_token_ids)
                num_draft_tokens[req_idx] = draft_len
                if (
                    self.input_batch.num_computed_tokens_cpu[req_idx]
                    >= self.input_batch.num_prompt_tokens[req_idx]
                ):
                    num_decode_draft_tokens[req_idx] = draft_len
            spec_decode_metadata = self._calc_spec_decode_metadata(
                num_draft_tokens, cu_num_tokens
            )
            logits_indices = spec_decode_metadata.logits_indices
            num_sampled_tokens = num_draft_tokens + 1
            # For DECODE only cuda graph of some attention backends (e.g., GDN).
            self.num_decode_draft_tokens.np[:num_reqs] = num_decode_draft_tokens
            self.num_decode_draft_tokens.np[num_reqs:].fill(-1)
            self.num_decode_draft_tokens.copy_to_gpu()

        # Hot-Swap lora model
        if self.lora_config:
            assert (
                np.sum(num_sampled_tokens)
                <= self.vllm_config.scheduler_config.max_num_batched_tokens
            )
            self.set_active_loras(
                self.input_batch, num_scheduled_tokens, num_sampled_tokens
            )

        return (
            logits_indices,
            spec_decode_metadata,
        )