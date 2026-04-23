def mteb_test_rerank_models(
    vllm_runner,
    model_info: RerankModelInfo,
    hf_runner=HFMtebCrossEncoder,
    vllm_extra_kwargs=None,
    vllm_mteb_encoder=VllmMtebCrossEncoder,
    atol=MTEB_RERANK_TOL,
):
    vllm_extra_kwargs = get_vllm_extra_kwargs(model_info, vllm_extra_kwargs)

    # Maybe load chat_template.
    chat_template: str | None = None
    if model_info.chat_template_name is not None:
        chat_template = (template_home / model_info.chat_template_name).read_text()

    with vllm_runner(
        model_info.name,
        revision=model_info.revision,
        runner="pooling",
        max_model_len=None,
        max_num_seqs=8,
        **vllm_extra_kwargs,
    ) as vllm_model:
        model_config = vllm_model.llm.llm_engine.model_config
        vllm_model.chat_template = chat_template

        # Confirm whether vllm is using the correct architecture
        if model_info.architecture:
            assert model_info.architecture in model_config.architectures

        # Score API is only enabled for num_labels == 1
        assert model_config.hf_config.num_labels == 1

        # Confirm whether the important configs in model_config are correct.
        pooler_config = model_config.pooler_config
        if model_info.seq_pooling_type is not None:
            assert pooler_config.seq_pooling_type == model_info.seq_pooling_type
        if model_info.tok_pooling_type is not None:
            assert pooler_config.tok_pooling_type == model_info.tok_pooling_type
        if model_info.attn_type is not None:
            assert model_config.attn_type == model_info.attn_type
        if model_info.is_prefix_caching_supported is not None:
            assert (
                model_config.is_prefix_caching_supported
                == model_info.is_prefix_caching_supported
            )
        if model_info.is_chunked_prefill_supported is not None:
            assert (
                model_config.is_chunked_prefill_supported
                == model_info.is_chunked_prefill_supported
            )

        vllm_main_score = run_mteb_rerank(
            vllm_mteb_encoder(vllm_model),
            tasks=MTEB_RERANK_TASKS,
            languages=MTEB_RERANK_LANGS,
        )
        vllm_dtype = model_config.dtype
        head_dtype = model_config.head_dtype

    # Accelerate mteb test by setting
    # SentenceTransformers mteb score to a constant
    if model_info.mteb_score is None:
        with hf_runner(
            model_info.name, revision=model_info.revision, dtype=model_info.hf_dtype
        ) as hf_model:
            hf_model.chat_template = chat_template
            st_main_score = run_mteb_rerank(
                hf_model,
                tasks=MTEB_RERANK_TASKS,
                languages=MTEB_RERANK_LANGS,
            )
            st_dtype = next(hf_model.model.model.parameters()).dtype
    else:
        st_main_score = model_info.mteb_score
        st_dtype = "Constant"

    print("Model:", model_info.name)
    print("VLLM:", f"dtype:{vllm_dtype}", f"head_dtype:{head_dtype}", vllm_main_score)
    print("SentenceTransformers:", st_dtype, st_main_score)
    print("Difference:", st_main_score - vllm_main_score)

    # We are not concerned that the vllm mteb results are better
    # than SentenceTransformers, so we only perform one-sided testing.
    assert st_main_score - vllm_main_score < atol