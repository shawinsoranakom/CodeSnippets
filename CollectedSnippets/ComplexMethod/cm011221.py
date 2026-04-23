def _fused_scaled_matmul_reduce_scatter_impl(
    mm_out_op: torch._ops.OpOverload,
    A: torch.Tensor,
    B: torch.Tensor,
    A_scale: torch.Tensor,
    kwargs: dict[str, Any],
    out_dtype: torch.dtype | None,
    reduce_op: str,
    orig_scatter_dim: int,
    scatter_dim_after_maybe_reshape: int,
    group_name: c10d.GroupName,
    output_shape: list[int],
) -> torch.Tensor:
    if A.dim() < 2:
        raise ValueError("A_shard must be a matrix")
    if (
        scatter_dim_after_maybe_reshape < 0
        or scatter_dim_after_maybe_reshape >= A.dim()
    ):
        raise ValueError("Invalid scatter dim for 2D tensor input to scaled_mm")
    if orig_scatter_dim < 0 or orig_scatter_dim >= len(output_shape):
        raise ValueError("Invalid scatter dim for 3D+ output tensor")
    if B.dim() != 2:
        raise ValueError("B must be a matrix")
    if reduce_op == "sum":
        reduce_fn = partial(torch.sum, dim=0)
    elif reduce_op == "avg":
        reduce_fn = partial(torch.mean, dim=0)
    else:
        raise ValueError("reduce_op must be sum or avg")

    group = c10d._resolve_process_group(group_name)

    # Move scatter to first dim, then shard the tensor along the first dim, so the chunk producer
    # can perform matmuls along the first dim.
    A_with_scatter_dim_0 = A.movedim(scatter_dim_after_maybe_reshape, 0)

    # To handle case where A is 3D+, reshape to 2D to prepare for mm which requires 2D inputs.
    A_2D_with_scatter_dim_0 = A_with_scatter_dim_0.flatten(0, -2)

    # Partition A along the first dim to prepare for sharding across TP process group.
    A_shards = A_2D_with_scatter_dim_0.chunk(group.size())

    # Now that 'A' is sharded along the first dim, we need to update its scale(s) accordingly.
    # How we do this depends on if we are using tensorwise scaling, rowwise scaling, or no scaling.
    tensorwise_scaling = A_scale is not None and A_scale.numel() == 1
    rowwise_scaling = A_scale is not None and A_scale.numel() > 1

    # For tensorwise scaling, the scale should be replicated so each shard has a copy.
    if tensorwise_scaling:
        A_scale_shards = [A_scale] * group.size()

    # For rowwise scaling, we need to move the scatter dim to the first dim to match the
    # dim swap of the 'A' tensor. Then we can shard the scales along the first dim, just like
    # the 'A' tensor.
    elif rowwise_scaling:
        if A_scale.shape[:-1] != A.shape[:-1]:
            raise ValueError(
                "For row-wise scaling, the leading dims of A_scale "
                "must match the leading dims of A "
                f"(A shape: {A.shape}, A_scale shape: {A_scale.shape})"
            )
        A_scale = (
            A_scale.movedim(scatter_dim_after_maybe_reshape, 0)
            .contiguous()
            .flatten(0, -2)
        )
        A_scale_shards = list(A_scale.chunk(group.size()))
        # cuBLAS's row-wise kernel requires scales to be aligned to 16 bytes.
        # When we slice them we might break this and need to reallocate them.
        A_scale_shards = [
            t if t.data_ptr() % 16 == 0 else t.clone() for t in A_scale_shards
        ]
    else:
        raise ValueError("A_scale cannot be none for scaled_mm")

    # Computing block-wise matmul along the first dim of A
    def chunk_producer(rank: int, out: torch.Tensor) -> None:
        mm_out_op(A_shards[rank], B, scale_a=A_scale_shards[rank], **kwargs, out=out)

    # Stacked partials will be the 2D outputs of the pipelined scaled mm, and will
    # have the shape (A_with_scatter_dim_0_tensor.shape[0], B.shape[1]) to align with the formula:
    # (a*b,c) @ (c,d) = (a*b,d)
    stacked_partials = A_with_scatter_dim_0.new_empty(
        A_2D_with_scatter_dim_0.shape[0], B.shape[1], dtype=out_dtype or A.dtype
    )

    # Execute the pipelined mm/scaled_mm.
    _pipelined_produce_and_all2all(
        chunk_producer,
        stacked_partials,
        group_name,
    )

    # We now need to transform the *unreduced* stacked 2D partial mm outputs to an *unreduced* 3D+ output,
    # then reduce-scatter. To do this, we first need to determine the shape of the unreduced 3D+ output,
    # to reshape our stacked partials so we can apply the reduce-scatter.
    #
    # The *unreduced* 3D+ tensor will have dim 0 = `group_size`, as we have `group_size` instances of
    # stacked partial outputs. The next dims will be A's leading dims (sharded along the original scatter dim),
    # as it was the left operand of the mm op. We can use -1 as the final dim of the view to populate the rest.
    stacked_partials_3D_leading_dims = [group.size()] + list(
        # We use A from after the dim swap 0<=>scatter_dim, but before the flatten,
        # to get the leading dims of the 3D+ view of stacked partials.
        A_with_scatter_dim_0.shape[:-1]
    )

    # The `group_size` leading dim has been prepended to `stacked_partials_3D_leading_dims`,
    # to capture the partial output from each rank. We need to divide the sharding/scatter dim
    # by the group size. If the original scatter dim was 0, then it is now dim 1 in this
    # tensor, since this new `group_size` dim was prepended.
    stacked_partial_scatter_dim = orig_scatter_dim if orig_scatter_dim > 0 else 1
    stacked_partials_3D_leading_dims[stacked_partial_scatter_dim] //= group.size()

    # Ensures that the transpose and reduction produce contiguous result
    # in a single reduction kernel.
    reduced_out = reduce_fn(
        # View 2D stacked partials as 3D+ tensor of shape (`group_size`, ...)
        stacked_partials.view(*stacked_partials_3D_leading_dims, -1)
        # We originally swapped 0<=>scatter_dim_after_maybe_reshape. Now after
        # prepending the `group_size` dim, to undo this original swap, we
        # must swap 1<=>scatter_dim_after_maybe_reshape+1.
        .movedim(1, scatter_dim_after_maybe_reshape + 1),
        # Reduce along the `group_size` dim (0).
        dim=0,
    )

    # Output shape must be scattered along original scatter dim as well.
    output_shape[orig_scatter_dim] //= group.size()
    out = reduced_out.view(*output_shape)
    return out