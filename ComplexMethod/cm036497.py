def test_chat(
    vllm_runner, max_model_len: int, model: str, dtype: str, local_asset_server
) -> None:
    if (
        model == MISTRAL_SMALL_3_1_ID
        and max_model_len == 65536
        and current_platform.is_rocm()
    ):
        pytest.skip(
            "OOM on ROCm: 24B model with 65536 context length exceeds GPU memory"
        )

    EXPECTED_CHAT_LOGPROBS = load_outputs_w_logprobs(FIXTURE_LOGPROBS_CHAT[model])
    with vllm_runner(
        model,
        dtype=dtype,
        tokenizer_mode="mistral",
        load_format="mistral",
        config_format="mistral",
        max_model_len=max_model_len,
        limit_mm_per_prompt=LIMIT_MM_PER_PROMPT,
    ) as vllm_model:
        outputs = []

        urls_all = [local_asset_server.url_for(u) for u in IMG_URLS]
        msgs = [
            _create_msg_format(urls_all[:1]),
            _create_msg_format(urls_all[:2]),
            _create_msg_format(urls_all),
        ]
        for msg in msgs:
            output = vllm_model.llm.chat(msg, sampling_params=SAMPLING_PARAMS)

            outputs.extend(output)

    logprobs = vllm_runner._final_steps_generate_w_logprobs(outputs)
    # Remove last `None` prompt_logprobs to compare with fixture
    for i in range(len(logprobs)):
        assert logprobs[i][-1] is None
        logprobs[i] = logprobs[i][:-1]
    check_logprobs_close(
        outputs_0_lst=EXPECTED_CHAT_LOGPROBS,
        outputs_1_lst=logprobs,
        name_0="h100_ref",
        name_1="output",
    )