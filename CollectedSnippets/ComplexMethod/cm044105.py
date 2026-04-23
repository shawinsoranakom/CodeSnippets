def check_integration_tests(
    functions: dict[str, Any],
    check_function: Callable[
        [
            dict[str, dict[str, dict]] | list[tuple[dict[str, str], str]],
            list[dict],
            str,
            bool,
        ],
        list[str],
    ],
) -> list[str]:
    """Check if there are any missing items for integration tests."""
    pi = ProviderInterface()
    provider_interface_map = pi.map
    cm = CommandMap(coverage_sep=".")

    function_params: list[dict] = []
    all_missing_items: list[str] = []
    used_functions: list[str] = []

    for command, model in cm.commands_model.items():
        for function in functions:
            if command[1:].replace(".", "_") == function.replace("test_", ""):
                command_params: dict[str, dict[str, dict]] = provider_interface_map[
                    model
                ]
                try:
                    function_params = (
                        functions[function].pytestmark[1].args[1]
                        if len(functions[function].pytestmark[1].args) > 1
                        else []
                    )
                except IndexError:
                    # Another decorator is below the parametrize decorator
                    function_params = functions[function].pytestmark[2].args[1]
                missing_items = check_function(
                    command_params, function_params, function, False
                )
                all_missing_items.extend(missing_items)
                used_functions.append(function)

    # the processing commands are the ones that are left
    processing_functions = [
        function for function in functions if function not in used_functions
    ]

    for route, _ in cm.map.items():
        for function in processing_functions:
            if route.replace("/", "_")[1:] == function.replace("test_", ""):
                sig = inspect.signature(cm.map[route])
                param_names = list(sig.parameters.keys()) + ["return"]
                processing_command_params = [
                    {k: "" for k in param_names}
                ]
                if (
                    not processing_command_params
                    or len(functions[function].pytestmark) < 2
                ):
                    # If there are no params, we can skip this function
                    continue
                try:
                    function_params = functions[function].pytestmark[1].args[1]
                except IndexError:
                    # Another decorator is below the parametrize decorator
                    function_params = functions[function].pytestmark[2].args[1]

                missing_items = check_function(
                    processing_command_params,
                    function_params,
                    function,
                    True,  # type: ignore
                )

                # if "chart" is in missing_items, remove it
                if "chart" in missing_items:
                    missing_items.remove("chart")

                all_missing_items.extend(missing_items)

    return all_missing_items