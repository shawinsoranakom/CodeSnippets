def test_pack_seq_custom_padding_fp8():
    """Test pack_seq_triton with custom padding values for fp8."""
    device = "cuda"
    dtype = torch.float8_e4m3fn
    N, H, D, B = 20, 8, 16, 2
    lengths = torch.tensor([10, 10], device=device)

    x = torch.randn(N, H, D, dtype=torch.float32, device=device) * 0.1
    x = x.to(dtype=dtype)

    # Test with different padding values
    for pad_value in [-100.0, -10.0, 0.0, 10.0, 100.0]:
        result = pack_seq_triton(x, lengths, pad_value=pad_value)

        # Check valid data
        for b in range(B):
            start_idx = b * 10
            expected_data = x[start_idx : start_idx + 10].to(torch.float32)
            actual_data = result[b, :10].to(torch.float32)
            assert_close(actual_data, expected_data, rtol=1e-1, atol=1e-2)

        # Check padding (fp8 has limited range, so check for large values)
        padded_data = result[:, 10:].to(torch.float32)
        if pad_value < 0:
            assert torch.all(padded_data < -50)  # Large negative values
        elif pad_value > 0:
            assert torch.all(padded_data > 50)  # Large positive values
        else:
            assert torch.allclose(padded_data, torch.zeros_like(padded_data), atol=1e-2)