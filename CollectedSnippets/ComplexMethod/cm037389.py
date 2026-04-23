def _check_and_update_cudagraph_mode(
        self,
        attention_backends: list[set[type[AttentionBackend]]],
        kv_cache_groups: list[KVCacheGroupSpec],
        is_profiling: bool = False,
    ) -> None:
        """
        Resolve the cudagraph_mode when there are multiple attention
        groups with potential conflicting CUDA graph support.
        Then initialize the cudagraph_dispatcher based on the resolved
        cudagraph_mode.
        """
        min_cg_support = AttentionCGSupport.ALWAYS
        min_cg_attn_backend = None

        for attn_backend_set, kv_cache_group in zip(
            attention_backends, kv_cache_groups
        ):
            for attn_backend in attn_backend_set:
                builder_cls = attn_backend.get_builder_cls()

                cg_support = builder_cls.get_cudagraph_support(
                    self.vllm_config, kv_cache_group.kv_cache_spec
                )
                if cg_support.value < min_cg_support.value:
                    min_cg_support = cg_support
                    min_cg_attn_backend = attn_backend.__name__
        cudagraph_mode = self.compilation_config.resolve_cudagraph_mode_and_sizes(
            min_cg_support,
            min_cg_attn_backend,
            self.uniform_decode_query_len,
            self.parallel_config.tensor_parallel_size,
            self.kv_cache_config,
            self.max_num_reqs,
            is_profiling=is_profiling,
        )
        # Trigger cudagraph dispatching keys initialization after
        # resolved cudagraph mode.
        self.cudagraph_dispatcher.initialize_cudagraph_keys(
            cudagraph_mode, self.uniform_decode_query_len
        )

        # Initialize drafter's cudagraph dispatcher if using spec decode.
        if self.speculative_config and (
            self.speculative_config.use_eagle()
            or self.speculative_config.uses_extract_hidden_states()
        ):
            assert isinstance(
                self.drafter,
                EagleProposer | DFlashProposer | ExtractHiddenStatesProposer,
            )
            self.drafter.initialize_cudagraph_keys(cudagraph_mode)