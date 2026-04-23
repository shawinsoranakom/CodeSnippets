def mteb_test_embed_models(
    hf_runner,
    vllm_runner,
    model_info: EmbedModelInfo,
    vllm_extra_kwargs=None,
    hf_model_callback=None,
    atol=MTEB_EMBED_TOL,
    prompt_prefix: str | None = None,
):
    vllm_extra_kwargs = get_vllm_extra_kwargs(model_info, vllm_extra_kwargs)

    # Test embed_dims, isnan and whether to use normalize
    example_prompts = ["The chef prepared a delicious meal." * 1000]

    with vllm_runner(
        model_info.name,
        revision=model_info.revision,
        runner="pooling",
        max_model_len=model_info.max_model_len,
        **vllm_extra_kwargs,
    ) as vllm_model:
        model_config = vllm_model.llm.llm_engine.model_config

        # Confirm whether vllm is using the correct architecture
        if model_info.architecture:
            assert model_info.architecture in model_config.architectures

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

        vllm_main_score = run_mteb_embed_task(
            VllmMtebEncoder(vllm_model, prompt_prefix=prompt_prefix), MTEB_EMBED_TASKS
        )
        vllm_dtype = vllm_model.llm.llm_engine.model_config.dtype
        head_dtype = model_config.head_dtype

        # Test embedding_size, isnan and whether to use normalize
        vllm_outputs = vllm_model.embed(
            example_prompts,
            tokenization_kwargs=dict(truncate_prompt_tokens=-1),
        )
        outputs_tensor = torch.tensor(vllm_outputs)
        assert not torch.any(torch.isnan(outputs_tensor))
        embedding_size = model_config.embedding_size
        assert torch.tensor(vllm_outputs).shape[-1] == embedding_size

    # Accelerate mteb test by setting
    # SentenceTransformers mteb score to a constant
    if model_info.mteb_score is None:
        with hf_runner(
            model_info.name,
            revision=model_info.revision,
            is_sentence_transformer=True,
            dtype=ci_envs.VLLM_CI_HF_DTYPE or model_info.hf_dtype,
        ) as hf_model:
            # e.g. setting default parameters for the encode method of hf_runner
            if hf_model_callback is not None:
                hf_model_callback(hf_model)

            st_main_score = run_mteb_embed_task(
                HfMtebEncoder(hf_model), MTEB_EMBED_TASKS
            )
            st_dtype = next(hf_model.model.parameters()).dtype

            # Check embeddings close to hf outputs
            hf_outputs = hf_model.encode(example_prompts)
            check_embeddings_close(
                embeddings_0_lst=hf_outputs,
                embeddings_1_lst=vllm_outputs,
                name_0="hf",
                name_1="vllm",
                tol=1e-2,
            )
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