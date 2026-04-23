def __init__(self, vllm_config: "VllmConfig", kv_cache_config: "KVCacheConfig"):
        logger.warning(
            "Initializing OffloadingSpec. This API is experimental and "
            "subject to change in the future as we iterate the design."
        )
        self.vllm_config = vllm_config
        self.kv_cache_config = kv_cache_config

        kv_transfer_config = vllm_config.kv_transfer_config
        assert kv_transfer_config is not None
        self.extra_config = kv_transfer_config.kv_connector_extra_config

        # block size used by vLLM for hashing request tokens for the sake
        # of enabling prefix caching
        self.hash_block_size = vllm_config.cache_config.block_size
        # gpu block size per group
        self.gpu_block_size: tuple[int, ...] = tuple(
            kv_cache_group.kv_cache_spec.block_size
            for kv_cache_group in kv_cache_config.kv_cache_groups
        )

        for block_size in self.gpu_block_size:
            assert block_size % self.hash_block_size == 0, (
                f"gpu_block_size={block_size} not divisible by "
                f"hash_block_size={self.hash_block_size}. "
                f"Hybrid models (e.g. Mamba+Attention) need "
                f"--enable-prefix-caching to align block sizes."
            )

        # offloaded_block_size / gpu_block_size
        self.block_size_factor: int = 1

        offloaded_block_size = self.extra_config.get("block_size")
        if offloaded_block_size is not None:
            offloaded_block_size_int = int(offloaded_block_size)
            gpu_block_sizes = set(self.gpu_block_size)
            assert len(gpu_block_sizes) == 1, (
                "If 'block_size' is specified in kv_connector_extra_config, "
                "there must be at least one KV cache group, "
                "and all groups must have the same block size."
            )
            gpu_block_size = gpu_block_sizes.pop()

            assert offloaded_block_size_int % gpu_block_size == 0
            self.block_size_factor = offloaded_block_size_int // gpu_block_size