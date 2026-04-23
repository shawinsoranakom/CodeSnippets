def test_align_trtllm_fp4_moe_hidden_dim_pads_to_256_multiple():
    hidden_dim = 2688
    padded_hidden_dim = 2816

    w13 = torch.arange(2 * 12 * (hidden_dim // 2), dtype=torch.uint8).reshape(
        2, 12, hidden_dim // 2
    )
    w13_scale = torch.arange(2 * 12 * (hidden_dim // 16), dtype=torch.uint8).reshape(
        2, 12, hidden_dim // 16
    )

    w2 = torch.arange(2 * hidden_dim * 6, dtype=torch.uint8).reshape(2, hidden_dim, 6)
    w2_scale = torch.arange(2 * hidden_dim * 2, dtype=torch.uint8).reshape(
        2, hidden_dim, 2
    )

    out_w13, out_w13_scale, out_w2, out_w2_scale, out_hidden_dim = (
        align_trtllm_fp4_moe_hidden_dim_for_fi(w13, w13_scale, w2, w2_scale)
    )

    assert out_hidden_dim == padded_hidden_dim
    assert out_w13.shape == (2, 12, padded_hidden_dim // 2)
    assert out_w13_scale.shape == (2, 12, padded_hidden_dim // 16)
    assert out_w2.shape == (2, padded_hidden_dim, 6)
    assert out_w2_scale.shape == (2, padded_hidden_dim, 2)

    torch.testing.assert_close(out_w13[:, :, : hidden_dim // 2], w13)
    torch.testing.assert_close(out_w13_scale[:, :, : hidden_dim // 16], w13_scale)
    torch.testing.assert_close(out_w2[:, :hidden_dim, :], w2)
    torch.testing.assert_close(out_w2_scale[:, :hidden_dim, :], w2_scale)

    assert torch.count_nonzero(out_w13[:, :, hidden_dim // 2 :]) == 0
    assert torch.count_nonzero(out_w13_scale[:, :, hidden_dim // 16 :]) == 0
    assert torch.count_nonzero(out_w2[:, hidden_dim:, :]) == 0
    assert torch.count_nonzero(out_w2_scale[:, hidden_dim:, :]) == 0