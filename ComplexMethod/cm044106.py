def check_missing_integration_tests(test_type: Literal["api", "python"]) -> list[str]:
    """Check if all endpoints have integration tests."""
    cm = CommandMap(coverage_sep=".")
    routes = [route[1:].replace("/", "_") for route in cm.map]
    missing_integration_tests: list[str] = []

    if test_type == "api":
        functions = get_module_functions(get_integration_tests(test_type="api"))
    else:
        functions = get_module_functions(get_integration_tests(test_type="python"))

    tested_functions = [
        function.replace("test_", "", 1)
        for function in functions
        if function.startswith("test_")
    ]

    for route in routes:
        if route not in tested_functions:
            # TODO: See how to handle edge cases that are excluded from the schema
            # on purpose. This is currently on the econometrics router.
            if (
                test_type == "api"
                and "econometrics" in route
                or route.endswith(".json")
            ):
                continue
            missing_integration_tests.append(
                f"Missing {test_type} integration test for route {route}"
            )

    return missing_integration_tests