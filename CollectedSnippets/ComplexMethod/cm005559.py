def schedule_batch(
        self, token_budget: int, cache_budget: int
    ) -> tuple[list[FutureRequestState] | None, bool, int, int]:
        priority_states: list[RequestState] = []
        second_priority_states: list[RequestState] = []

        for state in self.active_requests.values():
            if state.status == RequestStatus.DECODING:
                priority_states.append(state)
            elif state.status == RequestStatus.PREFILLING:
                second_priority_states.append(state)

        # Add waiting requests to second priority
        if not self.block_new_requests:
            for req_id in self.waiting_requests_order:
                second_priority_states.append(self.waiting_requests[req_id])

        candidates = priority_states + second_priority_states
        request_ids_to_remove_from_waiting = set()
        scheduled_requests, one_allocation_failed, decode_fast_path, num_q_tokens, max_kv_read = (
            self._process_candidates(
                candidates,
                token_budget,
                cache_budget,
                request_ids_to_remove_from_waiting,
                safety_margin=self.safety_margin,
            )
        )

        # We remove waiting requests before checking requests were scheduled, because there might have been prefill matches
        self._cleanup_waiting_queue(request_ids_to_remove_from_waiting)

        # If no requests were scheduled and the cache is full, we signal it by returning None
        if not scheduled_requests and one_allocation_failed:
            return None, decode_fast_path, 0, 0

        return scheduled_requests, decode_fast_path, num_q_tokens, max_kv_read