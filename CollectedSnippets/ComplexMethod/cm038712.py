def validate_block_size(self) -> None:
        """Validate block_size against DCP and mamba constraints.

        Called after Platform.update_block_size_for_backend() has
        finalised block_size.
        """
        block_size = self.cache_config.block_size

        # DCP interleave-size compatibility
        if self.parallel_config.decode_context_parallel_size > 1:
            if self.parallel_config.dcp_kv_cache_interleave_size > 1 and (
                self.parallel_config.cp_kv_cache_interleave_size
                != self.parallel_config.dcp_kv_cache_interleave_size
            ):
                self.parallel_config.cp_kv_cache_interleave_size = (
                    self.parallel_config.dcp_kv_cache_interleave_size
                )
                logger.warning_once(
                    "cp_kv_cache_interleave_size is overridden by dcp_kv_cache"
                    "_interleave_size. And dcp-kv-cache-interleave-size will be "
                    "deprecated when PCP is fully supported."
                )
            assert (
                self.parallel_config.cp_kv_cache_interleave_size <= block_size
                and block_size % self.parallel_config.cp_kv_cache_interleave_size == 0
            ), (
                f"Block_size({block_size}) should be greater "
                "than or equal to and divisible by cp_kv_cache_interleave_size "
                f"({self.parallel_config.cp_kv_cache_interleave_size})."
            )

        # Mamba cache align-mode constraints
        if self.cache_config.mamba_cache_mode == "align":
            assert block_size <= self.scheduler_config.max_num_batched_tokens, (
                "In Mamba cache align mode, block_size "
                f"({block_size}) must be <= "
                "max_num_batched_tokens "
                f"({self.scheduler_config.max_num_batched_tokens})."
            )
            if self.scheduler_config.long_prefill_token_threshold > 0:
                assert self.scheduler_config.long_prefill_token_threshold >= block_size
            assert not self.scheduler_config.disable_chunked_mm_input, (
                "Chunked MM input is required because we need the flexibility "
                "to schedule a multiple of block_size tokens even if they are "
                "in the middle of a mm input"
            )