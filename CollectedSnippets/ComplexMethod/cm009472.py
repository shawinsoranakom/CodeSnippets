def _insert_input_variables(
    template: dict[str, Any],
    inputs: dict[str, Any],
    template_format: Literal["f-string", "mustache"],
) -> dict[str, Any]:
    formatted: dict[str, Any] = {}
    formatter = DEFAULT_FORMATTER_MAPPING[template_format]
    for k, v in template.items():
        if isinstance(v, str):
            formatted[k] = formatter(v, **inputs)
        elif isinstance(v, dict):
            if k == "image_url" and "path" in v:
                msg = (
                    "Specifying image inputs via file path in environments with "
                    "user-input paths is a security vulnerability. Out of an abundance "
                    "of caution, the utility has been removed to prevent possible "
                    "misuse."
                )
                warnings.warn(msg, stacklevel=2)
            formatted[k] = _insert_input_variables(v, inputs, template_format)
        elif isinstance(v, (list, tuple)):
            formatted_v: list[str | dict[str, Any]] = []
            for x in v:
                if isinstance(x, str):
                    formatted_v.append(formatter(x, **inputs))
                elif isinstance(x, dict):
                    formatted_v.append(
                        _insert_input_variables(x, inputs, template_format)
                    )
            formatted[k] = type(v)(formatted_v)
        else:
            formatted[k] = v
    return formatted