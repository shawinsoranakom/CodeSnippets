def use_scatter_fallback(
    op_overload: torch._ops.OpOverload,
    reduction_type: str | None,
    self_dtype: torch.dtype,
    src_dtype: torch.dtype,
    src_device_type: str,
    src_is_tensor: bool,
) -> bool:
    if (
        op_overload.overloadpacket
        in (torch.ops.aten.scatter_reduce_, torch.ops.aten.scatter_reduce)
        and reduction_type is None
    ):
        return False

    reduce_ty = (
        "add" if op_overload.overloadpacket == torch.ops.aten.scatter_ else "sum"
    )

    return (
        reduction_type not in (None, reduce_ty)
        or (
            src_is_tensor
            and is_gpu(src_device_type)
            and needs_fallback_due_to_atomic_add_limitations(src_dtype)
        )
        or (
            op_overload.overloadpacket == torch.ops.aten.scatter_reduce_
            and reduction_type == "sum"
            and src_is_tensor
            and src_device_type == "cpu"
            and config.cpp.fallback_scatter_reduce_sum
            and (config.cpp.dynamic_threads or parallel_num_threads() != 1)
        )
        or (reduction_type == reduce_ty and self_dtype in (torch.bool, torch.int64))
        or torch.are_deterministic_algorithms_enabled()
    )