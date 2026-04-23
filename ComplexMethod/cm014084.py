def bind_args_cached(
    func: FunctionType,
    tx: "InstructionTranslator",
    fn_source: Source | None,
    args: Sequence[Any],
    kwargs: dict[str, Any],
) -> dict[str, VariableTracker]:
    spec = _get_spec(func)

    # Fast path: simple positional-only, no defaults, no varargs/varkw
    # This is the common case for small utility functions called repeatedly.
    if (
        len(args) == spec.arg_count
        and not func.__defaults__
        and not kwargs
        and not spec.varargs_name
        and not spec.varkw_name
        and not spec.kwonly_names
    ):
        return {
            name: wrap_bound_arg(tx, args[i])
            for i, name in enumerate(spec.all_pos_names)
        }

    # Full path with all features
    spec.update_defaults(func)
    ba = {}
    rem_kw = dict(kwargs)

    # 1) Bind all positional (pos-only + pos-or-kw)
    # 1.1) Apply pos-defaults first (maybe overridden later)
    for name, idx in spec.pos_default_map.items():
        default_source = None
        if fn_source and not (
            ConstantVariable.is_literal(spec.defaults[idx])
            and config.skip_guards_on_constant_func_defaults
        ):
            default_source = DefaultsSource(fn_source, idx)
        ba[name] = wrap_bound_arg(tx, spec.defaults[idx], default_source)
    # 1.2) Fill in provided positional args
    for i, name in enumerate(spec.all_pos_names):
        if i < len(args):
            # Maybe override pos-defaults applied above
            ba[name] = wrap_bound_arg(tx, args[i])
        elif name in rem_kw and (
            # `kwargs` can have the same key as a pos-only arg `name`.
            # If this case happens, we should not consume the `name` here and
            # keep it in `kwargs`:
            #   >>> def fn(a, /, **kwargs): return (a, kwargs)
            #   >>> fn(1, a=2)
            #   (1, {'a': 2})
            name not in spec.posonly_names
        ):
            # Maybe override pos-defaults applied above
            ba[name] = wrap_bound_arg(tx, rem_kw.pop(name))
        elif name not in ba:
            raise TypeError(f"missing required positional argument: {name}")

    # 2) *args
    extra = args[len(spec.all_pos_names) :]
    if spec.varargs_name:
        ba[spec.varargs_name] = wrap_bound_arg(tx, tuple(extra))
    elif extra:
        raise TypeError(
            f"Too many positional arguments: got {len(args)}, expected {len(spec.all_pos_names)}"
        )

    # 3) Keyword-only
    for name in spec.kwonly_names:
        if name in rem_kw:
            ba[name] = wrap_bound_arg(tx, rem_kw.pop(name))
        elif name in spec.kwdefaults:
            kwdefault_source = None
            if fn_source:
                kwdefault_source = DefaultsSource(fn_source, name, is_kw=True)
            ba[name] = wrap_bound_arg(tx, spec.kwdefaults[name], kwdefault_source)
        else:
            raise TypeError(f"Missing required keyword-only argument: {name}")

    # 4) **kwargs
    if spec.varkw_name:
        ba[spec.varkw_name] = wrap_bound_arg(tx, rem_kw)
    elif rem_kw:
        raise TypeError(f"Unexpected keyword arguments: {list(rem_kw)}")

    return ba