def _nll_loss_forward_handler(
    op_call: torch._ops.OpOverload,
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> object:
    x = cast(DTensor, args[0])
    target = args[1]
    weight = args[2]
    reduction = cast(int, args[3])
    ignore_index = cast(int, args[4])

    channel_dim = 1 if x.dim() >= 2 else 0
    spec = x._spec
    mesh_dim = _find_all_reduce_mesh_dim(spec.placements, channel_dim)

    # Check user input: if target and weight are not DTensors, convert them to DTensors;
    # if they are DTensors, check that they have the desired placements.
    target_placements = _skip_dim(
        replicate_reduction_dims(spec.placements, [channel_dim]), channel_dim
    )
    all_replicate_placements = (Replicate(),) * spec.mesh.ndim
    target = _cast_to_dtensor(target, target_placements, spec.mesh)
    local_weight = None
    if weight is not None:
        weight = _cast_to_dtensor(weight, all_replicate_placements, spec.mesh)
        # For local computation, both (replicated) weight and (sharded) local_weight
        # are needed in _nll_loss_forward(). local_weight is generated here using
        # DTensor API, without incurring any communication.
        sharded_placements = [
            Shard(0) if i == mesh_dim else Replicate() for i in range(spec.mesh.ndim)
        ]
        local_weight = weight.redistribute(spec.mesh, sharded_placements)._local_tensor
        if local_weight.shape[0] != x._local_tensor.shape[channel_dim]:
            raise AssertionError

    if reduction == Reduction.NONE.value:
        output_placements = target_placements
    else:
        output_placements = all_replicate_placements

    # tensor inputs to _propagate_tensor_meta need to be DTensors
    # pyrefly: ignore [bad-assignment]
    args = list(args)
    # pyrefly: ignore [unsupported-operation]
    args[1], args[2] = target, weight
    output_tensor_meta = _propagate_tensor_meta(op_call, tuple(args), kwargs)

    result, total_weight = _nll_loss_forward(
        x._local_tensor,
        target._local_tensor,
        weight._local_tensor if weight is not None else None,
        local_weight,
        reduction,
        ignore_index,
        x.shape,
        channel_dim,
        spec.mesh,
        mesh_dim,
    )
    out_spec = DTensorSpec(spec.mesh, output_placements, tensor_meta=output_tensor_meta)

    return (
        # pyrefly: ignore [bad-argument-type]
        DTensor(
            # pyrefly: ignore [bad-argument-count]
            result,
            out_spec,
            # pyrefly: ignore [unexpected-keyword]
            requires_grad=result.requires_grad,
        ),
        total_weight,
    )