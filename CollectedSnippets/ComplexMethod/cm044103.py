def check_wrong_params(
    command_params: dict[str, dict[str, dict]] | list[tuple[dict[str, str], str]],
    function_params: list[dict],
    function,
    processing: bool = False,
) -> list[str]:
    """Check if there are any wrong params passed to a command."""
    wrong_params = []
    if not processing:
        for i, test_params in enumerate(function_params):
            if "provider" in test_params and i != 0:
                provider = test_params["provider"]
                if provider in command_params:
                    for param in test_params:
                        if (
                            param
                            not in command_params[provider]["QueryParams"]["fields"]
                            and param not in command_params["openbb"]["QueryParams"]["fields"]  # type: ignore
                            and param != "provider"
                        ):
                            wrong_params.append(
                                f"Wrong param {param} for provider {provider} in function {function}"
                            )
            elif isinstance(command_params, dict):
                providers = list(command_params.keys())
                providers.remove("openbb")
                for param in test_params:
                    is_wrong_param = True
                    for provider in providers:
                        if (
                            param in command_params[provider]["QueryParams"]["fields"]
                            or param
                            in command_params["openbb"]["QueryParams"]["fields"]
                            or param == "provider"
                        ):
                            is_wrong_param = False
                            break

                    if is_wrong_param:
                        wrong_params.append(
                            f"Wrong param {param} in function {function}"
                        )

    else:
        for test_params in function_params:
            if isinstance(command_params, list):
                try:
                    iter_commands_params = command_params[0][0]
                except KeyError:
                    iter_commands_params = command_params[0]  # type: ignore

                if isinstance(test_params, dict):
                    param_keys = test_params.keys()
                elif isinstance(test_params, tuple) and all(
                    isinstance(item, dict) for item in test_params
                ):
                    param_keys = [key for item in test_params for key in item]
                else:
                    continue  # Skip this iteration if test_params is neither a dict nor a tuple of dicts

                for key in param_keys:
                    if key not in iter_commands_params and key != "return":
                        wrong_params.append(f"Wrong param {key} in function {function}")
    return wrong_params