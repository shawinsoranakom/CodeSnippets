def warmup(
        self,
        model: nn.Module,
        logit_processor: LogitsProcessorList,
        num_query_tokens: int = 0,
        num_cache_tokens: int = 0,
    ) -> None:
        """Pre-capture CUDA graphs (or trigger compile warmup) for varlen and decode paths. In async mode, both IO
        pairs are warmed up since each has its own graph buffer and static tensors."""

        if not self._pad_inputs:
            logger.info("CUDA graphs and compile are disabled, skipping warmup.")
            return None

        num_query_tokens = num_query_tokens if num_query_tokens > 0 else self.max_batch_tokens
        num_query_tokens = min(num_query_tokens, self.max_batch_tokens)
        num_cache_tokens = num_cache_tokens if num_cache_tokens > 0 else self.cache.block_size * num_query_tokens
        num_cache_tokens = min(num_cache_tokens, self.cache.num_blocks * self.cache.block_size)

        num_pages = self.cache.num_blocks * self.cache.block_size
        compute_stream = self.inputs_and_outputs.compute_stream

        # In async mode, each IO pair has its own graph buffer and static tensors, so we warm up both
        num_io_pairs = 2 if self.use_async_batching else 1

        for pair_idx in range(num_io_pairs):
            if self.use_async_batching:
                self.inputs_and_outputs.current_pair = pair_idx
                logger.info(f"Warming up IO pair {pair_idx + 1}/2...")

            # --- Varlen path ---
            padded_q = pad_to_interval(num_query_tokens, self.q_padding_interval_size, self.max_batch_tokens)
            padded_kv = pad_to_interval(num_cache_tokens + num_query_tokens, self.kv_padding_interval_size, num_pages)
            logger.info(f"Warming up varlen path ({padded_q} Q tokens, {padded_kv} KV tokens)...")

            future_states = create_warmup_future_states(
                1, RequestStatus.PREFILLING, num_query_tokens, num_cache_tokens, self.cache
            )
            try:
                start = perf_counter()
                self.inputs_and_outputs.prepare_batch_tensors(
                    future_states, self.logit_processor, False, padded_q, padded_kv - padded_q
                )
                batch_data = self.inputs_and_outputs.get_model_kwargs(use_padding=True)
                carry_over_ids, prev_output_ids, output_ids = self.inputs_and_outputs.get_cb_kwargs()
                forward_fn = self._compiled_varlen or self._forward_process_and_sample
                forward_fn_args = (model, batch_data, carry_over_ids, prev_output_ids, output_ids)
                if self.use_cuda_graph_varlen:
                    self.capture_graph(forward_fn, compute_stream, *forward_fn_args)
                else:
                    with torch.cuda.stream(compute_stream):
                        forward_fn(*forward_fn_args)
                logger.info(f"Varlen warmup completed in {perf_counter() - start:.2f}s")
            except Exception as e:
                logger.warning(f"Failed to warm up varlen path: {e}")
            finally:
                for fs in future_states:
                    self.cache.free_blocks(fs.state.request_id)

            # Exit here if the decode fast path is not available
            if self.cache.max_blocks_per_request == 0:
                continue

            # --- Decode fast path ---
            logger.info("Warming up decode fast path...")
            q_interval = self.q_padding_interval_size  # shorthand to avoid overly long lines
            decode_graphs = 0
            start = perf_counter()
            # If N requests reach decoding stage, then the number of query tokens is going to start at N and decrease to
            # 0 as all request finish. So we warmup for all intervals between 0 and N.
            for num_requests in range(q_interval, num_query_tokens + q_interval, q_interval):
                future_states = create_warmup_future_states(
                    num_requests, RequestStatus.DECODING, 1, self.cache.block_size, self.cache
                )
                if not future_states:
                    continue
                try:
                    padded_q = pad_to_interval(len(future_states), q_interval, self.max_batch_tokens)
                    self.inputs_and_outputs.prepare_batch_tensors(
                        future_states, self.logit_processor, True, padded_q, 0
                    )
                    batch_data = self.inputs_and_outputs.get_model_kwargs(use_padding=True)
                    carry_over_ids, prev_output_ids, output_ids = self.inputs_and_outputs.get_cb_kwargs()
                    forward_fn = self._compiled_decode or self._forward_process_and_sample
                    forward_fn_args = (model, batch_data, carry_over_ids, prev_output_ids, output_ids)
                    if self.use_cuda_graph_decode:
                        self.capture_graph(forward_fn, compute_stream, *forward_fn_args)
                    else:
                        with torch.cuda.stream(compute_stream):
                            forward_fn(*forward_fn_args)
                    decode_graphs += 1
                except Exception as e:
                    logger.warning(f"Failed to warm up decode path for {num_requests} requests: {e}")
                finally:
                    for fs in future_states:
                        self.cache.free_blocks(fs.state.request_id)
            logger.info(f"Decode warmup completed ({decode_graphs} graphs) in {perf_counter() - start:.2f}s.")

        # If using async batching, reset to pair 0 for the generation loop
        if self.use_async_batching:
            self.inputs_and_outputs.current_pair = 0