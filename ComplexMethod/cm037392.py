def initialize_kv_cache(
        self,
        kv_cache_config: KVCacheConfig,
        is_profiling: bool = False,
    ) -> None:
        """
        Initialize KV cache based on `kv_cache_config`.
        Args:
            kv_cache_config: Configuration for the KV cache, including the KV
            cache size of each layer
        """
        kv_cache_config = deepcopy(kv_cache_config)
        self.kv_cache_config = kv_cache_config
        self._mamba_copy_bufs = None
        self.may_add_encoder_only_layers_to_kv_cache_config()
        self.maybe_add_kv_sharing_layers_to_kv_cache_groups(kv_cache_config)
        self.initialize_attn_backend(kv_cache_config, is_profiling=is_profiling)
        initialize_mamba_ssu_backend(
            self.vllm_config.mamba_config, self.kv_cache_config
        )
        # The kernel block size for all KV cache groups. For example, if
        # kv_cache_manager uses block_size 256 for a given group, but the attention
        # backends for that group only supports block_size 64, we will return
        # kernel_block_size 64 and split the 256-token-block to 4 blocks with 64
        # tokens each.
        kernel_block_sizes = prepare_kernel_block_sizes(
            kv_cache_config, self.attn_groups
        )
        self._kernel_block_sizes = kernel_block_sizes

        # create metadata builders
        self.initialize_metadata_builders(kv_cache_config, kernel_block_sizes)

        # Reinitialize need to after initialize_attn_backend
        self.may_reinitialize_input_batch(kv_cache_config, kernel_block_sizes)
        kv_caches = self.initialize_kv_cache_tensors(
            kv_cache_config, kernel_block_sizes
        )

        if (
            self.speculative_config
            and self.speculative_config.uses_extract_hidden_states()
        ):
            assert isinstance(self.drafter, ExtractHiddenStatesProposer)
            # validate all draft model layers belong to the same kv cache
            # group
            self.drafter.validate_same_kv_cache_group(kv_cache_config)

        if has_kv_transfer_group() and not is_profiling:
            kv_transfer_group = get_kv_transfer_group()
            if self.cross_layers_kv_cache is not None:
                assert self.cross_layers_attn_backend is not None
                kv_transfer_group.register_cross_layers_kv_cache(
                    self.cross_layers_kv_cache, self.cross_layers_attn_backend
                )
            else:
                kv_transfer_group.register_kv_caches(kv_caches)
            kv_transfer_group.set_host_xfer_buffer_ops(copy_kv_blocks)