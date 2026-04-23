def __init__(
        self,
        model: str,
        *,
        runner: RunnerOption = "auto",
        convert: ConvertOption = "auto",
        tokenizer: str | None = None,
        tokenizer_mode: TokenizerMode | str = "auto",
        skip_tokenizer_init: bool = False,
        trust_remote_code: bool = False,
        allowed_local_media_path: str = "",
        allowed_media_domains: list[str] | None = None,
        tensor_parallel_size: int = 1,
        dtype: ModelDType = "auto",
        quantization: QuantizationMethods | None = None,
        revision: str | None = None,
        tokenizer_revision: str | None = None,
        chat_template: Path | str | None = None,
        seed: int = 0,
        gpu_memory_utilization: float = 0.92,
        cpu_offload_gb: float = 0,
        offload_group_size: int = 0,
        offload_num_in_group: int = 1,
        offload_prefetch_step: int = 1,
        offload_params: set[str] | None = None,
        enforce_eager: bool = False,
        enable_return_routed_experts: bool = False,
        disable_custom_all_reduce: bool = False,
        hf_token: bool | str | None = None,
        hf_overrides: HfOverrides | None = None,
        mm_processor_kwargs: dict[str, Any] | None = None,
        pooler_config: PoolerConfig | None = None,
        structured_outputs_config: dict[str, Any]
        | StructuredOutputsConfig
        | None = None,
        profiler_config: dict[str, Any] | ProfilerConfig | None = None,
        attention_config: dict[str, Any] | AttentionConfig | None = None,
        kv_cache_memory_bytes: int | None = None,
        compilation_config: int | dict[str, Any] | CompilationConfig | None = None,
        quantization_config: dict[str, Any]
        | OnlineQuantizationConfigArgs
        | None = None,
        logits_processors: list[str | type[LogitsProcessor]] | None = None,
        **kwargs: Any,
    ) -> None:
        """LLM constructor."""

        if "swap_space" in kwargs:
            kwargs.pop("swap_space")
            import warnings

            warnings.warn(
                "The 'swap_space' parameter is deprecated and ignored. "
                "It will be removed in a future version.",
                DeprecationWarning,
                stacklevel=2,
            )

        if "disable_log_stats" not in kwargs:
            kwargs["disable_log_stats"] = True

        if "worker_cls" in kwargs:
            worker_cls = kwargs["worker_cls"]
            # if the worker_cls is not qualified string name,
            # we serialize it using cloudpickle to avoid pickling issues
            if isinstance(worker_cls, type):
                kwargs["worker_cls"] = cloudpickle.dumps(worker_cls)

        if "kv_transfer_config" in kwargs and isinstance(
            kwargs["kv_transfer_config"], dict
        ):
            from vllm.config.kv_transfer import KVTransferConfig

            raw_config_dict = kwargs["kv_transfer_config"]
            try:
                kwargs["kv_transfer_config"] = KVTransferConfig(**raw_config_dict)
            except ValidationError as e:
                logger.error(
                    "Failed to convert 'kv_transfer_config' dict to "
                    "KVTransferConfig object. Dict: %s. Error: %s",
                    raw_config_dict,
                    e,
                )
                # Consider re-raising a more specific vLLM error or ValueError
                # to provide better context to the user.
                raise ValueError(f"Invalid 'kv_transfer_config' provided: {e}") from e

        if hf_overrides is None:
            hf_overrides = {}

        def _make_config(value: Any, cls: type[_R]) -> _R:
            """Convert dict/None/instance to a config instance."""
            if value is None:
                return cls()
            if isinstance(value, dict):
                return cls(**{k: v for k, v in value.items() if is_init_field(cls, k)})  # type: ignore[arg-type]
            return value

        if isinstance(compilation_config, int):
            compilation_config_instance = CompilationConfig(
                mode=CompilationMode(compilation_config)
            )
        else:
            compilation_config_instance = _make_config(
                compilation_config, CompilationConfig
            )

        structured_outputs_instance = _make_config(
            structured_outputs_config, StructuredOutputsConfig
        )
        profiler_config_instance = _make_config(profiler_config, ProfilerConfig)
        attention_config_instance = _make_config(attention_config, AttentionConfig)

        # warn about single-process data parallel usage.
        _dp_size = int(kwargs.get("data_parallel_size", 1))
        _distributed_executor_backend = kwargs.get("distributed_executor_backend")
        if (
            _dp_size > 1
            and not _distributed_executor_backend == "external_launcher"
            and not current_platform.is_tpu()
        ):
            raise ValueError(
                f"LLM(data_parallel_size={_dp_size}) is not supported for single-"
                "process usage and may hang. Please use "
                "the explicit multi-process data-parallel example at "
                "'examples/offline_inference/data_parallel.py'."
            )

        engine_args = EngineArgs(
            model=model,
            runner=runner,
            convert=convert,
            tokenizer=tokenizer,
            tokenizer_mode=tokenizer_mode,
            skip_tokenizer_init=skip_tokenizer_init,
            trust_remote_code=trust_remote_code,
            allowed_local_media_path=allowed_local_media_path,
            allowed_media_domains=allowed_media_domains,
            tensor_parallel_size=tensor_parallel_size,
            dtype=dtype,
            quantization=quantization,
            revision=revision,
            tokenizer_revision=tokenizer_revision,
            seed=seed,
            gpu_memory_utilization=gpu_memory_utilization,
            kv_cache_memory_bytes=kv_cache_memory_bytes,
            cpu_offload_gb=cpu_offload_gb,
            offload_group_size=offload_group_size,
            offload_num_in_group=offload_num_in_group,
            offload_prefetch_step=offload_prefetch_step,
            offload_params=offload_params or set(),
            enforce_eager=enforce_eager,
            enable_return_routed_experts=enable_return_routed_experts,
            disable_custom_all_reduce=disable_custom_all_reduce,
            hf_token=hf_token,
            hf_overrides=hf_overrides,
            mm_processor_kwargs=mm_processor_kwargs,
            pooler_config=pooler_config,
            structured_outputs_config=structured_outputs_instance,
            profiler_config=profiler_config_instance,
            attention_config=attention_config_instance,
            compilation_config=compilation_config_instance,
            quantization_config=quantization_config,
            logits_processors=logits_processors,
            **kwargs,
        )

        log_non_default_args(engine_args)

        self.llm_engine = LLMEngine.from_engine_args(
            engine_args=engine_args, usage_context=UsageContext.LLM_CLASS
        )
        self.model_config = self.llm_engine.model_config
        self.engine_class = type(self.llm_engine)

        self.request_counter = Counter()
        self.default_sampling_params: dict[str, Any] | None = None

        supported_tasks = self.llm_engine.get_supported_tasks()
        self.supported_tasks = supported_tasks
        self.pooling_task = self.model_config.get_pooling_task(supported_tasks)
        if self.pooling_task is not None:
            logger.info("Supported pooling task: %s", self.pooling_task)

        self.runner_type = self.model_config.runner_type
        self.renderer = self.llm_engine.renderer
        self.chat_template = load_chat_template(chat_template)
        self.input_processor = self.llm_engine.input_processor
        self.chat_template_config = ChatTemplateConfig(chat_template=self.chat_template)
        self.pooling_io_processors = init_pooling_io_processors(
            supported_tasks=supported_tasks,
            vllm_config=self.llm_engine.vllm_config,
            renderer=self.renderer,
            chat_template_config=self.chat_template_config,
        )
        # Cache for __repr__ to avoid repeated collective_rpc calls
        self._cached_repr: str | None = None