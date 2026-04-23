def test_sampling_metadata_in_input_batch(device: str, batch_size: int):
    """
    Tests the logic for managing sampling metadata in the InputBatch.

    This test involves adding a set of requests to the InputBatch,
    followed by removing a subset of them. Afterward, the batch is compacted,
    and the `make_sampling_metadata` method is invoked on the batch. The
    output of `make_sampling_metadata` is then compared against the expected
    results to ensure correctness.

    Note: Ignore logits processor logic, which is tested separately
    """
    input_batch: InputBatch = InputBatch(
        max_num_reqs=batch_size,
        max_model_len=1024,
        max_num_batched_tokens=1024,
        device=torch.device(device),
        pin_memory=is_pin_memory_available(),
        vocab_size=1024,
        block_sizes=[1],
        kernel_block_sizes=[1],
    )
    reqs: list[CachedRequestState] = []
    req_id_reqs = {}
    req_id_output_token_ids = {}

    # Add requests
    for req_index in range(batch_size):
        req: CachedRequestState = _construct_cached_request_state(req_index)
        assigned_req_index = input_batch.add_request(req)
        assert req_index == assigned_req_index
        reqs.append(req)
        req_id_reqs[req.req_id] = req
        req_id_output_token_ids[req.req_id] = req.output_token_ids

    # Remove some requests
    req_ids_to_remove = _remove_requests(input_batch, batch_size, reqs)
    req_ids_retained = set(req_id_reqs.keys()) - req_ids_to_remove

    # Compact the input batch
    input_batch.condense()

    # Generate the sampling metadata
    sampling_metadata = input_batch._make_sampling_metadata()

    # Create expected output.
    expected_sampling_metadata = _construct_expected_sampling_metadata(
        reqs, req_ids_retained, input_batch.req_id_to_index, device=torch.device(device)
    )

    def same(t1: torch.Tensor | None, t2: torch.Tensor | None) -> bool:
        return (t1 is None and t2 is None) or (
            t1 is not None and t2 is not None and torch.allclose(t1, t2)
        )

    # Assert the actual and expected output.
    assert torch.allclose(
        expected_sampling_metadata.temperature, sampling_metadata.temperature
    )
    assert same(expected_sampling_metadata.top_p, sampling_metadata.top_p)
    assert same(expected_sampling_metadata.top_k, sampling_metadata.top_k)
    assert torch.allclose(
        expected_sampling_metadata.frequency_penalties,
        sampling_metadata.frequency_penalties,
    )
    assert torch.allclose(
        expected_sampling_metadata.presence_penalties,
        sampling_metadata.presence_penalties,
    )
    assert torch.allclose(
        expected_sampling_metadata.repetition_penalties,
        sampling_metadata.repetition_penalties,
    )
    assert torch.allclose(
        expected_sampling_metadata.prompt_token_ids, sampling_metadata.prompt_token_ids
    )
    assert (
        expected_sampling_metadata.output_token_ids
        == sampling_metadata.output_token_ids
    )
    assert expected_sampling_metadata.no_penalties == sampling_metadata.no_penalties
    if sampling_metadata.allowed_token_ids_mask:
        assert torch.allclose(
            expected_sampling_metadata.allowed_token_ids_mask,
            sampling_metadata.allowed_token_ids_mask,
        )
    assert (
        expected_sampling_metadata.bad_words_token_ids
        == sampling_metadata.bad_words_token_ids
    )