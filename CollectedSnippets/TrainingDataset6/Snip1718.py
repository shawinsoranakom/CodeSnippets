def get_openapi_security_definitions(
    flat_dependant: Dependant,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    security_definitions = {}
    # Use a dict to merge scopes for same security scheme
    operation_security_dict: dict[str, list[str]] = {}
    for security_dependency in flat_dependant._security_dependencies:
        security_definition = jsonable_encoder(
            security_dependency._security_scheme.model,
            by_alias=True,
            exclude_none=True,
        )
        security_name = security_dependency._security_scheme.scheme_name
        security_definitions[security_name] = security_definition
        # Merge scopes for the same security scheme
        if security_name not in operation_security_dict:
            operation_security_dict[security_name] = []
        for scope in security_dependency.oauth_scopes or []:
            if scope not in operation_security_dict[security_name]:
                operation_security_dict[security_name].append(scope)
    operation_security = [
        {name: scopes} for name, scopes in operation_security_dict.items()
    ]
    return security_definitions, operation_security