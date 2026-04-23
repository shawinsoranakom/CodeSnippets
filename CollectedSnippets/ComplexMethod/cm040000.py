def update_shapes_dict_for_target_fn(
    target_fn,
    shapes_dict,
    call_spec,
    class_name,
):
    """Updates a `shapes_dict` for `build()` or `compute_output_shape()`.

    This function will align a dictionary of the shapes of all tensor
    passed to `call`, with the signatures of `build()` or
    `compute_output_shape()`.

    The alignment is a follows:

    - If `build()` or `compute_output_shape()` accept only one argument,
        forward the shape of the first positional argument from call without
        checking any argument names.
    - If `build()` or `compute_output_shape()` accept multiple arguments,
        enforce that all argument names match a call argument name, e.g.
        `foo_shape` would match call argument `foo`.

    Returns:
        An updated `shapes_dict` that can be used to invoke
        `target_fn(**shapes_dict)`.
    """
    if utils.is_default(target_fn):
        return None
    sig = inspect.signature(target_fn)
    expected_names = []
    for name, param in sig.parameters.items():
        if param.kind in (
            param.POSITIONAL_OR_KEYWORD,
            param.POSITIONAL_ONLY,
            param.KEYWORD_ONLY,
        ):
            expected_names.append(name)

    # Single arg: don't check names, pass first shape.
    if len(expected_names) == 1:
        key = expected_names[0]
        values = tuple(shapes_dict.values())
        if values:
            input_shape = values[0]
        else:
            input_shape = None
        return {key: input_shape}

    # Multiple args: check that all names line up.
    kwargs = {}
    for name in expected_names:
        method_name = target_fn.__name__
        error_preamble = (
            f"For a `{method_name}()` method with more than one argument, all "
            "arguments should have a `_shape` suffix and match an argument "
            f"from `call()`. E.g. `{method_name}(self, foo_shape, bar_shape)` "
        )
        if not name.endswith("_shape"):
            raise ValueError(
                f"{error_preamble} For layer '{class_name}', "
                f"Received `{method_name}()` argument "
                f"`{name}`, which does not end in `_shape`."
            )
        expected_call_arg = utils.removesuffix(name, "_shape")
        if expected_call_arg not in call_spec.arguments_dict:
            raise ValueError(
                f"{error_preamble} For layer '{class_name}', "
                f"received `{method_name}()` argument "
                f"`{name}`, but `call()` does not have argument "
                f"`{expected_call_arg}`."
            )
        if name in shapes_dict:
            kwargs[name] = shapes_dict[name]

    return kwargs