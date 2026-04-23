def update_batch(self) -> None:
        """Update request states based on generated tokens."""
        requests_in_batch, new_tokens, logprobs = self.inputs_and_outputs.prepare_batch_update()
        current_logits_index = 0
        pending_outputs = []
        for future_state in requests_in_batch:
            state = future_state.state
            # Early return if the request is finished
            if state.status == RequestStatus.FINISHED:
                if self.use_async_batching:
                    # Skip this request, but still consume its token from new_tokens if it had one
                    if future_state.has_new_token:
                        current_logits_index += 1
                    continue
                raise RuntimeError(f"Tried to update FINISHED request {state.request_id} in sync mode.")
            # If the request has a new token, it means prefill has already ended or just finished
            if future_state.has_new_token:
                # If there is just one temporary token, it means prefill just ended
                if state.generated_len() == 0:
                    self.metrics.record_ttft_metric(state.created_time, state.request_id)
                    state.status = RequestStatus.DECODING

                token = new_tokens[current_logits_index]
                logprob = logprobs[current_logits_index] if logprobs is not None else None
                current_logits_index += 1

                # Update the request and stop if it is complete
                is_finished = state.update_and_check_completion(token, logprob)
                # We mark the completed blocks as such
                self.cache.mark_shareable_blocks_as_complete(state, future_state.complete_blocks)
                if is_finished:
                    self.metrics.record_request_completion(state.created_time, state.request_id)
                    self.scheduler.finish_request(state.request_id)
                    self.scheduler.block_new_requests = False
                if state.streaming or state.status == RequestStatus.FINISHED:
                    pending_outputs.append(state.to_generation_output())
            #  Otherwise, the request is still prefilling, but the prefill has been split
            elif state.status == RequestStatus.PREFILLING:
                self.cache.mark_shareable_blocks_as_complete(state, future_state.complete_blocks)

        if pending_outputs:
            self.output_router.deliver_batch(pending_outputs)

        # If some requests need to be forked, we do it now
        copy_source, copy_destination = [], []
        while self.scheduler._requests_to_fork:
            # Get the number of children and reset it so it's not forked again
            state_to_fork = self.scheduler._requests_to_fork.pop()
            num_children = state_to_fork.num_children
            state_to_fork.num_children = 0
            # Create the new request and add them to the scheduler
            new_request_ids = [f"{state_to_fork.request_id}__child#{i}" for i in range(num_children)]
            for new_request_id in new_request_ids:
                self.scheduler.active_requests[new_request_id] = state_to_fork.fork(new_request_id)
            # Fork the cache
            copy_src, copy_dst = self.cache.fork_request(state_to_fork.request_id, new_request_ids)
            copy_source.extend(copy_src)
            copy_destination.extend(copy_dst)
            # FIXME: if fork cant be done, create a new pending request without forking instead of crashing everything

        # The copy induced by the fork is done in one go (if it's even needed)
        if copy_source:
            # FIXME: this will avoid any race condition, but it can cause issue when using async batching with a sliding
            # window model. Fix will be fixed in a PR in the near future (tempfix, v5.3)
            compute_stream = self.inputs_and_outputs.compute_stream
            maybe_stream = torch.cuda.stream(compute_stream) if compute_stream is not None else nullcontext()
            with maybe_stream:
                self.cache.copy_cache(copy_source, copy_destination)