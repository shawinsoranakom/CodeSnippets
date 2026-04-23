def check_outdated_integration_tests(test_type: Literal["api", "python"]) -> list[str]:
    """Check if there are any outdated integration tests."""
    cm = CommandMap(coverage_sep=".")
    routes = [route[1:].replace("/", "_") for route in cm.map]
    outdated_integration_tests: list[str] = []

    if test_type == "api":
        functions = get_module_functions(get_integration_tests(test_type="api"))
    else:
        functions = get_module_functions(get_integration_tests(test_type="python"))

    for function, f_callable in functions.items():
        if function.startswith("test_"):
            route = function.replace("test_", "", 1)
            try:
                if f_callable.pytestmark[1].name != "skip":
                    args = f_callable.pytestmark[1].args[1]
                else:
                    continue
            except IndexError:
                continue
            if route not in routes and len(args) > 0:
                # If it doesn't have any args it is because it is not installed.
                outdated_integration_tests.append(
                    f"Outdated {test_type} integration test for route {route}"
                )

    return outdated_integration_tests