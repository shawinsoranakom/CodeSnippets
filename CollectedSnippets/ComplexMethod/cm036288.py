def test_pooling_metadata_token_id_buffers(
    pooling_params: dict[str, object],
    expect_device_prompt_token_ids: bool,
    expect_cpu_prompt_token_ids: bool,
):
    from vllm.pooling_params import PoolingParams

    input_batch = InputBatch(
        max_num_reqs=1,
        max_model_len=MAX_PROMPT_SIZE + NUM_OUTPUT_TOKENS,
        max_num_batched_tokens=MAX_PROMPT_SIZE + NUM_OUTPUT_TOKENS,
        device=torch.device("cpu"),
        pin_memory=False,
        vocab_size=VOCAB_SIZE,
        block_sizes=[16],
        kernel_block_sizes=[16],
        is_pooling_model=True,
    )
    req = _construct_pooling_request(0, PoolingParams(**pooling_params))
    input_batch.add_request(req)
    input_batch.refresh_metadata()

    metadata = input_batch.get_pooling_metadata()
    if expect_device_prompt_token_ids:
        assert input_batch.sampling_metadata.prompt_token_ids is not None
        assert metadata.prompt_token_ids is not None
        assert metadata.get_prompt_token_ids()[0].tolist() == req.prompt_token_ids
    else:
        assert input_batch.sampling_metadata.prompt_token_ids is None
        assert metadata.prompt_token_ids is None

    if expect_cpu_prompt_token_ids:
        assert metadata.prompt_token_ids_cpu is not None
        assert metadata.get_prompt_token_ids_cpu()[0].tolist() == req.prompt_token_ids
    else:
        assert metadata.prompt_token_ids_cpu is None