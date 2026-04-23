def check_router_model_functions_signature() -> list[str]:
    """Check if the router model functions have the correct signature."""
    expected_args = ["cc", "provider_choices", "standard_params", "extra_params"]
    expected_return_type = "OBBject"
    missing_args: list[str] = []
    missing_return_type: list[str] = []

    routers = collect_routers("extensions")
    loaded_routers = import_routers(routers)
    router_functions = collect_router_functions(loaded_routers)

    for router_name, functions in router_functions.items():
        for function in functions:
            decorator = find_decorator(
                os.path.join(*router_name.split(".")) + ".py",
                function.__name__,
            )
            if decorator:
                if "POST" in decorator or "GET" in decorator:
                    continue
                args = list(function.__code__.co_varnames)

                if (
                    args
                    and not all(arg in args for arg in expected_args)
                    and "model" in decorator
                ):
                    missing_args.append(
                        f"{function.__name__} in {router_name} missing expected args: {expected_args}"
                    )
                if expected_return_type not in str(function.__annotations__["return"]):
                    missing_return_type.append(
                        f"{function.__name__} in {router_name} "
                        f"doesn't have the expected return type: {expected_return_type}"
                    )

    return missing_args + missing_return_type