def update_state_after_alloc(self, request: "Request", num_external_tokens: int):
        """
        Update KVConnector state after temporary buffer alloc.

        For SharedStorageConnector, update _request_needs_load
        if the CacheManager this allocated blocks for us.
        """

        # Clear local status in lookup client when a new request is
        # successfully scheduled.
        self.lookup_client.clear_lookup_status(request.request_id)

        kv_transfer_params = (
            request.kv_transfer_params
            if hasattr(request, "kv_transfer_params")
            else None
        )

        if kv_transfer_params is not None and "disagg_spec" in kv_transfer_params:
            req_disagg_spec = kv_transfer_params["disagg_spec"]

            receiver_id = req_disagg_spec["receiver_host"] + str(
                req_disagg_spec["receiver_init_port"]
            )

            disagg_spec = DisaggSpec(
                req_id=req_disagg_spec["req_id"],
                receiver_id=receiver_id,
                receiver_host=req_disagg_spec["receiver_host"],
                receiver_init_port=req_disagg_spec["receiver_init_port"],
                receiver_alloc_port=req_disagg_spec["receiver_alloc_port"],
            )

            tmp_disagg_tracker[request.request_id] = disagg_spec
        self._unfinished_requests[request.request_id] = request

        if request.request_id not in self.load_specs:
            # No KV tokens from external KV cache, return
            return

        if num_external_tokens == 0:
            # No need to load anything
            self.load_specs[request.request_id].can_load = False
            return

        # Only check for non-prompt-hit case
        if (
            self.load_specs[request.request_id].lmcache_cached_tokens
            != request.num_tokens
        ):
            assert (
                num_external_tokens > 0
                and num_external_tokens
                == self.load_specs[request.request_id].lmcache_cached_tokens
                - self.load_specs[request.request_id].vllm_cached_tokens
            ), (
                f"Mismatch in number of tokens: {num_external_tokens} vs "
                f"{self.load_specs[request.request_id].lmcache_cached_tokens} -"
                f" {self.load_specs[request.request_id].vllm_cached_tokens}"
                f" for request {request.request_id}"
            )

        self.load_specs[request.request_id].can_load = True