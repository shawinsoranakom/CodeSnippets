def create_authorizers(security_schemes: dict) -> None:
        for security_scheme_name, security_config in security_schemes.items():
            aws_apigateway_authorizer = security_config.get(OpenAPIExt.AUTHORIZER, {})
            if not aws_apigateway_authorizer:
                continue

            if security_scheme_name in authorizers:
                continue

            authorizer_type = aws_apigateway_authorizer.get("type", "").upper()
            # TODO: do we need validation of resources here?
            authorizer = Authorizer(
                id=ApigwAuthorizerIdentifier(
                    account_id, region_name, security_scheme_name
                ).generate(),
                name=security_scheme_name,
                type=authorizer_type,
                authorizerResultTtlInSeconds=aws_apigateway_authorizer.get(
                    "authorizerResultTtlInSeconds", None
                ),
            )
            if provider_arns := aws_apigateway_authorizer.get("providerARNs"):
                authorizer["providerARNs"] = provider_arns
            if auth_type := security_config.get(OpenAPIExt.AUTHTYPE):
                authorizer["authType"] = auth_type
            if authorizer_uri := aws_apigateway_authorizer.get("authorizerUri"):
                authorizer["authorizerUri"] = authorizer_uri
            if authorizer_credentials := aws_apigateway_authorizer.get("authorizerCredentials"):
                authorizer["authorizerCredentials"] = authorizer_credentials
            if authorizer_type in ("TOKEN", "COGNITO_USER_POOLS"):
                header_name = security_config.get("name")
                authorizer["identitySource"] = f"method.request.header.{header_name}"
            elif identity_source := aws_apigateway_authorizer.get("identitySource"):
                # https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-swagger-extensions-authorizer.html
                # Applicable for the authorizer of the request and jwt type only
                authorizer["identitySource"] = identity_source
            if identity_validation_expression := aws_apigateway_authorizer.get(
                "identityValidationExpression"
            ):
                authorizer["identityValidationExpression"] = identity_validation_expression

            rest_api_container.authorizers[authorizer["id"]] = authorizer

            authorizers[security_scheme_name] = authorizer