def _fused_all_gather_scaled_matmul(
    A_shard: torch.Tensor,
    Bs: list[torch.Tensor],
    A_scale: torch.Tensor,
    B_scales: list[torch.Tensor],
    gather_dim: int,
    group_name: c10d.GroupName,
    biases: list[torch.Tensor | None],
    result_scales: list[torch.Tensor | None],
    out_dtypes: list[torch.dtype | None],
    use_fast_accum: list[bool],
) -> tuple[torch.Tensor, list[torch.Tensor]]:
    """
    Perform the following logic with micro-pipelined computation and
    communication:

        A = all_gather_tensor(A_shard, gather_dim, group_name)
        leading_dims = A.shape[:-1]
        res = torch.ops.aten._scaled_mm(A.flatten(0, -2), B, A_scale, B_scale)
        res = res.unflatten(0, leading_dims)

    The input `A_scale` can be tensor-wise, row-wise-sharded or
    row-wise-replicated.

    Optimal stride order for `A_shard` - if `A_shard.movedim(gather_dim, 0)` is
    contiguous, no extra copy is required for input layout transformation.
    Otherwise A_shard needs to be copied once.
    """
    out_dtypes = _maybe_convert_scalar_types_to_dtypes(out_dtypes)

    if len(biases) != len(Bs):
        raise ValueError("len(biases) must be the same as len(Bs)")
    if len(result_scales) != len(Bs):
        raise ValueError("len(result_scales) must be the same as len(Bs)")
    if len(out_dtypes) != len(Bs):
        raise ValueError("len(out_dtypes) must be the same as len(Bs)")
    if len(use_fast_accum) != len(Bs):
        raise ValueError("len(use_gast_accum_list) must be the same as len(Bs)")

    if _is_test_mode:
        return _fused_all_gather_scaled_matmul_fallback(
            A_shard,
            Bs,
            A_scale,
            B_scales,
            gather_dim,
            group_name,
            biases,
            result_scales,
            out_dtypes,
            use_fast_accum,
        )

    with torch.profiler.record_function("fused_all_gather_scaled_matmul"):
        A, res = _fused_all_gather_matmul_impl(
            torch.ops.aten._scaled_mm.out,
            A_shard,
            Bs,
            A_scale,
            [
                {
                    "scale_b": B_scale,
                    "bias": bias,
                    "scale_result": result_scale,
                    "out_dtype": out_dtype,
                    "use_fast_accum": fast_accum,
                }
                for B_scale, bias, result_scale, out_dtype, fast_accum in zip(
                    B_scales, biases, result_scales, out_dtypes, use_fast_accum
                )
            ],
            out_dtypes,
            gather_dim,
            group_name,
            True,
        )
        if A is None:
            raise AssertionError
        return A, res