def test_convert_moe_weights_to_flashinfer_trtllm_block_layout(
    num_experts, intermediate, hidden
):
    from vllm.model_executor.layers.quantization.utils.flashinfer_utils import (
        convert_moe_weights_to_flashinfer_trtllm_block_layout,
    )

    w13 = torch.randn(
        (num_experts, 2 * intermediate, hidden), dtype=torch.bfloat16, device="cuda"
    )
    w2 = torch.randn(
        (num_experts, hidden, intermediate), dtype=torch.bfloat16, device="cuda"
    )

    cache: dict[torch.Size, torch.Tensor] = {}
    w13_converted, w2_converted = convert_moe_weights_to_flashinfer_trtllm_block_layout(
        cache, w13, w2
    )

    assert w13_converted.ndim == 4, (
        f"Expected 4D tensor, got shape {w13_converted.shape}"
    )
    assert w2_converted.ndim == 4, f"Expected 4D tensor, got shape {w2_converted.shape}"

    assert w13_converted.numel() == w13.numel(), "W13 element count should be preserved"
    assert w2_converted.numel() == w2.numel(), "W2 element count should be preserved"

    assert w13_converted.dtype == torch.bfloat16
    assert w2_converted.dtype == torch.bfloat16

    assert w13_converted.shape[0] == num_experts
    assert w2_converted.shape[0] == num_experts