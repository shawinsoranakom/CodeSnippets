def _redistribute_backward(
    grad_output: "dtensor.DTensor",
    previous_spec: DTensorSpec,
    original_dtype: torch.dtype | None = None,
    backward_dtype: torch.dtype | None = None,
    async_op: bool = False,
):
    """
    Common function for redistributing a distributed tensor during backward
    and twice-backward backpropagation steps.

    Args:
        grad_output: The output gradient tensor.
        previous_spec: DTensorSpec prior to redistribution.
        original_dtype: Original output tensor dtype from forward pass (for type checking)
        backward_dtype: Desired data type for backwards output.
        async_op: whether to perform the DTensor redistribute operation
                asynchronously or not. Default: False

    Returns:
        A :class:`torch.Tensor` object.
        A :class:`DTensorSpec` object.
    """
    if backward_dtype is not None and backward_dtype != grad_output._local_tensor.dtype:
        local_tensor = grad_output._local_tensor.to(dtype=backward_dtype)
        current_spec = DTensorSpec(
            mesh=grad_output._spec.device_mesh,
            placements=grad_output._spec.placements,
            tensor_meta=TensorMeta(
                shape=grad_output.shape,
                stride=grad_output.stride(),
                # pyrefly: ignore [bad-argument-type]
                dtype=backward_dtype,
            ),
            use_strided_shard_as_shard_order=grad_output._spec.use_strided_shard_as_shard_order,
        )
        previous_spec = DTensorSpec(
            mesh=previous_spec.device_mesh,
            placements=previous_spec.placements,
            tensor_meta=current_spec.tensor_meta,
            use_strided_shard_as_shard_order=previous_spec.use_strided_shard_as_shard_order,
        )
    else:
        local_tensor = grad_output._local_tensor
        current_spec = grad_output._spec
    # skip the replicate to partial transformation when we are in backward pass
    # In this case we keep the grad as replicate, this is because we don't
    # want to convert the replicated gradients back to partial, although
    # that's logically conform with the same layout, converting the gradients
    # back to partial is actually useless as you would have to do reduce later
    # which would be more expensive than keeping it replicate!

    # for backward shard -> partial, we just do shard -> replicate
    # for backward replicate -> partial, we skip the transformation
    # NOTE: _is_shard_like covers _StridedShard defensively; currently
    # unreachable because Partial -> _StridedShard is not implemented.
    normalized_placements: list[Placement] = []
    for current, target in zip(current_spec.placements, previous_spec.placements):
        if (_is_shard_like(current) or current.is_replicate()) and target.is_partial():
            normalized_placements.append(Replicate())
        else:
            normalized_placements.append(target)

    previous_spec = DTensorSpec(
        previous_spec.device_mesh,
        placements=tuple(normalized_placements),
        tensor_meta=previous_spec.tensor_meta,
        use_strided_shard_as_shard_order=previous_spec.use_strided_shard_as_shard_order,
    )

    output = redistribute_local_tensor(
        local_tensor,
        current_spec,
        previous_spec,
        async_op=async_op,
    )

    if output.dtype != original_dtype:
        output = output.to(original_dtype)

    spec = DTensorSpec(
        previous_spec.device_mesh,
        tuple(normalized_placements),
        tensor_meta=TensorMeta(
            shape=grad_output.shape,
            stride=grad_output.stride(),
            dtype=output.dtype,
        ),
        use_strided_shard_as_shard_order=previous_spec.use_strided_shard_as_shard_order,
    )
    return output, spec