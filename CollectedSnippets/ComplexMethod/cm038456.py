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
        meta = ExampleConnectorMetadata()

        total_need_load = 0
        for new_req in scheduler_output.scheduled_new_reqs:
            token_ids = new_req.prompt_token_ids or []
            mm_hashes = [f.identifier for f in new_req.mm_features]
            if new_req.req_id in self._requests_need_load:
                meta.add_request(
                    token_ids=token_ids,
                    block_ids=new_req.block_ids[0],
                    block_size=self._block_size,
                    is_store=False,
                    mm_hashes=mm_hashes,
                )
                total_need_load += 1
            else:
                # NOTE: here, we set the store and load being exclusive,
                # but a single request can have both store and load.
                # NOTE(rob): for this debug implementation, we only cache
                # the original prompt tokens.
                if not self._found_match_for_prompt(token_ids, mm_hashes):
                    meta.add_request(
                        token_ids=token_ids,
                        block_ids=new_req.block_ids[0],
                        block_size=self._block_size,
                        is_store=True,
                        mm_hashes=mm_hashes,
                    )

        cached_reqs = scheduler_output.scheduled_cached_reqs
        for i, req_id in enumerate(cached_reqs.req_ids):
            resumed_from_preemption = req_id in cached_reqs.resumed_req_ids
            if not resumed_from_preemption or req_id not in self._requests_need_load:
                continue

            num_computed_tokens = cached_reqs.num_computed_tokens[i]
            num_new_tokens = scheduler_output.num_scheduled_tokens[req_id]
            new_block_ids = cached_reqs.new_block_ids[i]

            # NOTE(rob): cached_req_data does not have the full
            # list of token ids (only new tokens). So we look it
            # up in the actual request object.
            request = self._requests_need_load[req_id]
            total_tokens = num_computed_tokens + num_new_tokens
            token_ids = request.all_token_ids[:total_tokens]

            # NOTE(rob): For resumed req, new_block_ids is all
            # of the block_ids for the request.
            assert new_block_ids is not None
            block_ids = new_block_ids[0]

            meta.add_request(
                token_ids=token_ids,
                block_ids=block_ids,
                block_size=self._block_size,
                is_store=False,
                mm_hashes=[f.identifier for f in request.mm_features],
            )
            total_need_load += 1

        assert total_need_load == len(self._requests_need_load)
        self._requests_need_load.clear()
        return meta