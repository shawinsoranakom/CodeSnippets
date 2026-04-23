def post_query_schema_for_widget(
    openapi_json,
    operation_id,
    route: str | None = None,
    target_schema: str | None = None,
):
    """
    Get the POST query schema for a widget based on its operationId.

    Args:
        openapi (dict): The OpenAPI specification as a dictionary.
        operation_id (str): The operationId of the widget.
        route (str): The route of the widget, if any.
        target_schema (str): The target schema to extract, if any.

    Returns:
        list[dict]: The schema dictionary for the widget's data.
    """

    new_params: dict = {}

    def set_param(k, v):
        """Set the parameter."""
        nonlocal new_params

        new_params[k] = {}
        new_params[k]["name"] = k
        new_params[k]["type"] = (
            "text"
            if v.get("type") == "object"
            else "date" if "date" in v.get("format", "") else v.get("type", "text")
        )
        new_params[k]["title"] = v.get("title")
        new_params[k]["description"] = v.get("description")
        new_params[k]["default"] = v.get("default")
        new_params[k]["x-widget_config"] = v.get("x-widget_config", {})
        choices: list = (
            [{"label": c, "value": c} for c in v.get("choices", []) if c]
            if v.get("choices")
            else []
        )

        if isinstance(v, dict) and "anyOf" in v:
            param_types = []
            for item in v["anyOf"]:
                if "type" in item and item.get("type") != "null":
                    param_types.append(item["type"])
                if "enum" in item:
                    choices.extend({"label": c, "value": c} for c in item["enum"])

            if param_types:
                new_params[k]["type"] = (
                    "number"
                    if "number" in param_types
                    or "integer" in param_types
                    and "string" not in param_types
                    and "date" not in param_types
                    else (
                        "date"
                        if any(
                            "date" in sub_prop.get("format", "")
                            for sub_prop in v["anyOf"]
                            if isinstance(sub_prop, dict)
                        )
                        else "text"
                    )
                )
            else:
                new_params[k]["type"] = (
                    "text"
                    if v.get("type") == "object"
                    else (
                        "date"
                        if "date" in v.get("format", "")
                        else v.get("type", "text")
                    )
                )
        elif isinstance(v, dict) and "enum" in v:
            choices.extend({"label": c, "value": c} for c in v["enum"] if c)

        if choices:
            new_params[k]["options"] = {"custom": choices}

    if not route:
        for path, methods in openapi_json["paths"].items():
            for _method, details in methods.items():
                if details.get("operationId") == operation_id:
                    route = path
                    break

    _route = openapi_json["paths"].get(route, {}).get("post", {})

    if (
        schema := _route.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    ):
        # Get the reference to the schema for the request body.

        title = schema.get("title")
        providers: list[str] = []

        if title and title in schema:
            providers = [title]
        elif title and "," in title:
            providers = title.split(",")
        else:
            providers = ["Custom"]

        if params := _route.get("parameters"):
            if isinstance(params, list):
                for _param in params:
                    set_param(_param["name"], _param["schema"])
            elif isinstance(params, dict):
                for k, v in params.items():
                    set_param(k, v)

        if "items" in schema or "$ref" in schema:
            param_ref = (
                schema["items"].get("$ref")
                if "items" in schema
                else schema.get("$ref") or schema
            )

            if isinstance(param_ref, dict) and "type" in param_ref:
                param_ref = param_ref["type"]

            if param_ref and isinstance(param_ref, str):
                # Extract the schema name from the reference
                schema_name = param_ref.split("/")[-1]
                schema = openapi_json["components"]["schemas"].get(
                    schema_name, schema_name
                )
                props = {} if isinstance(schema, str) else schema.get("properties", {})

                for k, v in props.items():
                    if target_schema and target_schema != k:
                        continue
                    if nested_schema := v.get("$ref"):
                        nested_schema_name = nested_schema.split("/")[-1]
                        nested_schema = openapi_json["components"]["schemas"].get(
                            nested_schema_name, {}
                        )
                        for nested_k, nested_v in nested_schema.get(
                            "properties", {}
                        ).items():
                            set_param(nested_k, nested_v)

                    else:
                        set_param(k, v)

                route_params: list[dict] = []

                for new_param_values in new_params.values():
                    _new_values = new_param_values.copy()
                    p = process_parameter(_new_values, providers)
                    if not p.get("exclude") and not p.get("x-widget_config", {}).get(
                        "exclude"
                    ):
                        route_params.append(p)

                return route_params
        if "anyOf" in _route or "anyOf" in schema:
            any_of_schema = (
                schema.get("anyOf", [])
                if "anyOf" in schema
                else _route.get("anyOf", [])
            )
            for item in any_of_schema:
                # If item is a $ref, resolve it
                if "$ref" in item:
                    ref_name = item["$ref"].split("/")[-1]
                    ref_schema = openapi_json["components"]["schemas"].get(ref_name, {})
                    if "properties" in ref_schema:
                        for k, v in ref_schema["properties"].items():
                            if target_schema and target_schema != k:
                                continue
                            set_param(k, v)
                # If item has properties directly
                elif "properties" in item:
                    for k, v in item["properties"].items():
                        if target_schema and target_schema != k:
                            continue
                        set_param(k, v)

            route_params = []

            for new_param_values in new_params.values():
                _new_values = new_param_values.copy()
                p = process_parameter(_new_values, providers)
                if not p.get("exclude") and not p.get("x-widget_config", {}).get(
                    "exclude"
                ):
                    route_params.append(p)

            return route_params

    # Return None if the schema is not found
    return None