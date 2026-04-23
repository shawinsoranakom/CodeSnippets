def check_and_update_config(cls, vllm_config: VllmConfig) -> None:
        parallel_config = vllm_config.parallel_config

        # lazy import to avoid circular import
        from vllm.config import CUDAGraphMode

        compilation_config = vllm_config.compilation_config
        if compilation_config.compile_sizes is None:
            compilation_config.compile_sizes = []

        attention_config = vllm_config.attention_config
        if attention_config.backend is None:
            attention_config.backend = AttentionBackendEnum.FLASH_ATTN
        if not supports_xpu_graph():
            compilation_config.cudagraph_mode = CUDAGraphMode.NONE
            logger.warning(
                "XPU Graph is not supported in the current PyTorch version, "
                "disabling cudagraph_mode."
            )
        elif not envs.VLLM_XPU_ENABLE_XPU_GRAPH:
            compilation_config.cudagraph_mode = CUDAGraphMode.NONE
            logger.warning(
                "XPU Graph is disabled by environment variable, "
                "please set VLLM_XPU_ENABLE_XPU_GRAPH=1 to enable it."
            )
        elif parallel_config.world_size_across_dp > 1:
            compilation_config.cudagraph_mode = CUDAGraphMode.NONE
            logger.warning(
                "XPU Graph doesn't support capture communication ops, "
                "disabling cudagraph_mode."
            )
        else:
            if (
                attention_config.backend == AttentionBackendEnum.FLASH_ATTN
                and compilation_config.cudagraph_mode
                not in {CUDAGraphMode.NONE, CUDAGraphMode.PIECEWISE}
            ):
                compilation_config.cudagraph_mode = CUDAGraphMode.PIECEWISE
                logger.warning(
                    "FMHA sycl-tla kernels cannot be captured with XPU graphs, "
                    "falling back to PIECEWISE graph mode on XPU platform."
                )

        # Disable fusion passes not yet supported on XPU.
        pass_config = compilation_config.pass_config
        fusion_passes_to_disable = {
            "enable_sp": "Sequence parallelism",
            "fuse_gemm_comms": "Async TP",
            "fuse_allreduce_rms": "AllReduce + RMSNorm fusion",
            "fuse_norm_quant": "RMSNorm + quant fusion",
            "fuse_act_quant": "Activation + quant fusion",
            "fuse_attn_quant": "Attention + quant fusion",
            "fuse_act_padding": "Activation + padding fusion",
            "fuse_rope_kvcache": "RoPE + KV cache fusion",
        }
        for flag, feature_name in fusion_passes_to_disable.items():
            if getattr(pass_config, flag):
                logger.warning(
                    "Feature %r is not yet supported on XPU and will be disabled.",
                    feature_name,
                )
                setattr(pass_config, flag, False)

        # check and update parallel config
        parallel_config = vllm_config.parallel_config
        # Only override worker_cls if it's still the default "auto"
        # This allows custom workers (like vllm-omni workers) to be used on XPU
        if parallel_config.worker_cls == "auto":
            parallel_config.worker_cls = "vllm.v1.worker.xpu_worker.XPUWorker"
        if vllm_config.kv_transfer_config is not None:
            vllm_config.kv_transfer_config.enable_permute_local_kv = True

        # In some cases, the internal memory type cache can misdetect GPU
        # memory as host memory, also leading to invalid memory access.
        # This cache can be disabled by setting UCX_MEMTYPE_CACHE=n.
        # ref. https://openucx.readthedocs.io/en/master/faq.html
        os.environ["UCX_MEMTYPE_CACHE"] = "n"

        # spawn is the only supported multiprocessing method on XPU
        if "VLLM_WORKER_MULTIPROC_METHOD" not in os.environ:
            os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"