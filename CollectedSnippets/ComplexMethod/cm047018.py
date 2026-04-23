def check_gate_up_proj_grad(
    moe_block: Qwen3MoeSparseMoeBlock,
    grouped_gemm_block: Qwen3MoeGroupedGEMMBlock,
    atol: float,
    rtol: float,
):
    moe_intermediate_size = grouped_gemm_block.moe_intermediate_size
    for i, expert in enumerate(moe_block.experts):
        ref_gate_proj_grad = expert.gate_proj.weight.grad
        ref_up_proj_grad = expert.up_proj.weight.grad
        assert ref_gate_proj_grad is not None
        assert ref_up_proj_grad is not None

        # Extract gradients
        test_gate_proj_grad = grouped_gemm_block.gate_up_proj.grad[
            i, :moe_intermediate_size
        ]
        test_up_proj_grad = grouped_gemm_block.gate_up_proj.grad[
            i, moe_intermediate_size:
        ]
        assert test_gate_proj_grad is not None
        assert test_up_proj_grad is not None

        # Sanity check shapes
        assert (
            ref_gate_proj_grad.shape == test_gate_proj_grad.shape
        ), f"{ref_gate_proj_grad.shape} != {test_gate_proj_grad.shape}"
        assert (
            ref_up_proj_grad.shape == test_up_proj_grad.shape
        ), f"{ref_up_proj_grad.shape} != {test_up_proj_grad.shape}"

        # Check gradients
        diff = (ref_gate_proj_grad - test_gate_proj_grad).abs().max()
        if not torch.allclose(
            ref_gate_proj_grad, test_gate_proj_grad, atol = atol, rtol = rtol
        ):
            print(f"expert {i} gate_proj_grad_diff: {diff.detach().cpu().item():.6f}")
        diff = (ref_up_proj_grad - test_up_proj_grad).abs().max()
        if not torch.allclose(
            ref_up_proj_grad, test_up_proj_grad, atol = atol, rtol = rtol
        ):
            print(f"expert {i} up_proj_grad_diff: {diff.detach().cpu().item():.6f}")