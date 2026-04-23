def test_check_stop_min_tokens():
    """Test that requests don't stop when min_tokens requirement isn't met."""
    from vllm.v1.core.sched.utils import check_stop

    # Test case 1: num_output_tokens < min_tokens
    # Should return False (don't stop)
    sampling_params = SamplingParams(
        ignore_eos=False,
        max_tokens=20,
        min_tokens=5,
    )
    sampling_params.update_from_generation_config({}, EOS_TOKEN_ID)
    request = Request(
        request_id="0",
        prompt_token_ids=[0, 1, 2],
        sampling_params=sampling_params,
        pooling_params=None,
    )
    # Simulate having generated 3 output tokens (less than min_tokens=5)
    request.append_output_token_ids([10, 11, EOS_TOKEN_ID])  # EOS token present

    result = check_stop(request, max_model_len=100)
    assert result is False, "Should not stop when num_output_tokens<min_tokens"

    # Test case 2: num_output_tokens >= min_tokens
    # Should follow normal stopping logic (stop on EOS)
    request.append_output_token_ids(
        [
            10,
            11,
            12,
            13,
            14,
            EOS_TOKEN_ID,
        ]
    )  # 6 tokens > min_tokens

    result = check_stop(request, max_model_len=100)
    assert result is True, "Should stop on EOS when min_tokens met"
    assert request.status == RequestStatus.FINISHED_STOPPED

    # Test case 3: min_tokens = 0, should follow normal stopping logic
    sampling_params_no_min = SamplingParams(
        ignore_eos=False,
        max_tokens=20,
        min_tokens=0,
    )
    sampling_params_no_min.update_from_generation_config({}, EOS_TOKEN_ID)
    request_no_min = Request(
        request_id="1",
        prompt_token_ids=[0, 1, 2],
        sampling_params=sampling_params_no_min,
        pooling_params=None,
    )
    request_no_min.append_output_token_ids([10, EOS_TOKEN_ID])

    result = check_stop(request_no_min, max_model_len=100)
    assert result is True, "Should stop on EOS when min_tokens=0"
    assert request_no_min.status == RequestStatus.FINISHED_STOPPED

    # Test case 4: min_tokens > 0 with stop token (not EOS)
    sampling_params_stop = SamplingParams(
        ignore_eos=False,
        max_tokens=20,
        min_tokens=5,
        stop_token_ids=[42],
    )
    sampling_params_stop.update_from_generation_config({}, EOS_TOKEN_ID)
    request_stop = Request(
        request_id="2",
        prompt_token_ids=[0, 1, 2],
        sampling_params=sampling_params_stop,
        pooling_params=None,
    )
    # Only 3 output tokens, less than min_tokens=5, but has stop token
    request_stop.append_output_token_ids([10, 11, 42])
    result = check_stop(request_stop, max_model_len=100)
    assert result is False, "Should not stop when num_output_tokens<min_tokens"

    # Test case 5: min_tokens met, should stop on stop token
    request_stop.append_output_token_ids(
        [10, 11, 12, 13, 14, 42]
    )  # 6 tokens >= min_tokens=5

    result = check_stop(request_stop, max_model_len=100)
    assert result is True, "Should stop on stop token when min_tokens met"
    assert request_stop.status == RequestStatus.FINISHED_STOPPED
    assert request_stop.stop_reason == 42