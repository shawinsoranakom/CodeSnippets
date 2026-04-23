def get_num_new_matched_tokens(
        self, request: Request, num_computed_tokens: int
    ) -> tuple[int | None, bool]:
        """
        Get number of new tokens that can be loaded beyond the
        num_computed_tokens.

        Args:
            request (Request): the request object.
            num_computed_tokens (int): the number of locally
                computed tokens for this request

        Returns:
            A tuple with the following elements:
                - The number of tokens that can be loaded beyond what is
                  already computed.
                  If None, it means that the connector needs more time to
                  determine the number of matched tokens, and the scheduler
                  should query for this request again later.
                - `True` if tokens will be loaded asynchronously
                  (between scheduler steps).
        """
        if req_status := self._req_status.get(request.request_id):
            # make sure block IDs are cleared
            for group_state in req_status.group_states:
                group_state.block_ids.clear()
        else:
            req_status = RequestOffloadState(config=self.config, req=request)
            req_status.update_offload_keys()
            self._req_status[request.request_id] = req_status

        req_status.num_locally_computed_tokens = num_computed_tokens

        # Below assertions will be removed once this function supports HMA
        assert len(self.config.kv_group_configs) == 1
        assert len(req_status.group_states) == 1
        group_config = self.config.kv_group_configs[0]
        group_state = req_status.group_states[0]

        num_blocks = request.num_tokens // group_config.offloaded_block_size

        assert len(request.block_hashes) // self.config.block_size_factor == num_blocks
        offload_keys = group_state.offload_keys

        self.manager.touch(offload_keys)

        full_block_tokens = group_config.offloaded_block_size * num_blocks
        if full_block_tokens - num_computed_tokens < group_config.offloaded_block_size:
            # we can load less than a block, skip
            return 0, False

        start_block_idx = num_computed_tokens // group_config.offloaded_block_size
        # Full attention relays on all previous KV cache blocks.
        # Thus, we search for a maximal prefix of KV cache which are all cached.
        hits = self._maximal_prefix_lookup(
            offload_keys[start_block_idx:], req_status.req_context
        )
        if hits is None:
            # indicates a lookup that should be tried later
            return None, False
        if hits == 0:
            return 0, False

        num_hit_tokens = (
            group_config.offloaded_block_size * (start_block_idx + hits)
            - num_computed_tokens
        )
        logger.debug(
            "Request %s hit %s offloaded tokens after %s GPU hit tokens",
            request.request_id,
            num_hit_tokens,
            num_computed_tokens,
        )
        if num_hit_tokens < group_config.offloaded_block_size:
            return 0, False

        if self._blocks_being_loaded and any(
            key in self._blocks_being_loaded
            for key in offload_keys[start_block_idx : start_block_idx + hits]
        ):
            # hit blocks are being loaded, delay request
            logger.debug(
                "Delaying request %s since some of its blocks are already being loaded",
                request.request_id,
            )
            return None, False

        return num_hit_tokens, True