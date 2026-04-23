def _compare_results(
        self,
        logits: torch.Tensor,
        k: torch.Tensor | None,
        p: torch.Tensor | None,
    ):
        """Compare Triton kernel results with PyTorch sorting implementation.

        For top-k only, we expect exact match.
        For top-p (with or without top-k), we allow small differences due to
        floating-point precision in probability sum calculations.
        """
        from vllm.v1.sample.ops.topk_topp_triton import apply_top_k_top_p_triton

        # Clone logits for both implementations
        logits_pytorch = logits.clone()
        logits_triton = logits.clone().to(torch.float32)

        # Apply PyTorch sorting implementation
        result_pytorch = apply_top_k_top_p_pytorch(logits_pytorch, k, p)

        # Apply Triton kernel
        k_i32 = k.to(torch.int32) if k is not None else None
        p_f32 = p.to(torch.float32) if p is not None else None
        result_triton = apply_top_k_top_p_triton(logits_triton, k_i32, p_f32)

        # Compare kept counts per row
        pytorch_kept = (result_pytorch != float("-inf")).sum(dim=-1)
        triton_kept = (result_triton != float("-inf")).sum(dim=-1)

        if p is None:
            # Top-k only: expect exact match
            assert torch.equal(pytorch_kept, triton_kept), (
                f"Top-k mask mismatch: PyTorch kept {pytorch_kept.tolist()}, "
                f"Triton kept {triton_kept.tolist()}"
            )
        else:
            # Top-p involved: allow small differences
            # Either < 1% of kept values OR < 5 values absolute
            max_diff = (pytorch_kept - triton_kept).abs().max().item()
            max_kept = pytorch_kept.max().item()
            if max_kept > 0 and max_diff > 3:
                diff_pct = max_diff / max_kept * 100
                assert diff_pct < 0.5, (
                    f"Top-p mask difference too large: {diff_pct:.2f}% "
                    f"(max diff {max_diff} values out of {max_kept})"
                )