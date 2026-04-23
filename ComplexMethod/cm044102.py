def check_missing_providers(
    command_params: dict[str, dict[str, dict]] | list[tuple[dict[str, str], str]],
    function_params: list[dict],
    function,
    processing: bool = False,
) -> list[str]:
    """Check if there are any missing providers for a command."""
    if processing or not isinstance(command_params, dict):
        return []

    missing_providers: list[str] = []
    providers = list(command_params.keys())
    providers.remove("openbb")
    if not providers:
        return []

    for test_params in function_params:
        provider = test_params.get("provider", None)
        if provider:
            try:  # noqa
                providers.remove(provider)
            except ValueError:
                pass

    if providers:
        # if there is only one provider left and the length of the
        #  test_params is 1, we can ignore because it is picked up by default
        if len(providers) == 1 and len(function_params) == 1:
            pass
        else:
            missing_providers.append(
                f"Missing providers for {function}: {providers}  --? {function_params}"
            )

    return missing_providers