def format_trace_inputs(f: NativeFunction) -> str:
    def dispatch_trace_input(arg: Argument | TensorOptionsArguments) -> Sequence[str]:
        if isinstance(arg, TensorOptionsArguments):
            name = "options"
            return [
                ADD_TRACE_INPUT.substitute(
                    name=name, input="c10::optTypeMetaToScalarType(options.dtype_opt())"
                ),
                ADD_TRACE_INPUT.substitute(name=name, input="options.layout()"),
                ADD_TRACE_INPUT.substitute(name=name, input="options.device()"),
                ADD_TRACE_INPUT.substitute(name=name, input="options.pinned_memory()"),
            ]
        else:
            name = arg.name
            if str(arg.type) == "Tensor?[]":
                return [f'jit::tracer::addInputs(node, "{name}", {name});']
            else:
                return [ADD_TRACE_INPUT.substitute(name=name, input=name)]

    args: list[Argument | TensorOptionsArguments] = list(
        f.func.schema_order_arguments()
    )

    if f.func.is_out_fn():
        # *_out functions take the result as a separate argument, but we don't want to
        # trace that argument directly. Instead, we trace its TensorOptions.
        # So first, we need to remove the out argument from the list of arguments to trace.
        num_out_args = len(f.func.arguments.out)
        args = args[:-num_out_args]

    trace_inputs = itertools.chain.from_iterable(
        dispatch_trace_input(arg) for arg in args
    )

    if f.func.is_out_fn():
        # for *_out functions, handle the result argument differently for inplace/outplace.
        # For inplace: just add the input to the end to confirm with the JIT schema
        inplace = [
            ADD_TRACE_INPUT.substitute(
                name=f.func.arguments.out[i].name, input=f.func.arguments.out[i].name
            )
            # pyrefly: ignore [unbound-name]
            for i in range(num_out_args)
        ]

        # for outplace: do nothing, except if the function is a factory.
        # Factories are a bit special because their out-of-place overloads
        # take an extra TensorOptions argument, which is missing in the _out function
        has_tensor_return = any(r.type.is_tensor_like() for r in f.func.returns)
        has_tensor_input_arg = any(
            a.type.is_tensor_like() for a in f.func.arguments.flat_non_out
        )
        is_factory_method = f.category_override == "factory" or (
            has_tensor_return and not has_tensor_input_arg
        )

        # HACK: preserve old codegen behavior - the old codegen set the `is_factory_method`
        # flag for the whole family of ops with the same basename if any of them is a
        # factory method. For most cases the whole family of ops are indeed all factory
        # method - 'normal' is the only exception. So we handle it specially here to avoid
        # cloning the old logic.
        if f.func.name.name.base == "normal":
            is_factory_method = True

        if is_factory_method:
            outplace = [
                ADD_TRACE_INPUT.substitute(
                    name="out",
                    input="c10::optTypeMetaToScalarType(out.options().dtype_opt())",
                ),
                ADD_TRACE_INPUT.substitute(name="out", input="out.options().layout()"),
                ADD_TRACE_INPUT.substitute(name="out", input="out.options().device()"),
                ADD_TRACE_INPUT.substitute(
                    name="out", input="out.options().pinned_memory()"
                ),
            ]
        else:
            outplace = []

        trace_inputs = itertools.chain(
            trace_inputs,
            [
                SELECT.substitute(
                    cond="tracer_state->force_outplace",
                    true="\n".join(outplace),
                    false="\n".join(inplace),
                )
            ],
        )

    return "\n".join(trace_inputs)