def _set_compile_ranges(self):
        """
        Set the compile ranges for the compilation config.
        """
        compilation_config = self.compilation_config
        computed_compile_ranges_endpoints = []

        # The upper bound of the compile ranges is the max_num_batched_tokens.
        compile_range_end = self.scheduler_config.max_num_batched_tokens
        if compile_range_end is not None:
            computed_compile_ranges_endpoints.append(compile_range_end)

        # Add the compile ranges for flashinfer
        if compilation_config.pass_config.fuse_allreduce_rms:
            tp_size = self.parallel_config.tensor_parallel_size
            max_size = compilation_config.pass_config.flashinfer_max_size(tp_size)
            if max_size is not None:
                assert isinstance(self.model_config.dtype, torch.dtype)
                max_token_num = max_size // (
                    self.model_config.get_hidden_size()
                    * self.model_config.dtype.itemsize
                )
                if compile_range_end is not None and max_token_num < compile_range_end:
                    computed_compile_ranges_endpoints.append(max_token_num)
                else:
                    logger.debug(
                        "Max num batched tokens below allreduce-rms fusion threshold, "
                        "allreduce-rms fusion will be enabled for all num_tokens."
                    )

        # Add the compile ranges for sequence parallelism
        if compilation_config.pass_config.enable_sp:
            pass_config = compilation_config.pass_config

            # Calculate min_token_num if not explicitly provided
            # User override works regardless of hidden_size
            if pass_config.sp_min_token_num is None:
                from vllm.compilation.passes.fusion.sequence_parallelism import (
                    get_sequence_parallelism_threshold,
                )

                tp_size = self.parallel_config.tensor_parallel_size
                hidden_size = self.model_config.get_hidden_size()
                assert isinstance(self.model_config.dtype, torch.dtype)
                element_size = self.model_config.dtype.itemsize
                pass_config.sp_min_token_num = get_sequence_parallelism_threshold(
                    hidden_size, tp_size, element_size
                )

            min_token_num = pass_config.sp_min_token_num
            max_num_batched_tokens = self.scheduler_config.max_num_batched_tokens
            if min_token_num is not None and (
                max_num_batched_tokens is not None
                and min_token_num < max_num_batched_tokens
                and min_token_num > 1
            ):
                # Add endpoint at min_token_num - 1 to ensure SP applies
                # starting from min_token_num
                # This creates ranges: [1, min-1] (no SP), [min, max] (SP applies)
                computed_compile_ranges_endpoints.append(min_token_num - 1)

        if compilation_config.pass_config.fuse_rope_kvcache:
            max_token_num = (
                compilation_config.pass_config.rope_kvcache_fusion_max_token_num
            )
            if max_token_num is not None:
                if compile_range_end is not None and max_token_num < compile_range_end:
                    computed_compile_ranges_endpoints.append(max_token_num)
                else:
                    logger.debug(
                        "Max num batched tokens below rope+kvcache fusion threshold, "
                        "rope+kvcache fusion enabled for num_tokens <= %d.",
                        compile_range_end,
                    )

        if compilation_config.pass_config.fuse_minimax_qk_norm:
            from vllm.compilation.passes.fusion.minimax_qk_norm_fusion import (
                MAX_TOKEN_NUM,
            )

            max_token_num = min(
                MAX_TOKEN_NUM, self.scheduler_config.max_num_batched_tokens
            )
            if compile_range_end is not None and max_token_num < compile_range_end:
                computed_compile_ranges_endpoints.append(max_token_num)
            else:
                logger.debug(
                    "Max num batched tokens below MiniMax QK norm fusion threshold, "
                    "MiniMax QK norm fusion enabled for all num_tokens."
                )

        if compilation_config.compile_ranges_endpoints is not None:
            for x in compilation_config.compile_ranges_endpoints:
                assert isinstance(x, int)
                assert x > 0, f"Invalid compile range endpoint: {x}"
                if compile_range_end is not None and x < compile_range_end and x > 1:
                    computed_compile_ranges_endpoints.append(x)
        compilation_config.compile_ranges_endpoints = sorted(
            computed_compile_ranges_endpoints
        )