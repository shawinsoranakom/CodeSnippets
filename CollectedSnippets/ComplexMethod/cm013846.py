def tensor_always_has_static_shape(
    tensor: torch.Tensor | Any,
    is_tensor: bool,
    tensor_source: Source,
) -> tuple[bool, TensorStaticReason | None]:
    """
    Given a tensor, source, and is_tensor flag, determine if a shape should be static.

    Args:
    tensor - the real tensor to evaluate, parameters force a static shape.
    is_tensor - internal dynamo check, essentially "is_tensor": target_cls is TensorVariable,
    tensors not in a TensorVariable for whatever reason are forced static.

    Returns a tuple, where the first element is the bool of whether or not this tensor should have a static shape.
    The second element is a TensorStaticReason, useful for passing to tensor_static_reason_to_message if needed.
    """
    from .source import is_from_unspecialized_param_buffer_source

    if (
        tensor_source.guard_source.is_specialized_nn_module()
        or tensor_source.guard_source.is_unspecialized_builtin_nn_module()
    ) and config.force_nn_module_property_static_shapes:
        return True, TensorStaticReason.NN_MODULE_PROPERTY

    if (
        type(tensor) is torch.nn.Parameter
        or is_from_unspecialized_param_buffer_source(tensor_source)
    ) and config.force_parameter_static_shapes:
        return True, TensorStaticReason.PARAMETER
    if not is_tensor:
        return True, TensorStaticReason.NOT_TENSOR
    return False, None