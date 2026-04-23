def _prepare_input_ids(
        self,
        scheduler_output: "SchedulerOutput",
        num_reqs: int,
        total_num_scheduled_tokens: int,
        cu_num_tokens: np.ndarray,
    ) -> None:
        """Prepare the input IDs for the current batch.

        Carefully handles the `prev_sampled_token_ids` which can be cached
        from the previous engine iteration, in which case those tokens on the
        GPU need to be copied into the corresponding slots into input_ids.

        Uses self.prev_positions[:num_reqs] which maps current pos -> prev pos
        (-1 for new requests).
        """

        if self.input_batch.prev_sampled_token_ids is None:
            # Normal scheduling case
            self.input_ids.copy_to_gpu(total_num_scheduled_tokens)
            if self.enable_prompt_embeds:
                self.inputs_embeds.copy_to_gpu(total_num_scheduled_tokens)
                self.is_token_ids.copy_to_gpu(total_num_scheduled_tokens)
            return

        # Async scheduling case, where some decode requests from the previous
        # iteration won't have entries in input_ids_cpu and need to be copied
        # on the GPU from prev_sampled_token_ids.
        prev_positions = self.prev_positions.np[:num_reqs]
        scheduled_spec_tokens = scheduler_output.scheduled_spec_decode_tokens
        sample_flattened_indices: list[int] = []
        spec_flattened_indices: list[int] = []
        prev_draft_token_indices: list[int] = []
        prev_indices: list[int] = []
        common_indices_match = True
        max_flattened_index = -1
        total_num_spec_tokens = 0

        for cur_index in range(num_reqs):
            prev_index = prev_positions[cur_index]
            if prev_index < 0:
                continue
            prev_indices.append(prev_index)
            req_id = self.input_batch.req_ids[cur_index]
            # We need to compute the flattened input_ids index of the
            # last token in each common request.
            draft_len = len(scheduled_spec_tokens.get(req_id, ()))
            total_num_spec_tokens += draft_len
            flattened_index = cu_num_tokens[cur_index].item() - 1
            # example: cu_num_tokens = [2, 5, 8], draft_tokens = [1, 2, 2]
            # sample_flattened_indices = [0, 2, 5]
            # spec_flattened_indices = [1,   3, 4,    6, 7]
            sample_flattened_indices.append(flattened_index - draft_len)
            spec_flattened_indices.extend(
                range(flattened_index - draft_len + 1, flattened_index + 1)
            )
            start = prev_index * self.num_spec_tokens
            # prev_draft_token_indices is used to find which draft_tokens_id
            # should be copied to input_ids
            # example: prev draft_tokens_id [[1,2], [3,4], [5, 6]]
            # flatten draft_tokens_id [1,2,3,4,5,6]
            # draft_len of each request [1, 2, 1]
            # then prev_draft_token_indices is [0,   2, 3,   4]
            prev_draft_token_indices.extend(range(start, start + draft_len))
            common_indices_match &= prev_index == flattened_index
            max_flattened_index = max(max_flattened_index, flattened_index)

        num_common_tokens = len(sample_flattened_indices)
        total_without_spec = total_num_scheduled_tokens - total_num_spec_tokens
        if num_common_tokens < total_without_spec:
            # If not all requests are decodes from the last iteration,
            # we need to copy the input_ids_cpu to the GPU first.
            self.input_ids.copy_to_gpu(total_num_scheduled_tokens)
            if self.enable_prompt_embeds:
                self.inputs_embeds.copy_to_gpu(total_num_scheduled_tokens)
                self.is_token_ids.copy_to_gpu(total_num_scheduled_tokens)
        if num_common_tokens == 0:
            # No requests in common with the previous iteration
            # So input_ids.cpu will have all the input ids.
            return
        if common_indices_match and max_flattened_index == (num_common_tokens - 1):
            # Common-case optimization: the batch is unchanged
            # and no reordering happened.
            # The indices are both the same permutation of 0..N-1 so
            # we can copy directly using a single slice.
            self.input_ids.gpu[:num_common_tokens].copy_(
                self.input_batch.prev_sampled_token_ids[:num_common_tokens, 0],
                non_blocking=True,
            )
            if self.enable_prompt_embeds:
                self.is_token_ids.gpu[:num_common_tokens] = True
            return
        # Upload the index tensors asynchronously so the scatter can be non-blocking.
        sampled_tokens_index_tensor = torch.tensor(
            sample_flattened_indices, dtype=torch.int64, pin_memory=self.pin_memory
        ).to(self.device, non_blocking=True)
        prev_common_req_indices_tensor = torch.tensor(
            prev_indices, dtype=torch.int64, pin_memory=self.pin_memory
        ).to(self.device, non_blocking=True)
        self.input_ids.gpu.scatter_(
            dim=0,
            index=sampled_tokens_index_tensor,
            src=self.input_batch.prev_sampled_token_ids[
                prev_common_req_indices_tensor, 0
            ],
        )

        # Scatter the draft tokens after the sampled tokens are scattered.
        if self._draft_token_ids is None or not spec_flattened_indices:
            return

        assert isinstance(self._draft_token_ids, torch.Tensor)
        draft_tokens_index_tensor = torch.tensor(
            spec_flattened_indices, dtype=torch.int64, pin_memory=self.pin_memory
        ).to(self.device, non_blocking=True)
        prev_draft_token_indices_tensor = torch.tensor(
            prev_draft_token_indices, dtype=torch.int64, pin_memory=self.pin_memory
        ).to(self.device, non_blocking=True)

        # because input_ids dtype is torch.int32,
        # so convert draft_token_ids to torch.int32 here.
        draft_token_ids = self._draft_token_ids.to(dtype=torch.int32)

        self.input_ids.gpu.scatter_(
            dim=0,
            index=draft_tokens_index_tensor,
            src=draft_token_ids.flatten()[prev_draft_token_indices_tensor],
        )