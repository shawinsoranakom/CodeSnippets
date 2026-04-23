def find_missing_router_function_models(
    router_functions: dict, pi_map: dict
) -> list[str]:
    """Find the missing models in the router functions."""
    missing_models: list[str] = []
    for router_name, functions in router_functions.items():
        for function in functions:
            decorator = find_decorator(
                os.path.join(*router_name.split(".")) + ".py",
                function.__name__,
            )
            if (
                decorator
                and "model" in decorator
                and "POST" not in decorator
                and "GET" not in decorator
            ):
                if (
                    returns := str(function.__annotations__.get("return"))
                ) and returns.rsplit(".", maxsplit=1)[-1].startswith("OBBject"):
                    model = returns.rsplit("_", maxsplit=1)[-1].replace("'>", "")
                else:
                    model = decorator.split("model=")[1].split(",")[0].strip('"')
                if (
                    model not in pi_map
                    and "POST" not in decorator
                    and "GET" not in decorator
                ):
                    missing_models.append(
                        f"{function.__name__} in {router_name} model doesn't exist in the provider interface map."
                    )

    return missing_models