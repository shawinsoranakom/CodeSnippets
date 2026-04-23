def test_models(
    hf_runner,
    vllm_runner,
    example_prompts,
    model: str,
    max_tokens: int,
    num_logprobs: int,
    use_rocm_aiter: bool,
    use_prompt_embeds: bool,
    monkeypatch,
) -> None:
    model_info = HF_EXAMPLE_MODELS.find_hf_info(model)
    model_info.check_available_online(on_fail="skip")
    model_info.check_transformers_version(on_fail="skip")

    if use_rocm_aiter and (model in AITER_MODEL_LIST):
        monkeypatch.setenv("VLLM_ROCM_USE_AITER", "1")
        if model == "TitanML/tiny-mixtral":
            # Untrained model: near-uniform logits make argmax sensitive to
            # AITER's bfloat16 rounding error in plain rms_norm.
            monkeypatch.setenv("VLLM_ROCM_USE_AITER_RMSNORM", "0")
    elif use_rocm_aiter and model not in AITER_MODEL_LIST:
        # Skip model that are not using AITER tests.
        # When more AITER kernels are added, this list will not be
        # needed as all the models will be calling AITER kernels
        # in parts of the operators
        pytest.skip(f"Skipping '{model}' model test with AITER kernel.")

    with hf_runner(model) as hf_model:
        hf_outputs = hf_model.generate_greedy_logprobs_limit(
            example_prompts, max_tokens, num_logprobs
        )

        prompt_embeds: list[torch.Tensor] | None = [] if use_prompt_embeds else None

        for prompt in example_prompts:
            token_ids = hf_model.tokenizer(prompt, return_tensors="pt").input_ids.to(
                hf_model.model.device
            )
            if prompt_embeds is not None:
                embed = hf_model.model.get_input_embeddings()(token_ids)

                if "gemma" in model.lower() and (
                    Version(TRANSFORMERS_VERSION) < Version("5.3.0.dev0")
                ):
                    # For Gemma 1/2 models with Transformers 5.4.0+, the prompt
                    # embeddings are normalised in `get_prompt_embeddings`,
                    # like Gemma 3. For older versions, we need to manually normalise.
                    embed_scale = hf_model.config.hidden_size**0.5
                    normalizer = torch.tensor(embed_scale, dtype=embed.dtype)
                    embed *= normalizer

                # MiniCPM models apply scale_emb to embeddings internally.
                # vLLM expects pre-scaled embeddings when using inputs_embeds.
                if model in EMBED_SCALING_MODELS:
                    config = hf_model.model.config
                    embed = embed * config.scale_emb

                prompt_embeds.append(embed.squeeze(0))

    with vllm_runner(
        model,
        tokenizer_name=model_info.tokenizer or model,
        tokenizer_mode=model_info.tokenizer_mode,
        trust_remote_code=model_info.trust_remote_code,
        # Remove the effects of batch variance on ROCm since batch invariance
        # is not yet supported.
        # See: https://github.com/vllm-project/vllm/issues/27433
        max_num_seqs=1 if current_platform.is_rocm() else 2,
        enable_prompt_embeds=use_prompt_embeds,
        compilation_config={"cudagraph_capture_sizes": [1, 2]},
    ) as vllm_model:
        vllm_outputs = vllm_model.generate_greedy_logprobs(
            example_prompts, max_tokens, num_logprobs
        )
        if prompt_embeds is not None:
            vllm_outputs_from_embeds = vllm_model.generate_greedy_logprobs(
                prompt_embeds, max_tokens, num_logprobs
            )

    check_logprobs_close(
        outputs_0_lst=hf_outputs,
        outputs_1_lst=vllm_outputs,
        name_0="hf",
        name_1="vllm",
    )
    if prompt_embeds is not None:
        check_logprobs_close(
            outputs_0_lst=vllm_outputs,
            outputs_1_lst=vllm_outputs_from_embeds,
            name_0="vllm",
            name_1="vllm_from_embeds",
        )

    if use_rocm_aiter:
        # this is to ensure that vllm engine
        # has deallocated the memory before running the next
        # unit tests. On ROCm, when using AITER
        # the memory might not be deallocated completely
        # before running the next test case
        torch.accelerator.synchronize()