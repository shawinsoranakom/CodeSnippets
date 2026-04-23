def test_prepare_next_token_ids():
    """
    Test for prepare_next_token_ids_cpu and prepare_next_token_ids_padded.
    Each will produce a device tensor of next_token_ids, taking as input
    either the GPU tensor of sampled_token_ids with -1 for rejected tokens,
    or the CPU python list[list[int]] with the rejected tokens removed.
    """
    device = torch.device(DEVICE_TYPE)

    num_requests = 4
    num_speculative_tokens = 4
    req_ids = [f"req_{i + 1}" for i in range(num_requests)]
    mock_input_batch = mock.MagicMock(spec=InputBatch)
    mock_input_batch.req_ids = req_ids
    mock_input_batch.num_reqs = num_requests
    mock_input_batch.vocab_size = 100
    mock_input_batch.num_tokens_no_spec = np.array(
        [num_speculative_tokens + 1] * num_requests
    )

    mock_num_scheduled_tokens = {req_id: 0 for req_id in req_ids}
    mock_requests = {}
    for req_id in req_ids:
        mock_request = mock.MagicMock(spec=CachedRequestState)
        # Each request will have a backup next token id of 10, 20, 30, 40
        mock_request.get_token_id.return_value = int(req_id.split("_")[1]) * 10
        mock_request.num_computed_tokens = 0
        mock_requests[req_id] = mock_request

    # explicitly discard the last request
    discarded_req_mask = torch.tensor(
        [False, False, False, True], dtype=torch.bool, device=device
    )
    sampled_token_ids = [
        [0, 1, -1, -1, -1],  # 1 accepted, 3 rejected, "1" sampled
        [0, 1, 2, 3, 4],  # all accepted, "4" sampled
        [-1, -1, -1, -1, -1],  # sampling skipped, use backup token "30"
        [0, 1, 2, -1, -1],  # explicitly discarded, sampling should be ignored
    ]
    sampled_token_ids_tensor = torch.tensor(
        sampled_token_ids, dtype=torch.int32, device=device
    )
    sampled_token_ids_cpu = [[i for i in seq if i != -1] for seq in sampled_token_ids]
    for i in range(len(sampled_token_ids_cpu)):
        if discarded_req_mask[i]:
            sampled_token_ids_cpu[i] = []

    expected_next_token_ids_cpu = [1, 4, 30, 40]
    expected_next_token_ids_tensor = torch.tensor(
        expected_next_token_ids_cpu, dtype=torch.int32, device=device
    )

    proposer = _create_proposer("eagle", num_speculative_tokens)

    next_token_ids_from_cpu = proposer.prepare_next_token_ids_cpu(
        sampled_token_ids_cpu,
        mock_requests,
        mock_input_batch,
        mock_num_scheduled_tokens,
    )

    assert torch.equal(next_token_ids_from_cpu, expected_next_token_ids_tensor)

    expected_valid_sampled_tokens_count = torch.tensor(
        [2, 5, 0, 0], dtype=torch.int32, device=device
    )

    next_token_ids_from_padded, valid_sampled_tokens_count = (
        proposer.prepare_next_token_ids_padded(
            sampled_token_ids_tensor,
            mock_requests,
            mock_input_batch,
            discarded_req_mask,
        )
    )

    assert torch.equal(next_token_ids_from_padded, expected_next_token_ids_tensor)
    assert torch.equal(valid_sampled_tokens_count, expected_valid_sampled_tokens_count)