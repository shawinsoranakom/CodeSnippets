def populate_builtin_to_tensor_fn_map() -> None:
    global BUILTIN_TO_TENSOR_FN_MAP
    if len(BUILTIN_TO_TENSOR_FN_MAP) > 0:
        # Only populate once; after there are elements present no need to
        # repopulate
        return
    most_recent_func: Callable[..., Any] | None = None

    class GetMethodMode(BaseTorchFunctionMode):
        """
        Mode to extract the correct methods from torch function invocations
        (Used to get the correct torch.Tensor methods from builtins)
        """

        def __torch_function__(
            self,
            func: Callable[..., Any],
            types: Any,
            args: Sequence[Any] = (),
            kwargs: dict[str, Any] | None = None,
        ) -> Any:
            kwargs = kwargs or {}
            nonlocal most_recent_func
            most_recent_func = func
            return func(*args, **kwargs)

    inp0 = torch.ones(1)
    inp1 = torch.ones(1)
    inp0_int = torch.ones(1, dtype=torch.int32)
    inp1_int = torch.ones(1, dtype=torch.int32)
    with GetMethodMode():
        setups_and_oplists: list[tuple[Callable[..., Any], Iterable[Any]]] = [
            (lambda o: o(inp0), un_ops),
            (lambda o: o(inp0_int), un_int_ops),
            (lambda o: o(inp0, inp1), bin_ops),
            (lambda o: o(inp0_int, inp1_int), bin_int_ops),
            (lambda o: o(inp0_int, 0), tensor_and_int_ops),
        ]
        for setup_fn, op_list in setups_and_oplists:
            for op in op_list:
                setup_fn(op)
                assert most_recent_func is not None
                BUILTIN_TO_TENSOR_FN_MAP[op] = most_recent_func

        # gather the reverse functions
        rsetups_and_oplists: list[tuple[Callable[..., Any], Iterable[Any]]] = [
            (
                lambda o: o(1, inp1),
                bin_ops,
            ),  # Get r* ops, (ex. __sub__(int, Tensor) -> __rsub__(Tensor, int))
            (lambda o: o(1, inp1_int), bin_int_ops),
            (lambda o: o(0, inp0_int), tensor_and_int_ops),
        ]

        rskips = {operator.matmul, operator.imatmul, operator.getitem}
        for setup_fn, op_list in rsetups_and_oplists:
            for op in op_list:
                if op in rskips:
                    continue
                setup_fn(op)
                assert most_recent_func is not None
                if most_recent_func != BUILTIN_TO_TENSOR_FN_MAP[op]:
                    BUILTIN_TO_TENSOR_RFN_MAP[op] = most_recent_func