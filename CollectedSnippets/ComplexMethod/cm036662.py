def test_shuffle_rows_moe_like_scenario():
    """Test shuffle_rows in a scenario similar to MoE usage."""
    if not current_platform.is_cuda():
        pytest.skip("shuffle_rows requires CUDA")

    dtype = torch.float16
    batch_size = 32
    hidden_size = 1024
    topk = 2

    # Simulate input tokens
    input_tensor = torch.randn(batch_size, hidden_size, device="cuda", dtype=dtype)

    # Simulate expert assignment (each token goes to topk experts)
    # This creates a mapping where tokens are duplicated for multiple experts
    total_tokens = batch_size * topk
    dst2src_map = torch.zeros(total_tokens, device="cuda", dtype=torch.int32)

    # Fill the mapping to simulate MoE token distribution
    for i in range(batch_size):
        for k in range(topk):
            dst2src_map[i * topk + k] = i

    # Test shuffle_rows
    output = shuffle_rows(input_tensor, dst2src_map)

    # Check output shape
    assert output.shape == (total_tokens, hidden_size)
    assert output.dtype == dtype
    assert output.device == input_tensor.device

    # Verify that tokens are correctly duplicated
    for i in range(batch_size):
        for k in range(topk):
            output_idx = i * topk + k
            torch.testing.assert_close(
                output[output_idx], input_tensor[i], atol=1e-6, rtol=1e-5
            )