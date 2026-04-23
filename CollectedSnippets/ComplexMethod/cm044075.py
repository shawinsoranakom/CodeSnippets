def get_data_schema_for_widget(openapi_json, operation_id, route: str | None = None):
    """
    Get the data schema for a widget based on its operationId.

    Args:
        openapi (dict): The OpenAPI specification as a dictionary.
        operation_id (str): The operationId of the widget.

    Returns:
        dict: The schema dictionary for the widget's data.
    """
    # Find the route and method for the given operationId

    if not route:
        for path, methods in openapi_json["paths"].items():
            for _method, details in methods.items():
                if details.get("operationId") == operation_id:
                    route = path
                    break

    _route = openapi_json["paths"].get(route, {}).get("get", {})

    if (
        schema := _route.get("responses", {})
        .get("200", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    ):
        # Get the reference to the schema from the successful response

        if "items" in schema:
            response_ref = schema["items"].get("$ref")
        else:
            response_ref = schema.get("$ref") or _route["responses"]["200"]["content"][
                "application/json"
            ].get("schema")

        if isinstance(response_ref, dict) and "type" in response_ref:
            response_ref = response_ref["type"]

        if response_ref and isinstance(response_ref, str):
            # Extract the schema name from the reference
            schema_name = response_ref.split("/")[-1]
            # Fetch and return the schema from components
            if schema_name and schema_name in openapi_json.get("components", {}).get(
                "schemas", {}
            ):
                props = openapi_json["components"]["schemas"][schema_name].get(
                    "properties", {}
                )
                if props and "results" in props:
                    return props["results"]

            return openapi_json["components"]["schemas"].get(schema_name, schema_name)
    # Return None if the schema is not found
    return None