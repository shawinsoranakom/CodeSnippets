def check_missing_params(
    command_params: dict[str, dict[str, dict]] | list[tuple[dict[str, str], str]],
    function_params: list[dict],
    function,
    processing: bool = False,
) -> list[str]:
    """Check if there are any missing params for a command."""
    missing_params = []
    if not processing:
        for i, test_params in enumerate(function_params):
            if "provider" in test_params and i != 0:
                provider = test_params["provider"]
                if provider in command_params:
                    for expected_param in command_params[provider]["QueryParams"][
                        "fields"
                    ]:
                        if expected_param not in test_params:
                            missing_params.append(
                                f"Missing param {expected_param} for provider {provider} in function {function}"
                            )
            elif isinstance(command_params, dict):
                for expected_param in command_params["openbb"]["QueryParams"]["fields"]:
                    if expected_param not in test_params:
                        missing_params.append(
                            f"Missing standard param {expected_param} in function {function}"
                        )
    else:
        for test_params in function_params:
            if isinstance(command_params, list):
                try:
                    iter_commands_params = command_params[0][0]
                except KeyError:
                    iter_commands_params = command_params[0]  # type: ignore

                for expected_param in iter_commands_params:
                    try:
                        used_params = test_params[0].keys()
                    except KeyError:
                        used_params = test_params.keys()
                    if expected_param not in used_params and expected_param not in (
                        "return",
                        "chart",
                    ):
                        missing_params.append(
                            f"Missing param {expected_param} in function {function}"
                        )
    return missing_params