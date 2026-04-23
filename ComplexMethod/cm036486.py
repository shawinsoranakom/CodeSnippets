def can_initialize(
    model_arch: str, monkeypatch: pytest.MonkeyPatch, EXAMPLE_MODELS: HfExampleModels
):
    """The reason for using create_new_process_for_each_test is to avoid
    the WARNING:
        "We must use the 'spawn' multiprocessing start method. Overriding
        VLLM_WORKER_MULTIPROC_METHOD to 'spawn'."
    The spawn process causes the _initialize_kv_caches_v1 function below to
    become ineffective.
    """

    model_info = EXAMPLE_MODELS.get_hf_info(model_arch)
    model_info.check_available_online(on_fail="skip")
    model_info.check_transformers_version(
        on_fail="skip",
        check_max_version=False,
        check_version_reason="vllm",
    )

    hf_overrides_fn = partial(
        dummy_hf_overrides,
        model_arch=model_arch,
        exist_overrides=model_info.hf_overrides,
        use_original_num_layers=getattr(model_info, "use_original_num_layers", False),
    )

    # Avoid calling model.forward()
    def _initialize_kv_caches_v1(self, vllm_config):
        kv_cache_specs = self.model_executor.get_kv_cache_specs()
        kv_cache_configs = get_kv_cache_configs(
            vllm_config,
            kv_cache_specs,
            [10 * GiB_bytes],
        )
        scheduler_kv_cache_config = generate_scheduler_kv_cache_config(kv_cache_configs)
        vllm_config.cache_config.num_gpu_blocks = scheduler_kv_cache_config.num_blocks
        kv_cache_groups = scheduler_kv_cache_config.kv_cache_groups
        if kv_cache_groups:
            vllm_config.cache_config.block_size = min(
                g.kv_cache_spec.block_size for g in kv_cache_groups
            )

        vllm_config.validate_block_size()
        return scheduler_kv_cache_config

    if model_arch == "MiniMaxVL01ForConditionalGeneration":
        pytest.skip(
            "pickle error when loading `transformers.models.auto.CONFIG_MAPPING`"
        )

    if model_arch == "MoonshotKimiaForCausalLM":
        pytest.skip(
            "Kimi-Audio requires SpeechToTextConfig "
            "which is not configured in test environment"
        )

    if model_arch in ["DeepseekV32ForCausalLM", "GlmMoeDsaForCausalLM"]:
        from vllm.platforms import current_platform

        capability = current_platform.get_device_capability()
        if capability and capability.major < 9:
            pytest.skip(
                f"DeepseekV32 requires Hopper (9.0+) or Blackwell (10.0+) "
                f"for FLASHMLA_SPARSE backend. Current device has compute "
                f"capability {capability.major}.{capability.minor}"
            )

    with (
        patch.object(V1EngineCore, "_initialize_kv_caches", _initialize_kv_caches_v1),
        monkeypatch.context() as m,
    ):
        # FIXME: A hack to bypass FA3 assertion because our CI's L4 GPU
        # has cc==8.9 which hasn't supported FA3 yet. Remove this hack when
        # L4 supports FA3.
        # Step1ForCausalLM requires TRITON_ATTN for use_alibi_sqrt support.
        attention_config = (
            {"backend": "TRITON_ATTN"}
            if model_arch in ("GptOssForCausalLM", "Step1ForCausalLM")
            else None
        )
        if model_arch == "WhisperForConditionalGeneration":
            m.setenv("VLLM_WORKER_MULTIPROC_METHOD", "spawn")

        kwargs = {}
        if not model_info.enable_prefix_caching:
            kwargs["enable_prefix_caching"] = False

        LLM(
            model_info.default,
            tokenizer=model_info.tokenizer,
            tokenizer_mode=model_info.tokenizer_mode,
            revision=model_info.revision,
            enforce_eager=model_info.enforce_eager,
            skip_tokenizer_init=model_info.require_embed_inputs,
            enable_prompt_embeds=model_info.require_embed_inputs,
            enable_mm_embeds=model_info.require_embed_inputs,
            dtype=model_info.dtype,
            speculative_config={
                "model": model_info.speculative_model,
                "method": model_info.speculative_method,
                "num_speculative_tokens": 1,
            }
            if model_info.speculative_model
            else None,
            trust_remote_code=model_info.trust_remote_code,
            max_model_len=model_info.max_model_len,
            max_num_batched_tokens=model_info.max_num_batched_tokens,
            # these tests seem to produce leftover memory
            gpu_memory_utilization=0.80,
            load_format="dummy",
            model_impl="transformers"
            if model_arch in _TRANSFORMERS_BACKEND_MODELS
            else "vllm",
            hf_overrides=hf_overrides_fn,
            max_num_seqs=model_info.max_num_seqs,
            attention_config=attention_config,
            **kwargs,
        )