def _fused_all_gather_matmul_impl(
    mm_out_op: torch._ops.OpOverload,
    A_shard: torch.Tensor,
    Bs: list[torch.Tensor],
    A_scale: torch.Tensor | None,
    kwargs_list: list[dict[str, Any]],
    out_dtypes: list[torch.dtype | None],
    gather_dim: int,
    group_name: c10d.GroupName,
    return_A: bool,
) -> tuple[torch.Tensor | None, list[torch.Tensor]]:
    if A_shard.dim() < 2:
        raise ValueError("A_shard must be a matrix")
    for B in Bs:
        if B.dim() != 2:
            raise ValueError("B must be a matrix")
    if len(out_dtypes) != len(Bs):
        raise ValueError("len(out_types) must be the same as len(Bs)")
    if len(kwargs_list) != len(Bs):
        raise ValueError("len(kwargs_list) must be the same as len(Bs)")
    if gather_dim < 0 or gather_dim >= A_shard.dim():
        raise ValueError("Invalid gather_dim")

    group = c10d._resolve_process_group(group_name)

    if gather_dim == A_shard.ndim - 1 or gather_dim == -1:
        return _fused_all_gather_matmul_last_gather_dim_impl(
            mm_out_op,
            A_shard,
            Bs,
            A_scale,
            kwargs_list,
            out_dtypes,
            gather_dim,
            group_name,
            return_A,
        )

    # Move the gather_dim to the front and flatten the tensor into a 2D matrix.
    # The flattened tensor doesn't need to be contiguous (for computation
    # efficiency), as _pipelined_all_gather_and_consume guarantees that shards
    # passed to shard_consumer are contiguous.
    A_shard_flat = A_shard.movedim(gather_dim, 0)
    leading_dims = [group.size()] + list(A_shard_flat.shape[:-1])
    A_shard_flat = A_shard_flat.flatten(0, -2)

    # Helper function for reverting the above transformation
    def unflatten(t: torch.Tensor) -> torch.Tensor:
        return t.view(*leading_dims, -1).flatten(0, 1).movedim(0, gather_dim)

    A_flat = A_shard_flat.new_empty(
        A_shard_flat.shape[0] * group.size(),
        A_shard_flat.shape[1],
    )

    outputs = [
        A_flat.new_empty(A_flat.shape[0], B.shape[1], dtype=out_dtype or B.dtype)
        for B, out_dtype in zip(Bs, out_dtypes)
    ]
    output_shards = [output.chunk(group.size()) for output in outputs]

    scale_mode = _check_and_verify_fp8_all_gather_scale_mode(
        shard=A_shard, scale=A_scale, gather_dim=gather_dim, group_size=group.size()
    )

    # Computing block-wise matmul along the first dim of A
    if scale_mode == _ScaleMode.ROW_WISE_SHARDED:
        if A_scale is None:
            raise AssertionError
        A_scale_shard = A_scale.movedim(gather_dim, 0).flatten(0, -2)
        A_scale_flat = A_scale_shard.new_empty(
            A_scale_shard.shape[0] * group.size(),
            A_scale_shard.shape[1],
        )

        def row_wise_sharded_consumer(shard: list[torch.Tensor], rank: int) -> None:
            for idx, (B, kwargs) in enumerate(zip(Bs, kwargs_list)):
                mm_out_op(
                    shard[0],
                    B,
                    scale_a=shard[1],
                    **kwargs,
                    out=output_shards[idx][rank],
                )

        _pipelined_multi_all_gather_and_consume(
            [A_shard_flat, A_scale_shard],
            row_wise_sharded_consumer,
            [A_flat, A_scale_flat],
            group_name,
            return_A,
        )
    elif scale_mode == _ScaleMode.ROW_WISE_REPLICATED:
        if A_scale is None:
            raise AssertionError
        A_scale_shards = (
            A_scale.movedim(gather_dim, 0).flatten(0, -2).chunk(group.size())
        )

        def row_wise_replicated_consumer(shard: torch.Tensor, rank: int) -> None:
            for idx, (B, kwargs) in enumerate(zip(Bs, kwargs_list)):
                mm_out_op(
                    shard,
                    B,
                    scale_a=A_scale_shards[rank],
                    **kwargs,
                    out=output_shards[idx][rank],
                )

        _pipelined_all_gather_and_consume(
            A_shard_flat,
            row_wise_replicated_consumer,
            A_flat,
            group_name,
            return_A,
        )
    else:
        if scale_mode == _ScaleMode.TENSOR_WISE:
            if A_scale is None:
                raise AssertionError
            for kwargs in kwargs_list:
                kwargs["scale_a"] = A_scale
        else:
            if scale_mode != _ScaleMode.UNSCALED:
                raise AssertionError

        def default_consumer(shard: torch.Tensor, rank: int) -> None:
            for idx, (B, kwargs) in enumerate(zip(Bs, kwargs_list)):
                mm_out_op(shard, B, **kwargs, out=output_shards[idx][rank])

        _pipelined_all_gather_and_consume(
            A_shard_flat,
            default_consumer,
            A_flat,
            group_name,
            return_A,
        )

    A = unflatten(A_flat) if return_A else None
    return A, [unflatten(output) for output in outputs]