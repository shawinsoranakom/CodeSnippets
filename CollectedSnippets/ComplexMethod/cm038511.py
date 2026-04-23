def get_num_new_matched_tokens(
        self,
        request: "Request",
        num_computed_tokens: int,
    ) -> int | None:
        """
        Check for external KV cache hit.

        Args:
            request (Request): the request object.
            num_computed_tokens (int): the number of locally
                computed tokens for this request

        Returns:
            the number of tokens that can be loaded from the
            external KV cache beyond what is already computed.
        """
        if self.kv_role == "kv_producer" and not hasattr(
            self.lookup_client, "supports_producer_reuse"
        ):
            return 0

        self._requests_priority[request.request_id] = request.priority

        token_ids = request.prompt_token_ids

        # If the request has multimodal hashes, apply them to the token ids
        mm_hashes, mm_positions = extract_mm_features(request)
        if mm_hashes and mm_positions:
            # TODO(Jiayi): Optimize this
            token_ids_tensor = torch.tensor(request.prompt_token_ids)
            apply_mm_hashes_to_token_ids(token_ids_tensor, mm_hashes, mm_positions)
            token_ids = token_ids_tensor.tolist()

        if request.sampling_params:
            request_configs = extract_request_configs(request.sampling_params)
        else:
            request_configs = None

        if self.skip_last_n_tokens > 0:
            assert token_ids is not None
            token_ids = token_ids[: -self.skip_last_n_tokens]
        lookup_id = request.request_id if self.async_loading else str(uuid.uuid4())

        self._lookup_requests_in_step.append(lookup_id)

        num_external_hit_tokens = self.lookup_client.lookup(
            token_ids,
            lookup_id=lookup_id,
            request_configs=request_configs,
        )

        if num_external_hit_tokens is None:
            logger.info(
                "Reqid: %s, Total tokens %d, LMCache hit tokens: None.",
                request.request_id,
                request.num_tokens,
            )
            return None

        # When prompt length is divisible by the block size and all
        # blocks are cached, we need to recompute the last token.
        # This will be removed in the future if vLLM's scheduler provides
        # a better support for this case.
        need_to_allocate = num_external_hit_tokens - num_computed_tokens

        # In, full-prompt-hit case, we need to recompute the last token
        if num_external_hit_tokens == request.num_tokens:
            need_to_allocate -= 1

        logger.info(
            "Reqid: %s, Total tokens %d, LMCache hit tokens: %d, need to load: %d",
            request.request_id,
            request.num_tokens,
            num_external_hit_tokens,
            need_to_allocate,
        )

        self.load_specs[request.request_id] = LoadSpec(
            vllm_cached_tokens=num_computed_tokens,
            lmcache_cached_tokens=num_external_hit_tokens,
            can_load=False,
        )

        if need_to_allocate <= 0:
            return 0

        return need_to_allocate