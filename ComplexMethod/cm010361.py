def save_values_for_backward(ctx, args):
    if not all(
        isinstance(arg, (torch.Tensor, torch.SymInt, int, type(None), FakeScriptObject))
        or is_opaque_type(type(arg))
        for arg in args
    ):
        raise AssertionError(f"Invalid arg types in {args}")
    partitioned_args: list[Any] = [[], []]
    pos = []
    for arg in args:
        idx = 0 if isinstance(arg, torch.Tensor) else 1
        partitioned_args[idx].append(arg)
        pos.append(idx)

    if hasattr(ctx, "non_tensor_args"):
        raise AssertionError("ctx already has non_tensor_args attribute.")
    if hasattr(ctx, "pos"):
        raise AssertionError("ctx already has pos attribute.")
    ctx.save_for_backward(*partitioned_args[0])
    ctx.non_tensor_args = partitioned_args[1]
    ctx.pos = pos