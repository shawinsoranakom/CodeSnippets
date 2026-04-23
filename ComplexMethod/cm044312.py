def build_new_signature(path: str, func: Callable) -> Signature:
    """Build new function signature."""
    sig = signature(func)
    parameter_list = sig.parameters.values()
    return_annotation = sig.return_annotation
    new_parameter_list: list = []
    var_kw_pos = len(parameter_list)

    for pos, parameter in enumerate(parameter_list):
        if (
            parameter.name == "cc"
            and parameter.annotation == CommandContext
            or parameter.name in ["kwargs", "args", "*", "**", "**kwargs", "*args"]
        ):
            # We do not add kwargs into the finished API signature.
            # Kwargs will be passed to every function that accepts them,
            # but we won't force the endpoint to take them.
            # We read the original signature in the wrapper to
            # determine if kwargs can be passed to the locals.
            continue

        # These are path parameters or dependency injections.
        if parameter.kind == Parameter.VAR_KEYWORD:
            # We track VAR_KEYWORD parameter to insert the any additional
            # parameters we need to add before it and avoid a SyntaxError
            var_kw_pos = pos

        if get_origin(parameter.annotation) is Annotated:
            # Get the metadata from Annotated
            metadata = get_args(parameter.annotation)[1:]
            # Check if any metadata item is a Depends instance
            if any(isinstance(m, DependsParam) for m in metadata):
                # Insert at var_kw_pos with include_in_schema=False
                new_parameter_list.insert(
                    var_kw_pos,
                    Parameter(
                        parameter.name,
                        kind=Parameter.POSITIONAL_OR_KEYWORD,
                        default=parameter.default,
                        annotation=parameter.annotation,
                    ),
                )
                var_kw_pos += 1
                continue

        new_parameter_list.append(
            Parameter(
                parameter.name,
                kind=parameter.kind,
                default=parameter.default,
                annotation=parameter.annotation,
            )
        )

    if CHARTING_INSTALLED and path.replace("/", "_")[1:] in Charting.functions():
        new_parameter_list.insert(
            var_kw_pos,
            Parameter(
                "chart",
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=False,
                annotation=bool,
            ),
        )
        var_kw_pos += 1

    if custom_headers := SystemService().system_settings.api_settings.custom_headers:
        for name, default in custom_headers.items():
            new_parameter_list.insert(
                var_kw_pos,
                Parameter(
                    name.replace("-", "_"),
                    kind=Parameter.POSITIONAL_OR_KEYWORD,
                    default=default,
                    annotation=Annotated[str | None, Header(include_in_schema=False)],
                ),
            )
            var_kw_pos += 1

    if Env().API_AUTH:
        new_parameter_list.insert(
            var_kw_pos,
            Parameter(
                "__authenticated_user_settings",
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=UserSettings(),
                annotation=Annotated[
                    UserSettings, Depends(AuthService().user_settings_hook)
                ],
            ),
        )
        var_kw_pos += 1

    return Signature(
        parameters=new_parameter_list,
        return_annotation=return_annotation,
    )