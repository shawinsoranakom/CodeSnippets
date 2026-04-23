def _process_candidates(
        self,
        candidates: list[RequestState],
        token_budget: int,
        cache_budget: int,
        request_ids_to_remove_from_waiting: set[str],
        safety_margin: float = 0.0,
    ) -> tuple[list[FutureRequestState], bool, bool, int, int]:
        """Schedules candidate requests for the current batch.

        This method contains the common logic shared by all schedulers: it checks token and cache budgets, allocates
        cache blocks if needed, updates request states, and tracks which waiting requests should be removed from the
        waiting queue.
        """
        scheduled_requests = []
        one_allocation_failed = False
        decode_fast_path = True
        safety_margins = safety_margin * self.cache.num_blocks
        original_token_budget, original_cache_budget = token_budget, cache_budget

        for state in candidates:
            num_free_blocks = self.cache.get_num_free_blocks()
            # If we are out the safety margin, we only accept decoding requests or the first prefill request
            outside_safety_margin = num_free_blocks < safety_margins
            if outside_safety_margin and scheduled_requests and state.status != RequestStatus.DECODING:
                logger.info(
                    f"Outside safety margin, breaking out of scheduling loop. {num_free_blocks = } {safety_margins = }"
                )
                break

            # Check cache budget
            read_cache_needed = state.current_len()
            if self.read_cache_limit is not None:
                read_cache_needed = min(read_cache_needed, self.read_cache_limit)
            if cache_budget < read_cache_needed:
                continue

            # Infer the tokens that will be present in the batch if token budget is enough
            request_tokens = self._infer_request_tokens(state, request_ids_to_remove_from_waiting)
            # Account for token budget
            request_len = min(len(request_tokens), token_budget)
            # Check there will be enough cache for the new tokens
            allocation_successful = self._allocate_blocks_if_needed(state, request_len)

            # If the allocation would not be successful, we move on to the next request
            if not allocation_successful:
                one_allocation_failed = True
                # If we reached a waiting request and the cache is full, all subsequent waiting requests will need
                # allocation as well, so we can safely break out of the scheduling loop.
                if num_free_blocks == 0 and state.request_id in self.waiting_requests:
                    logger.info(f"Breaking mid-loop for request {state.request_id} because the cache is full")
                    break
                continue

            # If this point is reached, it means we can safely schedule the request
            self._schedule_request(state, request_tokens, token_budget, request_ids_to_remove_from_waiting)
            request_len = len(state.tokens_to_process)  # it may change after scheduling

            # The decode fast path is only used if the request is a single token and its length is less than the max blocks per request
            decode_fast_path &= request_len == 1 and state.position_offset < self.max_decode_fast_path_length

            # Update the token and cache budgets
            token_budget -= request_len
            cache_budget -= read_cache_needed

            # If using prefix sharing, we make note of the blocks that will be computed in the forward pass
            if self.cache.allow_block_sharing:
                tokens_in_current_block = state.current_len() % self.cache.block_size
                tokens_after_forward = tokens_in_current_block + request_len
                complete_blocks = tokens_after_forward // self.cache.block_size
            else:
                complete_blocks = 0

            # Store the future request state
            has_new_token = not state.remaining_prefill_tokens
            scheduled_requests.append(FutureRequestState(state, has_new_token, complete_blocks, request_len))

            # Remove the request from the waiting queue and mark it as removed
            req_id = state.request_id
            was_waiting = self.waiting_requests.pop(req_id, None) is not None
            if was_waiting:
                request_ids_to_remove_from_waiting.add(req_id)

            # Early exit of the loop if we have no budget left
            if token_budget == 0 or cache_budget == 0:
                break

        num_q_tokens = original_token_budget - token_budget
        max_kv_read = original_cache_budget - cache_budget
        return scheduled_requests, one_allocation_failed, decode_fast_path, num_q_tokens, max_kv_read