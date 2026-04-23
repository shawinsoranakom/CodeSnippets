def is_pointwise_use(
    use: Node,
    is_pointwise_fn: Callable[[torch._ops.OpOverload], bool] = lambda _: False,
) -> bool:
    """
    Do all uses of this op have torch.Tag.pointwise or return True for optional `is_pointwise_fn`

    Uses in views ops will follow the views uses
    """

    if use.op != "call_function":
        return False
    if not (
        isinstance(use.target, torch._ops.OpOverload) or use.target is operator.getitem
    ):
        return False

    target = cast(torch._ops.OpOverload, use.target)
    if target is operator.getitem or is_view(target):
        return all(is_pointwise_use(u, is_pointwise_fn) for u in use.users)

    return torch.Tag.pointwise in target.tags or is_pointwise_fn(target)