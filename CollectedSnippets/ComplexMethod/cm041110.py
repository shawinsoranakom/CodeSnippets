def is_api_key_required(path_payload: dict) -> bool:
        # TODO: consolidate and refactor with `create_authorizer`, duplicate logic for now
        if not (security_schemes := path_payload.get("security")):
            return False

        for security_scheme in security_schemes:
            for security_scheme_name in security_scheme.keys():
                # $.securityDefinitions is Swagger 2.0
                # $.components.SecuritySchemes is OpenAPI 3.0
                security_definitions = resolved_schema.get(
                    "securityDefinitions"
                ) or resolved_schema.get("components", {}).get("securitySchemes", {})
                if security_scheme_name in security_definitions:
                    security_config = security_definitions.get(security_scheme_name)
                    if (
                        OpenAPIExt.AUTHORIZER not in security_config
                        and security_config.get("type") == "apiKey"
                        and security_config.get("name", "").lower() == "x-api-key"
                    ):
                        return True
        return False