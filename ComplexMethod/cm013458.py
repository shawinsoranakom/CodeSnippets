def _should_save_eager_input_vals(
    target: Any,
    args_kwargs: tuple[tuple[Argument, ...], dict[str, Argument]] | None = None,
) -> bool:
    from torch._higher_order_ops.invoke_subgraph import InvokeSubgraphHOP

    if not callable(target):
        return False
    if isinstance(
        target,
        (
            torch._higher_order_ops.triton_kernel_wrap.TritonKernelWrapperFunctional,
            torch._higher_order_ops.triton_kernel_wrap.TritonKernelWrapperMutation,
            InvokeSubgraphHOP,
        ),
    ):
        return True
    if args_kwargs is not None and (
        target is torch.ops.higher_order.auto_functionalized
        or target is torch.ops.higher_order.auto_functionalized_v2
    ):
        args = args_kwargs[0]
        if not isinstance(
            args[0], (torch._ops.OpOverload, torch._ops.HigherOrderOperator)
        ):
            raise AssertionError(
                f"Expected OpOverload or HigherOrderOperator, got {type(args[0])}"
            )
        return _should_save_eager_input_vals(args[0], None)
    if target is torch.ops.higher_order.with_effects:
        # TODO: inductor lowering for with_effects needs to be updated to propagate
        # the arg_kwarg_vals
        return False
    if isinstance(target, torch._ops.HigherOrderOperator):
        if pytree.tree_any(_should_save_eager_input_vals, args_kwargs):
            raise RuntimeError(
                f"NYI: The HOP {target} has an input that is an OpOverload that "
                f"needs exact strides. We probably need special logic to "
                f"propagate the FakeTensor vals. Please file an issue."
            )
    if isinstance(target, torch._ops.OpOverload):
        from torch._library.utils import get_layout_constraint_tag

        return get_layout_constraint_tag(target) == torch._C.Tag.needs_exact_strides
    return False