def set_splitting_ops_for_v1(
        self, all2all_backend: str, data_parallel_size: int = 1
    ):
        # To compatible with OOT hardware plugin platform (for example vllm-ascend)
        # which currently only supports sequence parallelism in eager mode.
        if self.mode != CompilationMode.VLLM_COMPILE:
            if self.splitting_ops is None:
                self.splitting_ops = []
            return

        if self.pass_config.fuse_attn_quant and not self.use_inductor_graph_partition:
            self.set_splitting_ops_for_attn_fusion()
        else:
            if self.splitting_ops is None:
                # NOTE: When using full cudagraph, instead of setting an empty
                # list and capture the full cudagraph inside the flattened fx
                # graph, we keep the piecewise fx graph structure but capture
                # the full cudagraph outside the fx graph. This reduces some
                # cpu overhead when the runtime batch_size is not cudagraph
                # captured. see https://github.com/vllm-project/vllm/pull/20059
                # for details. Make a copy to avoid mutating the class-level
                # list via reference.
                self.splitting_ops = list(self._attention_ops)

                # unified_kv_cache_update has a string param that prevents Inductor
                # from reusing piecewise graphs. Remove it from the compiled graph.
                # This has the side-effect of excluding cache from cudagraphs but
                # that doesn't seem to affect performance.
                # https://github.com/vllm-project/vllm/issues/33267
                if not self.use_inductor_graph_partition:
                    if self.pass_config.fuse_rope_kvcache:
                        logger.warning_once(
                            "fuse_rope_kvcache is enabled, but splitting_ops is None "
                            "and Inductor graph partition is not enabled."
                            "Disabling fuse_rope_kvcache."
                            "Please either set splitting_ops to an empty list []"
                            "or set use_inductor_graph_partition to True "
                            "to enable RoPE+KV cache fusion."
                        )
                        self.pass_config.fuse_rope_kvcache = False
                    self.splitting_ops.append("vllm::unified_kv_cache_update")
                    self.splitting_ops.append("vllm::unified_mla_kv_cache_update")

            elif len(self.splitting_ops) == 0:
                if (
                    self.cudagraph_mode == CUDAGraphMode.PIECEWISE
                    or self.cudagraph_mode == CUDAGraphMode.FULL_AND_PIECEWISE
                ):
                    logger.warning_once(
                        "Using piecewise cudagraph with empty splitting_ops"
                    )
                if self.cudagraph_mode == CUDAGraphMode.PIECEWISE:
                    logger.warning_once(
                        "Piecewise compilation with empty splitting_ops does not "
                        "contain piecewise cudagraph. Setting cudagraph_"
                        "mode to NONE. Hint: If you are using attention "
                        "backends that support cudagraph, consider manually "
                        "setting cudagraph_mode to FULL or FULL_DECODE_ONLY "
                        "to enable full cudagraphs."
                    )
                    self.cudagraph_mode = CUDAGraphMode.NONE
                elif self.cudagraph_mode == CUDAGraphMode.FULL_AND_PIECEWISE:
                    logger.warning_once(
                        "Piecewise compilation with empty splitting_ops does "
                        "not contain piecewise cudagraph. Setting "
                        "cudagraph_mode to FULL."
                    )
                    self.cudagraph_mode = CUDAGraphMode.FULL
                self.splitting_ops = []

        # Disable CUDA graphs for DeepEP high-throughput since its not CG compatible
        if (
            all2all_backend == "deepep_high_throughput"
            and data_parallel_size > 1
            and self.cudagraph_mode != CUDAGraphMode.NONE
        ):
            # TODO: Piecewise Cuda graph might be enabled
            # if torch compile cache key issue fixed
            # See https://github.com/vllm-project/vllm/pull/25093
            logger.info(
                "DeepEP: Disabling CUDA Graphs since DeepEP high-throughput kernels "
                "are optimized for prefill and are incompatible with CUDA Graphs. "
                "In order to use CUDA Graphs for decode-optimized workloads, "
                "use --all2all-backend with another option, such as "
                "deepep_low_latency or allgather_reducescatter."
            )
            self.cudagraph_mode = CUDAGraphMode.NONE