def test_decode_bench_connector_multiple_requests():
    """Test DecodeBenchConnector with multiple sequential requests."""
    block_size = 16
    num_gpu_blocks = 100

    runner = DecodeBenchTestRunner(block_size=block_size, num_gpu_blocks=num_gpu_blocks)

    # First request
    req1 = runner.new_request([1] * (block_size * 2))
    _, metadata1 = runner.run_single_step()

    assert len(metadata1.reqs_to_fill) == 1
    assert req1.request_id in metadata1.reqs_to_fill

    # Complete first request
    while runner.scheduler.running:
        runner.run_single_step()

    # Add EOS to finish
    scheduler_output = runner.scheduler.schedule()
    model_runner_output = create_model_runner_output(
        reqs=runner.scheduler.running,
        token_id=EOS_TOKEN_ID,
        use_eos=True,
    )
    runner.scheduler.update_from_output(scheduler_output, model_runner_output)

    # Second request - should also get filled
    req2 = runner.new_request([2] * (block_size * 3))
    _, metadata2 = runner.run_single_step()

    assert len(metadata2.reqs_to_fill) == 1
    assert req2.request_id in metadata2.reqs_to_fill

    # Different request should have different metadata
    _, num_tokens1 = metadata1.reqs_to_fill[req1.request_id]
    _, num_tokens2 = metadata2.reqs_to_fill[req2.request_id]

    assert num_tokens1 == block_size * 2 - 1
    assert num_tokens2 == block_size * 3 - 1