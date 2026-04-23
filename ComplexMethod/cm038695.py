def resolve_cudagraph_mode_and_sizes(
        self,
        min_cg_support: "AttentionCGSupport",
        min_cg_attn_backend: str | None,
        uniform_decode_query_len: int = 1,
        tensor_parallel_size: int = 1,
        kv_cache_config: "KVCacheConfig | None" = None,
        max_num_reqs: int | None = None,
        is_profiling: bool = False,
    ) -> CUDAGraphMode:
        from vllm.v1.attention.backend import AttentionCGSupport

        cudagraph_mode = self.cudagraph_mode
        if cudagraph_mode is None or cudagraph_mode == CUDAGraphMode.NONE:
            self.cudagraph_mode = CUDAGraphMode.NONE
            return CUDAGraphMode.NONE

        # Check cudagraph for mixed batch is supported
        if (
            cudagraph_mode.mixed_mode() == CUDAGraphMode.FULL
            and min_cg_support != AttentionCGSupport.ALWAYS
        ):
            msg = (
                f"CUDAGraphMode.{cudagraph_mode.name} is not supported "
                f"with {min_cg_attn_backend} backend (support: "
                f"{min_cg_support})"
            )
            if min_cg_support == AttentionCGSupport.NEVER:
                # if not supported any full cudagraphs, just raise it.
                msg += (
                    "; please try cudagraph_mode=PIECEWISE, and "
                    "make sure compilation mode is VLLM_COMPILE"
                )
                raise ValueError(msg)

            # attempt to resolve the full cudagraph related mode
            if self.splitting_ops_contain_attention():
                msg += "; setting cudagraph_mode=FULL_AND_PIECEWISE"
                cudagraph_mode = CUDAGraphMode.FULL_AND_PIECEWISE
            else:
                msg += "; setting cudagraph_mode=FULL_DECODE_ONLY"
                cudagraph_mode = CUDAGraphMode.FULL_DECODE_ONLY
            logger.warning(msg)

        # check that if we are doing decode full-cudagraphs it is supported
        if (
            cudagraph_mode.decode_mode() == CUDAGraphMode.FULL
            and min_cg_support == AttentionCGSupport.NEVER
        ):
            msg = (
                f"CUDAGraphMode.{cudagraph_mode.name} is not supported "
                f"with {min_cg_attn_backend} backend (support: "
                f"{min_cg_support})"
            )
            if self.mode == CompilationMode.VLLM_COMPILE and (
                self.splitting_ops_contain_attention()
                or self.use_inductor_graph_partition
            ):
                msg += (
                    "; setting cudagraph_mode=PIECEWISE because "
                    "attention is compiled piecewise"
                )
                cudagraph_mode = CUDAGraphMode.PIECEWISE
            else:
                msg += (
                    "; setting cudagraph_mode=NONE because "
                    "attention is not compiled piecewise"
                )
                cudagraph_mode = CUDAGraphMode.NONE
            logger.warning(msg)

        # check that if we are doing spec-decode + decode full-cudagraphs it is
        # supported
        if (
            cudagraph_mode.decode_mode() == CUDAGraphMode.FULL
            and uniform_decode_query_len > 1
            and min_cg_support.value < AttentionCGSupport.UNIFORM_BATCH.value
        ):
            msg = (
                f"CUDAGraphMode.{cudagraph_mode.name} is not supported"
                f" with spec-decode for attention backend "
                f"{min_cg_attn_backend} (support: {min_cg_support})"
            )
            if self.splitting_ops_contain_attention():
                msg += "; setting cudagraph_mode=PIECEWISE"
                cudagraph_mode = CUDAGraphMode.PIECEWISE
            else:
                msg += "; setting cudagraph_mode=NONE"
                cudagraph_mode = CUDAGraphMode.NONE
            logger.warning(msg)

        # double check that we can support full cudagraph if they are requested
        # even after automatic downgrades
        if (
            cudagraph_mode.has_full_cudagraphs()
            and min_cg_support == AttentionCGSupport.NEVER
        ):
            raise ValueError(
                f"CUDAGraphMode.{cudagraph_mode.name} is not "
                f"supported with {min_cg_attn_backend} backend ("
                f"support:{min_cg_support}) "
                "; please try cudagraph_mode=PIECEWISE, "
                "and make sure compilation mode is VLLM_COMPILE"
            )

        # Adjust cudagraph sizes to be a multiple of uniform_decode_query_len
        # to avoid: https://github.com/vllm-project/vllm/issues/28207 and temp-fix:
        # https://github.com/vllm-project/vllm/issues/28207#issuecomment-3504004536
        # Will be removed in the near future when we have separate cudagraph capture
        # sizes for decode and mixed prefill-decode.
        if (
            cudagraph_mode.decode_mode() == CUDAGraphMode.FULL
            and uniform_decode_query_len > 1
        ):
            self.adjust_cudagraph_sizes_for_spec_decode(
                uniform_decode_query_len,
                tensor_parallel_size,
            )

        # For Mamba models with FULL decode cudagraphs, each decode
        # sequence needs one Mamba cache block. The decode cudagraph
        # dispatcher already caps batch sizes at max_num_seqs, so we just
        # need to verify that enough blocks exist. Raising here instead
        # of silently capping cudagraph_capture_sizes avoids unintended
        # restrictions on PIECEWISE (prefill) cudagraphs.
        # See: https://github.com/vllm-project/vllm/issues/34094
        if (
            kv_cache_config is not None
            and max_num_reqs is not None
            and cudagraph_mode.has_full_cudagraphs()
            and not is_profiling
            and kv_cache_config.has_mamba_layers
            and max_num_reqs > kv_cache_config.num_blocks
        ):
            raise ValueError(
                f"max_num_seqs ({max_num_reqs}) exceeds available Mamba cache "
                f"blocks ({kv_cache_config.num_blocks}). Each decode sequence "
                "requires one Mamba cache block, so CUDA graph capture cannot "
                "proceed. Please lower max_num_seqs to at most "
                f"{kv_cache_config.num_blocks} or increase "
                "gpu_memory_utilization."
            )

        self.cudagraph_mode = cudagraph_mode
        return cudagraph_mode