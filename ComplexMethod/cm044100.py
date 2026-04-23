def write_commands_integration_tests(
    command_map: CommandMap,
    provider_interface: ProviderInterface,
    api_paths: dict[str, dict],
) -> list[str]:
    """Write the commands integration tests."""
    commands_not_found = []

    cm_map = command_map.map
    cm_models = command_map.commands_model
    provider_interface_map = provider_interface.map

    for route in cm_map:
        http_method = get_http_method(api_paths, f"/api/v1{route}")

        menu = route.split("/")[1]
        path = os.path.join(
            "openbb_platform", "extensions", menu, "integration", f"test_{menu}_api.py"
        )
        if not os.path.exists(path):
            write_init_test_template(http_method=http_method, path=path)  # type: ignore

        if not http_method:
            commands_not_found.append(route)
        else:
            sig = _inspect.signature(cm_map[route])
            param_names = [k for k in sig.parameters.keys() if k not in ("cc", "return")]

            params_list = (
                [{k: "" for k in param_names}]
                if http_method == "post"
                else get_test_params(
                    model_name=cm_models[route],  # type: ignore
                    provider_interface_map=provider_interface_map,
                )
            )

            if not test_exists(route=route, path=path):
                write_test_w_template(
                    http_method=http_method,  # type: ignore
                    params_list=params_list,  # type: ignore
                    route=route,
                    path=path,
                )

    return commands_not_found