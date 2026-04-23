def _fused_matmul_reduce_scatter_impl(
    mm_out_op: torch._ops.OpOverload,
    A: torch.Tensor,
    B: torch.Tensor,
    kwargs: dict[str, Any],
    out_dtype: torch.dtype | None,
    reduce_op: str,
    scatter_dim: int,
    group_name: c10d.GroupName,
) -> torch.Tensor:
    if A.dim() < 2:
        raise ValueError("A_shard must be a matrix")
    if scatter_dim < 0 or scatter_dim >= A.dim():
        raise ValueError("Invalid gather_dim")
    if B.dim() != 2:
        raise ValueError("B must be a matrix")
    if reduce_op == "sum":
        reduce_fn = partial(torch.sum, dim=0)
    elif reduce_op == "avg":
        reduce_fn = partial(torch.mean, dim=0)
    else:
        raise ValueError("reduce_op must be sum or avg")
    group = c10d._resolve_process_group(group_name)
    out_shape = [*A.shape[:-1], B.shape[1]]
    out_shape[scatter_dim] //= group.size()

    if scatter_dim == A.ndim - 1:
        B_shards = B.chunk(group.size(), dim=B.ndim - 1)
        A_flat = A.flatten(0, -2)

        def _chunk_producer(rank: int, out: torch.Tensor) -> None:
            mm_out_op(A_flat, B_shards[rank], **kwargs, out=out)

        leading_dims = list(A.shape[:-1])

        stacked_partials = torch.empty(
            (A_flat.shape[0], B.shape[1]),
            dtype=out_dtype or A.dtype,
            device=A.device,
        )

        _pipelined_produce_and_all2all(
            _chunk_producer,
            stacked_partials,
            group_name,
            out_chunk_dim=1,
        )

        stacked_partials_view = stacked_partials.reshape(
            *leading_dims, group.size(), -1
        )
        return reduce_fn(
            stacked_partials_view,
            dim=-2,
        )

    # Move the scatter_dim to the front and flatten the tensor into a 2D matrix
    x = A.movedim(scatter_dim, 0)
    leading_dims = [group.size()] + list(x.shape[:-1])
    leading_dims[1] //= group.size()
    x = x.flatten(0, -2)
    A_shards = x.chunk(group.size())

    # Computing block-wise matmul along the first dim of A
    def chunk_producer(rank: int, out: torch.Tensor) -> None:
        mm_out_op(A_shards[rank], B, **kwargs, out=out)

    stacked_partials = x.new_empty(x.shape[0], B.shape[1], dtype=out_dtype or A.dtype)

    _pipelined_produce_and_all2all(
        chunk_producer,
        stacked_partials,
        group_name,
    )

    # Ensures that the transpose and reduction produce contiguous result
    # in a single reduction kernel.
    return reduce_fn(
        stacked_partials.view(*leading_dims, -1)
        .movedim(1, scatter_dim + 1)
        .movedim(0, scatter_dim),
        dim=scatter_dim,
    )