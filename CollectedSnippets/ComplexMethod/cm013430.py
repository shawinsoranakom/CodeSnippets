def _torchscript_schema_to_signature_impl(
    ts_schema: torch._C.FunctionSchema,
) -> inspect.Signature:
    from inspect import Parameter

    parameters: list[Parameter] = []
    for arg in ts_schema.arguments:
        arg_type = _torchscript_type_to_python_type(arg.type)
        default = arg.default_value if arg.has_default_value() else Parameter.empty
        # TODO: Figure out if this is safe. It seems like when generating the type signatures for
        # PythonArgParser, we emit signatures with `input` instead of `self` as the first tensor
        # argument name. Downstream, if someone converts that positional argument to a keyword
        # argument, the name mismatch will break things, so here we're going to normalize the
        # name to "input"
        name = arg.name if arg.name != "self" else "input"
        kind = (
            Parameter.KEYWORD_ONLY
            if arg.kwarg_only
            else Parameter.POSITIONAL_OR_KEYWORD
        )
        # "from" is a keyword therefore it must be a POSITIONAL_ONLY argument
        if name == "from":
            if kind != Parameter.POSITIONAL_OR_KEYWORD:
                raise AssertionError(f"Expected POSITIONAL_OR_KEYWORD, got {kind}")
            # ParameterKind type is internal implementation detail to inspec package
            # which makes it hard to do type annotation
            kind = Parameter.POSITIONAL_ONLY  # type: ignore[assignment]
            # This renders all previous arguments to positional only

            for idx, p in enumerate(parameters):
                if p.kind != Parameter.POSITIONAL_OR_KEYWORD:
                    raise AssertionError(
                        f"Expected POSITIONAL_OR_KEYWORD for param {p.name}, got {p.kind}"
                    )
                parameters[idx] = Parameter(
                    name=p.name,
                    kind=Parameter.POSITIONAL_ONLY,
                    default=p.default,
                    annotation=p.annotation,
                )

        parameters.append(
            Parameter(name=name, kind=kind, default=default, annotation=arg_type)
        )
    return_types = [
        _torchscript_type_to_python_type(ret.type) for ret in ts_schema.returns
    ]
    if len(return_types) == 0:
        return_type = None
    elif len(return_types) == 1:
        return_type = return_types[0]
    else:
        return_type = tuple(return_types)

    return inspect.Signature(parameters, return_annotation=return_type)