def check_router_command_examples() -> list[str]:
    """Check if the router command examples satisfy criteria."""
    general_violation: list[str] = []
    api_example_violation: list[str] = []
    python_example_violation: list[str] = []

    routers = collect_routers("extensions")
    loaded_routers = import_routers(routers)
    router_functions = collect_router_functions(loaded_routers)

    for router_name, functions in router_functions.items():
        for function in functions:
            if (
                "basemodel_to_df" in function.__name__
                or "router" not in function.__module__
            ):
                continue
            decorator = find_decorator(
                os.path.join(*router_name.split(".")) + ".py",
                function.__name__,
            )
            if decorator:
                decorator_details = get_decorator_details(function)
                if decorator_details and decorator_details.name == "router.command":
                    keywords = decorator_details.kwargs or {}
                    examples = keywords.get("examples", [])
                    # General checks
                    general_violation += check_general(
                        keywords, examples, router_name, function
                    )
                    if examples:
                        # API example checks
                        model = keywords.get("model", None)
                        api_example_violation += check_api(
                            examples, router_name, model, function
                        )

    return general_violation + api_example_violation + python_example_violation