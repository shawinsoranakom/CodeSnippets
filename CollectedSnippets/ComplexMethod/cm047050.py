def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)
        original_params = list(sig.parameters.values())
        original_param_names = {p.name for p in original_params}

        # Build new parameters: config fields first, then original params
        new_params = []

        for field_name, field_info in fields:
            # Skip fields already defined in function signature (e.g., with envvar)
            if field_name in original_param_names:
                continue
            annotation = field_info.annotation
            if _is_list_type(annotation):
                continue

            flag_name = _python_name_to_cli_flag(field_name)
            help_text = field_info.description or ""

            if _is_bool_field(annotation):
                default = typer.Option(
                    None,
                    f"{flag_name}/--no-{field_name.replace('_', '-')}",
                    help = help_text,
                )
                param = inspect.Parameter(
                    field_name,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    default = default,
                    annotation = Optional[bool],
                )
            else:
                py_type = _get_python_type(annotation)
                default = typer.Option(None, flag_name, help = help_text)
                param = inspect.Parameter(
                    field_name,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    default = default,
                    annotation = Optional[py_type],
                )
            new_params.append(param)

        # Add original params, excluding config_overrides (will be injected)
        for param in original_params:
            if param.name != "config_overrides":
                new_params.append(param)

        new_sig = sig.replace(parameters = new_params)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            config_overrides = {}
            for key in list(kwargs.keys()):
                if key in field_names:
                    if kwargs[key] is not None:
                        config_overrides[key] = kwargs[key]
                    # Only delete if not an explicitly declared parameter
                    if key not in original_param_names:
                        del kwargs[key]

            kwargs["config_overrides"] = config_overrides
            return func(*args, **kwargs)

        wrapper.__signature__ = new_sig
        return wrapper