def validate_structured_output_request_outlines(params: SamplingParams):
    if params.structured_outputs is None:
        return

    so_params = params.structured_outputs

    if so_params.regex:
        validate_regex_is_buildable(so_params.regex)
    elif so_params.json:
        if isinstance(so_params.json, str):
            try:
                # make sure schema is valid json
                json.loads(so_params.json)
                schema = so_params.json
            except json.JSONDecodeError as e:
                raise ValueError("Invalid JSON grammar specification.") from e
        else:
            try:
                schema = json.dumps(so_params.json)
            except Exception as e:
                raise ValueError(
                    f"Error serializing structured outputs jsonschema: {e}"
                ) from e
        pattern = json_schema.build_regex_from_schema(schema)
        validate_regex_is_buildable(pattern)
    elif so_params.choice:
        choices = [regex_escape(str(choice)) for choice in so_params.choice]
        regex = "(" + "|".join(choices) + ")"
        validate_regex_is_buildable(regex)
    elif so_params.grammar:
        raise ValueError(
            "Outlines structured outputs backend "
            "does not support grammar specifications"
        )