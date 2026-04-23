def do_auto_functionalize_v2(
    mode: "torch._subclasses.functional_tensor.FunctionalTensorMode",
    op: OpOverload | HopInstance,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    from torch._subclasses.functional_tensor import PythonFunctionalizeAPI

    ctx = PythonFunctionalizeAPI(mode=mode)

    # All of the (args, kwargs), but all as kwargs. The names for the
    # args come from the schema. This makes it easier for us to work with them.
    normalized_kwargs = {}

    schema = op._schema
    # pyrefly: ignore [bad-assignment]
    op = op._op if isinstance(op, HopInstance) else op
    if not isinstance(op, get_args(_MutableOpType)):
        raise AssertionError(f"Expected _MutableOpType, got {type(op)}")

    subgraph_arg_names = {
        arg_info.name
        for arg_info in schema.arguments
        if isinstance(arg_info.type, torch._C.AnyType)
    }

    def _maybe_functionalize(name: str, arg: Any) -> Any:
        if name in subgraph_arg_names and callable(arg):
            return FunctionalCallableWithEpilogue(arg)
        return arg

    args = tuple(
        _maybe_functionalize(schema.arguments[i].name, a)
        if i < len(schema.arguments)
        else a
        for i, a in enumerate(args)
    )
    kwargs = {k: _maybe_functionalize(k, v) for k, v in kwargs.items()}

    for idx, arg in enumerate(schema.arguments):
        # NB: torch_dispatch kwargs are the args defined as kwarg-only in the schema
        if arg.name in kwargs:
            normalized_kwargs[arg.name] = kwargs[arg.name]
        elif idx < len(args):
            # if its out of bounds we don't need to do anything
            # as it means the optional arg was passed with its default
            # value
            normalized_kwargs[arg.name] = args[idx]
        else:
            normalized_kwargs[arg.name] = arg.default_value

    if isinstance(op, OpOverload) and torch._library.utils.is_out(op):
        return _do_auto_functionalize_v2_for_out_operator(
            ctx, op, schema, normalized_kwargs
        )
    return _do_auto_functionalize_v2_for_generic_mutable_operator(
        ctx, op, schema, normalized_kwargs
    )