def validate_structured_output_request_lm_format_enforcer(params: SamplingParams):
    if params.structured_outputs is None:
        return

    so_params = params.structured_outputs

    if so_params.regex:
        return
    elif so_params.json:
        if isinstance(so_params.json, str):
            try:
                # make sure schema is valid json
                json.loads(so_params.json)
            except json.JSONDecodeError as e:
                raise ValueError("Invalid JSON grammar specification.") from e
        else:
            try:
                json.dumps(so_params.json)
            except Exception as e:
                raise ValueError(
                    f"Error serializing structured outputs jsonschema: {e}"
                ) from e
        return
    elif so_params.choice:
        return
    elif so_params.grammar:
        raise ValueError(
            "LM Format Enforcer structured outputs backend "
            "does not support grammar specifications"
        )