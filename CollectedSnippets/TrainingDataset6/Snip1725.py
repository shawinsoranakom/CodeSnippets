def get_fields_from_routes(
    routes: Sequence[BaseRoute],
) -> list[ModelField]:
    body_fields_from_routes: list[ModelField] = []
    responses_from_routes: list[ModelField] = []
    request_fields_from_routes: list[ModelField] = []
    callback_flat_models: list[ModelField] = []
    for route in routes:
        if not isinstance(route, routing.APIRoute):
            continue
        if route.include_in_schema:
            if route.body_field:
                assert isinstance(route.body_field, ModelField), (
                    "A request body must be a Pydantic Field"
                )
                body_fields_from_routes.append(route.body_field)
            if route.response_field:
                responses_from_routes.append(route.response_field)
            if route.response_fields:
                responses_from_routes.extend(route.response_fields.values())
            if route.stream_item_field:
                responses_from_routes.append(route.stream_item_field)
            if route.callbacks:
                callback_flat_models.extend(get_fields_from_routes(route.callbacks))
            params = get_flat_params(route.dependant)
            request_fields_from_routes.extend(params)

    flat_models = callback_flat_models + list(
        body_fields_from_routes + responses_from_routes + request_fields_from_routes
    )
    return flat_models