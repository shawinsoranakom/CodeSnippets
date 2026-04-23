def _factory(
            integration: IntegrationType,
            integration_uri: str,
            role_arn: str,
            special_cases: list[RequestParameterRoute],
        ):
            request_parameters = copy.deepcopy(REQUEST_PARAMETERS)

            stage = "test"
            # Creating as a regional endpoint to prevent the cloudfront header from modifying the apigw headers
            # TODO test with a "EDGE" configuration
            apigw, _, root_id = create_rest_apigw(endpointConfiguration={"types": ["REGIONAL"]})

            # Base test with no parameter mapping
            no_param_resource = aws_client.apigateway.create_resource(
                restApiId=apigw, parentId=root_id, pathPart="no-param"
            )["id"]
            # Full test with all the mentioned headers mapped except for the special cases below
            full_resource = aws_client.apigateway.create_resource(
                restApiId=apigw, parentId=root_id, pathPart="full"
            )["id"]

            for special_case in special_cases:
                resource = aws_client.apigateway.create_resource(
                    restApiId=apigw, parentId=root_id, pathPart=special_case["path"]
                )
                special_case["resource_id"] = resource["id"]
                special_case["parameter_mapping"] = request_parameters.pop(
                    special_case["request_parameter"], "''"
                )

            for resource_id in [
                no_param_resource,
                full_resource,
                *[special_case["resource_id"] for special_case in special_cases],
            ]:
                aws_client.apigateway.put_method(
                    restApiId=apigw,
                    resourceId=resource_id,
                    httpMethod="GET",
                    authorizationType="NONE",
                    requestParameters={
                        f"method.request.header.{header}": False for header in HEADERS
                    },
                )
                aws_client.apigateway.put_method_response(
                    restApiId=apigw,
                    resourceId=resource_id,
                    httpMethod="GET",
                    statusCode="200",
                    responseParameters={
                        f"method.response.header.{header}": True for header in HEADERS
                    },
                )

            # No param resource
            aws_client.apigateway.put_integration(
                restApiId=apigw,
                resourceId=no_param_resource,
                httpMethod="GET",
                type=integration,
                uri=integration_uri,
                integrationHttpMethod="POST",
                credentials=role_arn,
            )
            aws_client.apigateway.put_integration_response(
                restApiId=apigw, resourceId=no_param_resource, httpMethod="GET", statusCode="200"
            )

            # Full mapping
            request_template = (
                "{"
                + ",".join([f'"{header}": "$input.params(\'{header}\')"' for header in HEADERS])
                + "}"
            )
            aws_client.apigateway.put_integration(
                restApiId=apigw,
                resourceId=full_resource,
                httpMethod="GET",
                type=integration,
                integrationHttpMethod="POST",
                uri=integration_uri,
                credentials=role_arn,
                requestParameters=request_parameters,
                requestTemplates={APPLICATION_JSON: request_template},
            )
            aws_client.apigateway.put_integration_response(
                restApiId=apigw,
                resourceId=full_resource,
                httpMethod="GET",
                statusCode="200",
                responseParameters={
                    f"method.response.header.{header}": f"'response_param_{header}'"
                    for header in HEADERS
                },
            )
            for special_case in special_cases:
                aws_client.apigateway.put_integration(
                    restApiId=apigw,
                    resourceId=special_case["resource_id"],
                    httpMethod="GET",
                    type=integration,
                    integrationHttpMethod="POST",
                    uri=integration_uri,
                    credentials=role_arn,
                    requestParameters={
                        special_case["request_parameter"]: special_case["parameter_mapping"]
                    },
                )
                aws_client.apigateway.put_integration_response(
                    restApiId=apigw,
                    resourceId=special_case["resource_id"],
                    httpMethod="GET",
                    statusCode="200",
                )

            aws_client.apigateway.create_deployment(restApiId=apigw, stageName=stage)
            invoke_url = api_invoke_url(api_id=apigw, stage=stage, path="")

            return apigw, invoke_url