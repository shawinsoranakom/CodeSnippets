def get_query_schema_for_widget(
    openapi_json: dict, command_route: str, single_provider: str | None = None
) -> tuple[list[dict], bool]:
    """
    Extract the query schema for a widget.

    Parameters
    ----------
    openapi_json : dict
        The OpenAPI specification as a dictionary.
    command_route : str
        The route of the command in the OpenAPI specification.
    single_provider : str | None
        If set, extract provider-specific descriptions/defaults only for this provider.

    Returns
    -------
    Tuple[List[Dict], bool]
        A tuple containing the list of processed parameters and a boolean indicating if a chart is present.
    """
    has_chart = False
    command = openapi_json["paths"][command_route]
    command = command.get("get", {})
    params = command.get("parameters", [])
    route_params: list[dict] = []
    providers: list[str] = extract_providers(params)

    if not providers:
        providers = ["custom"]

    for param in params:
        if param["name"] in ["sort", "order"]:
            continue
        if param["name"] == "chart":
            has_chart = True
            continue

        p = process_parameter(param, providers, single_provider)
        if "show" not in p:
            p["show"] = True

        if not p.get("exclude") and not p.get("x-widget_config", {}).get("exclude"):
            route_params.append(p)

    return route_params, has_chart