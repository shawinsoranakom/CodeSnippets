def prepare_batch_tensors(
        self,
        requests_in_batch: list[FutureRequestState],
        logits_processors: ContinuousBatchingLogitsProcessorList,
        use_decode_fast_path: bool,
        num_q_tokens: int,
        max_kv_read: int,
    ) -> None:
        """Prepare tensors and metadata for the next model forward pass, using the given requests as data. This method:

        1. Resets the static tensors from the previous batch
        2. Iterates through requests to accumulate input_ids, position_ids, and sequence lengths
        3. Extends read/write indices for cache management
        4. Builds attention masks if needed (for eager/SDPA implementations)
        5. Converts accumulated lists to tensors and copies them to static storage

        This method also modifies the `position_offset` attribute of each request to track progress and adds a
        temporary token at the end of the requests for which there will a new token.
        """
        # Keep track of this requests in the batch, which will be useful to update the batch later
        if not requests_in_batch:
            raise ValueError("No requests in batch")

        # Determine if the block table is used before we start to prepare the batch, to avoid useless preparation
        self.use_block_table = use_decode_fast_path and self.block_table.numel() > 0
        # Memoize the length of Q and KV
        self.num_q_tokens = num_q_tokens
        self.max_kv_read = 0 if self.use_block_table else max_kv_read  # No need to track KV read for decode-fast-path
        self.true_batch_size = len(requests_in_batch)
        # Reset the static storage that is going to be used for the next batch
        self._reset_static_tensors()

        # Reset accumulators
        self.true_read_sizes = [0 for _ in range(self.cache.num_groups)]
        self.true_write_sizes = [0 for _ in range(self.cache.num_groups)]
        self.requests_in_batch = []
        self.req_id_to_new_token_position = {}

        # Prepare accumulators
        input_ids = []
        position_ids = []
        cumulative_seqlens_q = [0]
        logits_indices = []
        cumulative_seqlens_k = {layer_type: [0] for layer_type in self.cumulative_seqlens_k.keys()}
        read_index = [[] for _ in range(self.cache.num_groups)]
        write_index = [[] for _ in range(self.cache.num_groups)]

        # Go through all the requests in the batch
        for i, future_state in enumerate(requests_in_batch):
            # First we retrieve the lengths related to the request
            state = future_state.state
            past_length = state.position_offset
            query_length = future_state.query_length
            seqlens_k = self.cache.get_seqlens_k(past_length, query_length)

            # Update the internal state of the request
            state.position_offset += query_length

            # Then we accumulate for the object used in the kwargs
            input_ids.extend(state.tokens_to_process)
            position_ids.extend(range(past_length, past_length + query_length))
            cumulative_seqlens_q.append(cumulative_seqlens_q[-1] + query_length)
            self.max_seqlen_q = max(self.max_seqlen_q, query_length)

            # Accumulate the key sequence lengths for the current request
            for layer_type, layer_type_seqlen_k in seqlens_k.items():
                cumulative_seqlens_k[layer_type].append(cumulative_seqlens_k[layer_type][-1] + layer_type_seqlen_k)
                self.max_seqlen_k[layer_type] = max(self.max_seqlen_k[layer_type], layer_type_seqlen_k)

            # We extend the read and write indices for the cache, or fill the block table for decode-only batches
            if self.use_block_table:
                self.cache.fill_block_table(state.request_id, past_length, query_length, self.block_table[:, i])
            else:
                self.cache.extend_read_and_write_indices(
                    state.request_id, past_length, query_length, read_index, write_index
                )

            # If the request has no remaining prefill tokens, it means the next token prediction is relevant
            if future_state.has_new_token:
                logits_indices.append(cumulative_seqlens_q[-1] - 1)
                state.tokens_to_process = [TMP_TOKEN_ID]
                self.req_id_to_new_token_position[state.request_id] = logits_indices[-1]

            self.requests_in_batch.append(future_state)

        # Also prepare the tensor arguments for the logits processors
        logits_processors.prepare_tensor_args(
            requests_in_batch=requests_in_batch,
            arg_storage=self._bulk_input_tensor[self.static_inputs :],
        )

        # When looping over request is done, we can build the actual tensors. This is faster than modifying the static
        # tensors inside the loop.
        to_tensor = partial(torch.tensor, dtype=torch.int32, device=self.device)

        # Those kwargs always have the same type regardless of the model
        self.input_ids[: len(input_ids)] = to_tensor(input_ids)
        self.position_ids[: len(position_ids)] = to_tensor(position_ids)
        self.cumulative_seqlens_q[: len(cumulative_seqlens_q)] = to_tensor(cumulative_seqlens_q)
        self.logits_indices[: len(logits_indices)] = to_tensor(logits_indices)
        self.total_seqlen_q = cumulative_seqlens_q[-1]

        # Those kwargs are either dict of tensors or tensors, so we need to handle both cases
        for layer_type, layer_type_seqlens_k in cumulative_seqlens_k.items():
            self.cumulative_seqlens_k[layer_type][: len(layer_type_seqlens_k)] = to_tensor(layer_type_seqlens_k)
            if self.attention_mask is not None:
                build_attention_mask(
                    attention_mask=self.attention_mask[layer_type],
                    cumulative_seqlens_q=cumulative_seqlens_q,
                    cumulative_seqlens_k=layer_type_seqlens_k,
                    sliding_window=self.sliding_window if layer_type == "sliding_attention" else 1,
                )

        # If we are not using the block table, we populate the read and write indices
        if not self.use_block_table:
            to_index_tensor = partial(torch.tensor, dtype=torch.int64, device=self.device)
            for i, group_read_indices, group_write_indices in zip(count(), read_index, write_index):
                self.read_index_storage[i, : len(group_read_indices)] = to_index_tensor(group_read_indices)
                self.write_index_storage[i, : len(group_write_indices)] = to_index_tensor(group_write_indices)
                self.true_read_sizes[i] = len(group_read_indices)
                self.true_write_sizes[i] = len(group_write_indices)