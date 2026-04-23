def __post_init__(self):
        """Verify configs are valid & consistent with each other."""

        # To give each torch profile run a unique instance name.
        self.instance_id = f"{time.time_ns()}"

        if self.performance_mode != "balanced":
            logger.info_once("Performance mode set to '%s'.", self.performance_mode)

        self.try_verify_and_update_config()

        if self.model_config is not None:
            self.model_config.verify_with_parallel_config(self.parallel_config)
            self.model_config.verify_dual_chunk_attention_config(self.load_config)

            self.parallel_config.is_moe_model = self.model_config.is_moe

        if self.lora_config is not None:
            self.lora_config.verify_with_model_config(self.model_config)

        if (
            self.mamba_config.enable_stochastic_rounding
            and self.cache_config.mamba_ssm_cache_dtype != "float16"
        ):
            raise ValueError(
                "Stochastic rounding for Mamba cache requires "
                "the SSM cache to be float16. Please set it explicitly, "
                "by specifying `--mamba-ssm-cache-dtype float16`, or disable "
                "stochastic rounding by not specifying "
                "`--enable-mamba-cache-stochastic-rounding`."
            )

        if self.quant_config is None and self.model_config is not None:
            self.quant_config = VllmConfig._get_quantization_config(
                self.model_config, self.load_config
            )

        if (
            self.quant_config is not None
            and self.model_config is not None
            and hasattr(self.quant_config, "use_deep_gemm")
            and self.quant_config.use_deep_gemm is None
        ):
            from vllm.utils.deep_gemm import should_auto_disable_deep_gemm

            model_type = getattr(self.model_config.hf_text_config, "model_type", None)
            if should_auto_disable_deep_gemm(model_type):
                self.quant_config.use_deep_gemm = False
                logger.warning_once(
                    "Auto-disabled DeepGemm for model_type=%s on Blackwell. "
                    "DeepGemm E8M0 scale format causes accuracy degradation "
                    "for this architecture. Falling back to CUTLASS. "
                    "To disable DeepGemm globally, set VLLM_USE_DEEP_GEMM=0.",
                    model_type,
                )

        from vllm.v1.executor.abstract import Executor

        executor_backend = self.parallel_config.distributed_executor_backend
        executor_class = Executor.get_class(self)
        executor_supports_async_sched = executor_class.supports_async_scheduling()

        if self.scheduler_config.async_scheduling:
            # Async scheduling explicitly enabled, hard fail any incompatibilities.
            # Currently, async scheduling only support eagle speculative
            # decoding.
            if self.speculative_config is not None:
                if (
                    self.speculative_config.method not in get_args(EagleModelTypes)
                    and self.speculative_config.method not in get_args(NgramGPUTypes)
                    and self.speculative_config.method != "draft_model"
                ):
                    raise ValueError(
                        "Currently, async scheduling is only supported "
                        "with EAGLE/MTP/Draft Model/NGram GPU kind of "
                        "speculative decoding"
                    )
                if self.speculative_config.disable_padded_drafter_batch:
                    raise ValueError(
                        "Async scheduling is not compatible with "
                        "disable_padded_drafter_batch=True."
                    )
            if not executor_supports_async_sched:
                raise ValueError(
                    f"`{executor_backend}` does not support async scheduling yet."
                )
        elif self.scheduler_config.async_scheduling is None:
            # Enable async scheduling unless there is an incompatible option.
            if (
                self.model_config is not None
                and self.model_config.runner_type == "pooling"
            ):
                # The current implementation of asynchronous scheduling negatively
                # impacts performance of pooling models, so we disable by default.
                logger.debug(
                    "Disabling asynchronous scheduling by default for pooling model."
                )
                self.scheduler_config.async_scheduling = False
            elif (
                self.speculative_config is not None
                and self.speculative_config.method not in get_args(EagleModelTypes)
                and self.speculative_config.method not in get_args(NgramGPUTypes)
            ):
                logger.warning_once(
                    "Async scheduling not supported with %s-based "
                    "speculative decoding and will be disabled.",
                    self.speculative_config.method,
                )
                self.scheduler_config.async_scheduling = False
            elif (
                self.speculative_config is not None
                and self.speculative_config.disable_padded_drafter_batch
            ):
                logger.warning_once(
                    "Async scheduling is not compatible with "
                    "disable_padded_drafter_batch=True and will be disabled.",
                )
                self.scheduler_config.async_scheduling = False
            elif not executor_supports_async_sched:
                logger.warning_once(
                    "Async scheduling will be disabled because it is not supported "
                    "with the `%s` distributed executor backend. ",
                    executor_backend,
                )
                self.scheduler_config.async_scheduling = False
            else:
                self.scheduler_config.async_scheduling = True

        logger.info_once(
            "Asynchronous scheduling is %s.",
            "enabled" if self.scheduler_config.async_scheduling else "disabled",
        )

        if self.parallel_config.disable_nccl_for_dp_synchronization is None:
            if self.scheduler_config.async_scheduling:
                if self.parallel_config.data_parallel_size > 1 and (
                    self.model_config is None or self.model_config.is_moe
                ):
                    logger.info_once(
                        "Disabling NCCL for DP synchronization "
                        "when using async scheduling.",
                    )
                self.parallel_config.disable_nccl_for_dp_synchronization = True
            else:
                self.parallel_config.disable_nccl_for_dp_synchronization = False

        if (
            self.speculative_config is not None
            and self.scheduler_config.async_scheduling
            and self.model_config is not None
            and not self.model_config.disable_cascade_attn
        ):
            logger.warning_once(
                "Disabling cascade attention (not yet compatible with "
                "async speculative decoding).",
            )
            self.model_config.disable_cascade_attn = True

        if (
            self.model_config is not None
            and self.model_config.multimodal_config is not None
            and self.model_config.multimodal_config.mm_tensor_ipc == "torch_shm"
            and os.environ.get("VLLM_WORKER_MULTIPROC_METHOD") != "spawn"
        ):
            raise ValueError(
                "torch_shm is known to fail without "
                "VLLM_WORKER_MULTIPROC_METHOD set to spawn"
            )

        from vllm.platforms import current_platform

        if (
            self.model_config is not None
            and self.scheduler_config.enable_chunked_prefill
            and self.model_config.dtype == torch.float32
            and current_platform.get_device_capability() == (7, 5)
        ):
            logger.warning_once(
                "Turing devices tensor cores do not support float32 matmul. "
                "To workaround this limitation, vLLM will set 'ieee' input "
                "precision for chunked prefill triton kernels."
            )

        if self.model_config is not None and self.model_config.enforce_eager:
            logger.warning(
                "Enforce eager set, disabling torch.compile and CUDAGraphs. "
                "This is equivalent to setting -cc.mode=none -cc.cudagraph_mode=none"
            )
            self.compilation_config.mode = CompilationMode.NONE
            self.compilation_config.cudagraph_mode = CUDAGraphMode.NONE

        if self.compilation_config.backend == "eager" or (
            self.compilation_config.mode is not None
            and self.compilation_config.mode != CompilationMode.VLLM_COMPILE
        ):
            logger.warning(
                "Inductor compilation was disabled by user settings, "
                "optimizations settings that are only active during "
                "inductor compilation will be ignored."
            )

        def has_blocked_weights():
            if self.quant_config is not None:
                if hasattr(self.quant_config, "weight_block_size"):
                    return self.quant_config.weight_block_size is not None
                elif hasattr(self.quant_config, "has_blocked_weights"):
                    return self.quant_config.has_blocked_weights()
            return False

        # Enable quant_fp8 CUDA ops (TODO disable in follow up)
        # On H100 the CUDA kernel is faster than
        # native implementation
        # https://github.com/vllm-project/vllm/issues/25094
        if has_blocked_weights():
            custom_ops = self.compilation_config.custom_ops
            if "-quant_fp8" not in custom_ops:
                custom_ops.append("+quant_fp8")

        current_platform.apply_config_platform_defaults(self)

        if self.compilation_config.mode is None:
            if self.optimization_level > OptimizationLevel.O0:
                self.compilation_config.mode = CompilationMode.VLLM_COMPILE
            else:
                self.compilation_config.mode = CompilationMode.NONE

        # By default, enable torch wrapping only when using custom Inductor lowering
        if self.compilation_config.ir_enable_torch_wrap is None:
            self.compilation_config.ir_enable_torch_wrap = (
                self.compilation_config.mode == CompilationMode.VLLM_COMPILE
                and self.compilation_config.backend == "inductor"
            )

        if all(s not in self.compilation_config.custom_ops for s in ("all", "none")):
            if (
                self.compilation_config.backend == "inductor"
                and self.compilation_config.mode != CompilationMode.NONE
            ):
                self.compilation_config.custom_ops.append("none")
            else:
                self.compilation_config.custom_ops.append("all")

        # This populates IR op priorities,
        # must happen after compilation mode and backend are decided,
        # but before fusion defaults are applied as those may depend on op priority.
        self.kernel_config.set_platform_defaults(self)

        default_config = OPTIMIZATION_LEVEL_TO_CONFIG[self.optimization_level]
        self._apply_optimization_level_defaults(default_config)
        if self.kernel_config.enable_flashinfer_autotune is None:
            raise ValueError(
                "KernelConfig.enable_flashinfer_autotune must be set after applying "
                "optimization level defaults."
            )

        if (
            self.compilation_config.cudagraph_mode.requires_piecewise_compilation()
            and self.compilation_config.mode != CompilationMode.VLLM_COMPILE
        ):
            logger.info(
                "Cudagraph mode %s is not compatible with compilation mode %s."
                "Overriding to NONE.",
                self.compilation_config.cudagraph_mode,
                self.compilation_config.mode,
            )
            self.compilation_config.cudagraph_mode = CUDAGraphMode.NONE

        # async tp is built on top of sequence parallelism
        # and requires it to be enabled.
        if self.compilation_config.pass_config.fuse_gemm_comms:
            self.compilation_config.pass_config.enable_sp = True
        if self.compilation_config.pass_config.enable_sp:
            if self.parallel_config.tensor_parallel_size == 1:
                logger.warning("Sequence Parallelism requires TP>1, disabling")
                self.compilation_config.pass_config.enable_sp = False
                self.compilation_config.pass_config.fuse_gemm_comms = False
            else:
                # Compute SP threshold early; disable if None (model too
                # small for SP to be beneficial).
                pass_config = self.compilation_config.pass_config
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

                if pass_config.sp_min_token_num is None:
                    logger.warning(
                        "Model hidden_size too small for the SP "
                        "threshold heuristic, disabling. To force SP, "
                        "set pass_config.sp_min_token_num manually."
                    )
                    self.compilation_config.pass_config.enable_sp = False
                    self.compilation_config.pass_config.fuse_gemm_comms = False

        from vllm.utils.torch_utils import HAS_OPAQUE_TYPE

        if HAS_OPAQUE_TYPE:
            # On torch >= 2.11 the hoisted OpaqueObject approach supersedes
            # fast_moe_cold_start, so force it off.
            self.compilation_config.fast_moe_cold_start = False
        elif self.compilation_config.fast_moe_cold_start is None:
            # resolve default behavior: try to be as safe as possible
            # this config is unsafe if any spec decoding draft model has a MOE.
            # We'll conservatively turn it off if we see spec decoding.
            self.compilation_config.fast_moe_cold_start = (
                self.speculative_config is None
            )

        self._set_max_num_scheduled_tokens()

        if current_platform.support_static_graph_mode():
            # if cudagraph_mode has full cudagraphs, we need to check support
            if model_config := self.model_config:
                if (
                    self.compilation_config.cudagraph_mode.has_full_cudagraphs()
                    and model_config.pooler_config is not None
                ):
                    logger.warning_once(
                        "Pooling models do not support full cudagraphs. "
                        "Overriding cudagraph_mode to PIECEWISE."
                    )
                    self.compilation_config.cudagraph_mode = CUDAGraphMode.PIECEWISE
                elif (
                    model_config.is_encoder_decoder
                    and self.compilation_config.cudagraph_mode
                    not in (CUDAGraphMode.NONE, CUDAGraphMode.FULL_DECODE_ONLY)
                ):
                    logger.info_once(
                        "Encoder-decoder models do not support %s. "
                        "Overriding cudagraph_mode to FULL_DECODE_ONLY.",
                        self.compilation_config.cudagraph_mode.name,
                    )
                    self.compilation_config.cudagraph_mode = (
                        CUDAGraphMode.FULL_DECODE_ONLY
                    )

            # Check if KV connector requires PIECEWISE mode for CUDA graphs
            if (
                self.kv_transfer_config is not None
                and self.kv_transfer_config.is_kv_transfer_instance
                and self.compilation_config.cudagraph_mode.has_full_cudagraphs()
            ):
                # Lazy import to avoid circular dependencies
                from vllm.distributed.kv_transfer.kv_connector.factory import (
                    KVConnectorFactory,
                )

                connector_cls = KVConnectorFactory.get_connector_class(
                    self.kv_transfer_config
                )
                if connector_cls.requires_piecewise_for_cudagraph(
                    self.kv_transfer_config.kv_connector_extra_config
                ):
                    logger.warning_once(
                        "KV connector %s requires PIECEWISE CUDA graph mode "
                        "due to layerwise async operations that cannot be "
                        "captured in CUDA graphs. "
                        "Overriding cudagraph_mode from %s to PIECEWISE.",
                        connector_cls.__name__,
                        self.compilation_config.cudagraph_mode.name,
                    )
                    self.compilation_config.cudagraph_mode = CUDAGraphMode.PIECEWISE

            # disable cudagraph when enforce eager execution
            if self.model_config is not None and self.model_config.enforce_eager:
                logger.info("Cudagraph is disabled under eager mode")
                self.compilation_config.cudagraph_mode = CUDAGraphMode.NONE
                # override related settings when enforce eager
                self.compilation_config.max_cudagraph_capture_size = 0
                self.compilation_config.cudagraph_capture_sizes = []
            else:
                self.compilation_config.cudagraph_num_of_warmups = 1

            self._set_cudagraph_sizes()
        else:
            self.compilation_config.cudagraph_mode = CUDAGraphMode.NONE

        if self.cache_config.kv_sharing_fast_prefill:
            if (
                self.speculative_config is not None
                and self.speculative_config.use_eagle()
            ):
                raise ValueError(
                    "Fast prefill optimization for KV sharing is not "
                    "compatible with EAGLE as EAGLE requires correct logits "
                    "for all tokens while fast prefill gives incorrect logits "
                    "for prompt tokens."
                )

            logger.warning_once(
                "--kv-sharing-fast-prefill requires changes on model side for "
                "correctness and to realize prefill savings."
            )

        if (
            self.model_config
            and self.model_config.architecture == "WhisperForConditionalGeneration"
            and os.environ.get("VLLM_WORKER_MULTIPROC_METHOD") != "spawn"
        ):
            logger.warning(
                "Whisper is known to have issues with "
                "forked workers. If startup is hanging, "
                "try setting 'VLLM_WORKER_MULTIPROC_METHOD' "
                "to 'spawn'."
            )

        if (
            self.kv_events_config is not None
            and self.kv_events_config.enable_kv_cache_events
            and not self.cache_config.enable_prefix_caching
        ):
            logger.warning(
                "KV cache events are on, but prefix caching is not enabled. "
                "Use --enable-prefix-caching to enable."
            )
        if (
            self.kv_events_config is not None
            and self.kv_events_config.publisher != "null"
            and not self.kv_events_config.enable_kv_cache_events
        ):
            logger.warning(
                "KV cache events are disabled, "
                "but the scheduler is configured to publish them. "
                "Modify KVEventsConfig.enable_kv_cache_events "
                "to True to enable."
            )
        current_platform.check_and_update_config(self)

        if envs.VLLM_USE_V2_MODEL_RUNNER:
            self._validate_v2_model_runner()

        # Re-compute compile ranges after platform-specific config updates
        # (e.g., XPU may lower max_num_batched_tokens when MLA is enabled)
        self._set_compile_ranges()

        # Do this after all the updates to compilation_config.mode
        effective_dp_size = (
            self.parallel_config.data_parallel_size
            if self.model_config is None or self.model_config.is_moe
            else 1
        )
        self.compilation_config.set_splitting_ops_for_v1(
            all2all_backend=self.parallel_config.all2all_backend,
            data_parallel_size=effective_dp_size,
        )

        if self.compilation_config.pass_config.enable_sp:
            # With pipeline parallelism or dynamo partitioning,
            # native rms norm tracing errors due to incorrect residual shape.
            # Use custom rms norm to unblock. In the future,
            # the pass will operate on higher-level IR to avoid the issue.
            # TODO: https://github.com/vllm-project/vllm/issues/27894
            if self.compilation_config.mode != CompilationMode.VLLM_COMPILE:
                logger.warning(
                    "Sequence parallelism is enabled, but running in wrong "
                    "vllm compile mode: %s.",
                    self.compilation_config.mode,
                )

            is_fullgraph = (
                self.compilation_config.use_inductor_graph_partition
                or len(self.compilation_config.splitting_ops or []) == 0
            )
            if self.parallel_config.pipeline_parallel_size > 1 or not is_fullgraph:
                if "-rms_norm" not in self.compilation_config.custom_ops:
                    self.compilation_config.custom_ops.append("+rms_norm")
                else:
                    regime = (
                        "Dynamo partition"
                        if not is_fullgraph
                        else "pipeline parallelism"
                    )
                    logger.warning_once(
                        "Sequence parallelism not supported with "
                        "native rms_norm when using %s, "
                        "this will likely lead to an error.",
                        regime,
                    )

        # final check of cudagraph mode after all possible updates
        if current_platform.is_cuda_alike():
            if (
                self.compilation_config.cudagraph_mode.has_full_cudagraphs()
                and self.model_config is not None
                and not self.model_config.disable_cascade_attn
                and not self.compilation_config.cudagraph_mode.has_piecewise_cudagraphs()  # noqa: E501
            ):
                logger.warning_once(
                    "No piecewise cudagraph for executing cascade attention."
                    " Will fall back to eager execution if a batch runs "
                    "into cascade attentions."
                )

            if self.compilation_config.cudagraph_mode.requires_piecewise_compilation():
                assert self.compilation_config.mode == CompilationMode.VLLM_COMPILE, (
                    "Compilation mode should be CompilationMode.VLLM_COMPILE "
                    "when cudagraph_mode piecewise cudagraphs is used, "
                    f"cudagraph_mode={self.compilation_config.cudagraph_mode}"
                )
        if (
            self.model_config
            and envs.VLLM_BATCH_INVARIANT
            and not self.model_config.disable_cascade_attn
        ):
            self.model_config.disable_cascade_attn = True
            logger.warning_once(
                "Disabling cascade attention when VLLM_BATCH_INVARIANT is enabled.",
            )

        if self.parallel_config.use_ubatching:
            a2a_backend = self.parallel_config.all2all_backend
            assert a2a_backend in [
                "deepep_low_latency",
                "deepep_high_throughput",
            ], (
                "Microbatching currently only supports the deepep_low_latency and "
                f"deepep_high_throughput all2all backend. {a2a_backend} is not "
                "supported. To fix use --all2all-backend=deepep_low_latency or "
                "--all2all-backend=deepep_high_throughput and install the DeepEP"
                " kernels."
            )

            if not self.model_config.disable_cascade_attn:
                self.model_config.disable_cascade_attn = True
                logger.warning_once("Disabling cascade attention when DBO is enabled.")

        if not self.instance_id:
            self.instance_id = random_uuid()[:5]

        if self.reasoning_config is not None and self.model_config is not None:
            self.reasoning_config.initialize_token_ids(self.model_config)
            if not self.reasoning_config.enabled:
                logger.warning_once(
                    "Auto-initialization of reasoning token IDs failed. "
                    "Please check whether your reasoning parser has implemented "
                    "the `reasoning_start_str` and `reasoning_end_str`."
                )

        # Hybrid KV cache manager (HMA) runtime rules:
        # - Explicit enable (--no-disable-kv-cache-manager): error if runtime
        #   disables it
        # - No preference: auto-disable for unsupported features (e.g. kv connector)
        # - Explicit disable (--disable-kv-cache-manager): always respect it
        need_disable_hybrid_kv_cache_manager = False
        # logger should only print warning message for hybrid models. As we
        # can't know whether the model is hybrid or not now, so we don't log
        # warning message here and will log it later.
        if not current_platform.support_hybrid_kv_cache():
            # Hybrid KV cache manager is not supported on non-GPU platforms.
            need_disable_hybrid_kv_cache_manager = True
        if (
            self.model_config is not None
            and self.model_config.attention_chunk_size is not None
        ):
            if (
                self.speculative_config is not None
                and self.speculative_config.use_eagle()
            ):
                # Hybrid KV cache manager is not yet supported with chunked
                # local attention + eagle.
                need_disable_hybrid_kv_cache_manager = True
            elif not envs.VLLM_ALLOW_CHUNKED_LOCAL_ATTN_WITH_HYBRID_KV_CACHE:
                logger.warning(
                    "There is a latency regression when using chunked local"
                    " attention with the hybrid KV cache manager. Disabling"
                    " it, by default. To enable it, set the environment "
                    "VLLM_ALLOW_CHUNKED_LOCAL_ATTN_WITH_HYBRID_KV_CACHE=1."
                )
                # Hybrid KV cache manager is not yet supported with chunked
                # local attention.
                need_disable_hybrid_kv_cache_manager = True

        if self.scheduler_config.disable_hybrid_kv_cache_manager is None:
            # Default to disable HMA, but only if the user didn't express a preference.
            if self.kv_transfer_config is not None:
                # NOTE(Kuntai): turn HMA off for connector unless specifically enabled.
                need_disable_hybrid_kv_cache_manager = True
                logger.warning(
                    "Turning off hybrid kv cache manager because "
                    "`--kv-transfer-config` is set. This will reduce the "
                    "performance of vLLM on LLMs with sliding window attention "
                    "or Mamba attention. If you are a developer of kv connector"
                    ", please consider supporting hybrid kv cache manager for "
                    "your connector by making sure your connector is a subclass"
                    " of `SupportsHMA` defined in kv_connector/v1/base.py and"
                    " use --no-disable-hybrid-kv-cache-manager to start vLLM."
                )
            self.scheduler_config.disable_hybrid_kv_cache_manager = (
                need_disable_hybrid_kv_cache_manager
            )
        elif (
            self.scheduler_config.disable_hybrid_kv_cache_manager is False
            and need_disable_hybrid_kv_cache_manager
        ):
            raise ValueError(
                "Hybrid KV cache manager was explicitly enabled but is not "
                "supported in this configuration. Consider omitting the "
                "--no-disable-hybrid-kv-cache-manager flag to let vLLM decide"
                " automatically."
            )

        if self.scheduler_config.disable_hybrid_kv_cache_manager is None:
            # Default to enable HMA if not explicitly disabled by user or logic above.
            self.scheduler_config.disable_hybrid_kv_cache_manager = False

        if self.compilation_config.debug_dump_path:
            self.compilation_config.debug_dump_path = (
                self.compilation_config.debug_dump_path.absolute().expanduser()
            )
        if envs.VLLM_DEBUG_DUMP_PATH is not None:
            env_path = Path(envs.VLLM_DEBUG_DUMP_PATH).absolute().expanduser()
            if self.compilation_config.debug_dump_path:
                logger.warning(
                    "Config-specified debug dump path is overridden"
                    " by VLLM_DEBUG_DUMP_PATH to %s",
                    env_path,
                )
            self.compilation_config.debug_dump_path = env_path

        # Enable quant_fp8 CUDA ops (TODO disable in follow up)
        # On H100 the CUDA kernel is faster than
        # native implementation
        # https://github.com/vllm-project/vllm/issues/25094
        if has_blocked_weights():
            custom_ops = self.compilation_config.custom_ops
            if "-quant_fp8" not in custom_ops:
                custom_ops.append("+quant_fp8")

        # Handle the KV connector configs
        self._post_init_kv_transfer_config()

        # Log the custom passes that are enabled
        self.compilation_config.pass_config.log_enabled_passes()