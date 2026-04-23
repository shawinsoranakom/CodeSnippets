def emit_view_func(
    f: NativeFunction, bindings: list[Binding], view_idx: str | None = None
) -> str:
    """Generate an additional lambda function to recover views in backward when as_strided is not supported.
    See Note [View + Inplace update for base tensor] and [View + Inplace update for view tensor] for more details.
    """
    # TODO: Clean this logic up if we get rid of reverse view funcs or reify them.
    input_base = "input_base"
    replay_view_func = ""
    updated_args: list[str] = []
    known_view_arg_simple_types: list[CType] = [
        BaseCType(longT),
        OptionalCType(BaseCType(longT)),
        BaseCType(SymIntT),
        OptionalCType(BaseCType(SymIntT)),
        BaseCType(boolT),
        BaseCType(intArrayRefT),
        BaseCType(symIntArrayRefT),
        ConstRefCType(BaseCType(tensorT)),
        ConstRefCType(OptionalCType(BaseCType(tensorT))),
    ]
    for binding in bindings:
        arg, arg_type = binding.name, binding.nctype.type
        if arg == "self":
            updated_args.append(input_base)
            continue
        if arg_type not in known_view_arg_simple_types:
            known_types_str = ", ".join([str(t) for t in known_view_arg_simple_types])
            raise TypeError(
                f"You are adding an {arg_type} {arg} argument to op {cpp.name(f.func)} in addition to known types: "
                f"{known_types_str}. Please update the list or materialize it so that it can be closed "
                "over by value, also add a test in pytorch/xla/test/test_operations.py where this code "
                "is exercised."
            )
        if arg_type == BaseCType(intArrayRefT) or arg_type == BaseCType(
            symIntArrayRefT
        ):
            # It's not safe to close over IntArrayRef by value, since this is a
            # reference type, so materialize a vector to close over by value
            arg_vec = arg + "_vec"
            replay_view_func += ARRAYREF_TO_VEC.substitute(arg=arg, vec=arg_vec)
            updated_args.append(arg_vec)
        elif arg_type == OptionalCType(BaseCType(longT)):
            # Materialize int64_t? to int64_t
            arg_value = arg + "_val"
            replay_view_func += OPTIONAL_TO_VAL.substitute(
                arg=arg, val=arg_value, default="0"
            )
            updated_args.append(arg_value)
        elif arg_type == ConstRefCType(BaseCType(tensorT)) or arg_type == ConstRefCType(
            OptionalCType(BaseCType(tensorT))
        ):
            # NB: Closing over a tensor. If a user modifies this tensor, this will be silently
            # incorrect. The proper thing to do is to store the version counter and copy on write.
            updated_args.append(arg)
        else:
            updated_args.append(arg)

    from .gen_view_funcs import view_func_name

    view_func_args = [b.name for b in bindings if b.name != "self"]
    if view_idx is not None:
        view_func_args.append(f"{view_idx}")
    replay_view_func += REPLAY_VIEW_FUNC.substitute(
        view_func_name=view_func_name(f, include_namespace=True),
        view_func_args=view_func_args,
    )

    input_view = "input_view"
    reverse_unpacked_args = [
        "self",
        f"{input_view}",
        # inverse_return_mode=
        "at::functionalization::InverseReturnMode::AlwaysView",
        *(() if view_idx is None else (f"{view_idx}",)),
        # skip input_base arg
        *updated_args[1:],
    ]

    from torchgen.api.functionalization import reverse_name

    reverse_replay_view_call = REVERSE_VIEW_DISPATCH.substitute(
        reverse_name=reverse_name(f, include_namespace=True),
        unpacked_args=reverse_unpacked_args,
    )
    reverse_replay_view_func = REVERSE_REPLAY_VIEW_LAMBDA_FUNC.substitute(
        input_view=input_view, reverse_replay_view_call=reverse_replay_view_call
    )

    is_view_with_metadata_change = (
        "true" if cpp.name(f.func) in VIEW_FUNCTIONS_WITH_METADATA_CHANGE else "false"
    )

    return SETUP_REPLAY_VIEW_IF_NOT_SUPPORT_AS_STRIDED_OR_VIEW_WITH_METADATA_CHANGE.substitute(
        is_view_with_metadata_change=is_view_with_metadata_change,
        replay_view_func=replay_view_func,
        reverse_replay_view_func=reverse_replay_view_func,
    )