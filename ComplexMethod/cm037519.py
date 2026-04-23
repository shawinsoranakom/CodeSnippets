def nested_tensors_equal(a: NestedTensors, b: NestedTensors) -> bool:
    """
    Equality check between
    [`NestedTensors`][vllm.multimodal.inputs.NestedTensors] objects.
    """
    if isinstance(a, torch.Tensor):
        return isinstance(b, torch.Tensor) and torch.equal(a, b)
    elif isinstance(b, torch.Tensor):
        return isinstance(a, torch.Tensor) and torch.equal(b, a)

    if isinstance(a, list):
        return (
            isinstance(b, list)
            and len(a) == len(b)
            and all(nested_tensors_equal(a_, b_) for a_, b_ in zip(a, b))
        )
    if isinstance(b, list):
        return (
            isinstance(a, list)
            and len(b) == len(a)
            and all(nested_tensors_equal(b_, a_) for b_, a_ in zip(b, a))
        )

    if isinstance(a, tuple):
        return (
            isinstance(b, tuple)
            and len(a) == len(b)
            and all(nested_tensors_equal(a_, b_) for a_, b_ in zip(a, b))
        )
    if isinstance(b, tuple):
        return (
            isinstance(a, tuple)
            and len(b) == len(a)
            and all(nested_tensors_equal(b_, a_) for b_, a_ in zip(b, a))
        )

    # Both a and b are scalars
    return a == b