def argument_names(
    f_sig: inspect.Signature,
    args: list[Any] | tuple[Any, ...],
    kwargs: dict[str, Any],
) -> list[str]:
    def signature_to_fullargspec(sig: inspect.Signature) -> inspect.FullArgSpec:
        # Get a list of Parameter objects from the Signature object
        params = list(sig.parameters.values())
        # Separate positional arguments, keyword-only arguments and varargs/varkw
        args = [
            p.name for p in params if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        ]
        kwonlyargs = [
            p.name for p in params if p.kind == inspect.Parameter.KEYWORD_ONLY
        ]
        varargs = next(
            (p.name for p in params if p.kind == inspect.Parameter.VAR_POSITIONAL),
            None,
        )
        varkw = next(
            (p.name for p in params if p.kind == inspect.Parameter.VAR_KEYWORD),
            None,
        )
        # Get default values for positional arguments and keyword-only arguments
        defaults = tuple(
            p.default
            for p in params
            if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
            and p.default is not inspect.Parameter.empty
        )
        kwonlydefaults = {
            p.name: p.default
            for p in params
            if p.kind == inspect.Parameter.KEYWORD_ONLY
            and p.default is not inspect.Parameter.empty
        }
        # Get annotations for parameters and return value
        # pyrefly: ignore [implicit-any]
        annotations = {}
        if sig.return_annotation:
            annotations = {"return": sig.return_annotation}
        for parameter in params:
            annotations[parameter.name] = parameter.annotation
        # Return a FullArgSpec object with the extracted attributes
        return inspect.FullArgSpec(
            args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations
        )

    fullargspec = signature_to_fullargspec(f_sig)

    # 1. Map `args` 1-to-1 to positional arguments in original signature.
    input_strs = fullargspec.args[: len(args)]

    if len(args) > len(fullargspec.args):
        # 2. If there are more arguments left in `args`, they map to varargs in original
        # signature. Assign names as {varargs}_0, {varargs}_1, ...
        assert fullargspec.varargs is not None, "More arguments than expected"
        input_strs += [
            f"{fullargspec.varargs}_{i}" for i in range(len(args) - len(input_strs))
        ]
    elif len(args) < len(fullargspec.args):
        # 3. If there are fewer arguments in `args` than `fullargspec.args`,
        # it implies these are arguments either with default values, or provided in
        # `kwargs`. The former can be safely ignored. Because Dynamo.export does not
        # export them as part of the function signature. The latter will be handled
        # in the next step.
        for unprovided_arg in fullargspec.args[
            len(args) : -len(fullargspec.defaults or [])
        ]:
            assert unprovided_arg in kwargs, f"Missing argument {unprovided_arg}"

    # 4. Keyword arguments provided in `kwargs`.
    input_strs += list(kwargs.keys())

    # 5. Keyword-only arguments with default values if not provided are not exported
    # as part of the function signature.
    for kwonly_arg in fullargspec.kwonlyargs:
        kwonlydefaults = fullargspec.kwonlydefaults or {}
        assert kwonly_arg in kwargs or kwonly_arg in kwonlydefaults, (
            f"Missing keyword only argument {kwonly_arg}"
        )

    return input_strs