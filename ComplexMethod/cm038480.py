def build_connector_meta(
        self,
        scheduler_output: SchedulerOutput,
    ) -> KVConnectorMetadata:
        """Build the connector metadata for this step.

        This function should NOT modify any fields in the scheduler_output.
        Also, calling this function will reset the state of the connector.

        Args:
            scheduler_output (SchedulerOutput): the scheduler output object.
        """

        meta = P2pNcclConnectorMetadata()

        for new_req in scheduler_output.scheduled_new_reqs:
            if self.is_producer:
                num_scheduled_tokens = (scheduler_output.num_scheduled_tokens)[
                    new_req.req_id
                ]
                num_tokens = num_scheduled_tokens + new_req.num_computed_tokens
                # the request's prompt is chunked prefill
                if num_tokens < len(new_req.prompt_token_ids or []):
                    # 'CachedRequestData' has no attribute 'prompt_token_ids'
                    self.chunked_prefill[new_req.req_id] = (
                        new_req.block_ids[0],
                        new_req.prompt_token_ids,
                    )
                    continue
                # the request's prompt is not chunked prefill
                meta.add_request(
                    request_id=new_req.req_id,
                    token_ids=new_req.prompt_token_ids or [],
                    block_ids=new_req.block_ids[0],
                    block_size=self._block_size,
                )
                continue
            if new_req.req_id in self._requests_need_load:
                meta.add_request(
                    request_id=new_req.req_id,
                    token_ids=new_req.prompt_token_ids or [],
                    block_ids=new_req.block_ids[0],
                    block_size=self._block_size,
                )
                self._requests_need_load.pop(new_req.req_id)

        cached_reqs = scheduler_output.scheduled_cached_reqs
        for i, req_id in enumerate(cached_reqs.req_ids):
            num_computed_tokens = cached_reqs.num_computed_tokens[i]
            new_block_ids = cached_reqs.new_block_ids[i]
            resumed_from_preemption = req_id in cached_reqs.resumed_req_ids

            if self.is_producer:
                num_scheduled_tokens = scheduler_output.num_scheduled_tokens[req_id]
                num_tokens = num_scheduled_tokens + num_computed_tokens
                assert req_id in self.chunked_prefill
                assert new_block_ids is not None
                block_ids = new_block_ids[0]
                if not resumed_from_preemption:
                    block_ids = self.chunked_prefill[req_id][0] + block_ids
                prompt_token_ids = self.chunked_prefill[req_id][1]
                assert prompt_token_ids is not None
                # the request's prompt is chunked prefill again
                if num_tokens < len(prompt_token_ids):
                    self.chunked_prefill[req_id] = (block_ids, prompt_token_ids)
                    continue
                # the request's prompt is all prefilled finally
                meta.add_request(
                    request_id=req_id,
                    token_ids=prompt_token_ids,
                    block_ids=block_ids,
                    block_size=self._block_size,
                )
                self.chunked_prefill.pop(req_id, None)
                continue

            # NOTE(rob): here we rely on the resumed requests being
            # the first N requests in the list scheduled_cache_reqs.
            if not resumed_from_preemption:
                break
            if req_id in self._requests_need_load:
                request, _ = self._requests_need_load.pop(req_id)
                total_tokens = num_computed_tokens + 1
                token_ids = request.all_token_ids[:total_tokens]

                # NOTE(rob): For resumed req, new_block_ids is all
                # of the block_ids for the request.
                assert new_block_ids is not None
                block_ids = new_block_ids[0]

                meta.add_request(
                    request_id=req_id,
                    token_ids=token_ids,
                    block_ids=block_ids,
                    block_size=self._block_size,
                )

        self._requests_need_load.clear()
        return meta