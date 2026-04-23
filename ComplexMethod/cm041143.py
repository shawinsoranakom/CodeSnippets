def invoke_rest_api_integration_backend(invocation_context: ApiInvocationContext):
    # define local aliases from invocation context
    method = invocation_context.method
    headers = invocation_context.headers
    integration = invocation_context.integration
    integration_type_orig = integration.get("type") or integration.get("integrationType") or ""
    integration_type = integration_type_orig.upper()
    integration_method = integration.get("httpMethod")
    uri = integration.get("uri") or integration.get("integrationUri") or ""

    if (re.match(f"{ARN_PARTITION_REGEX}:apigateway:", uri) and ":lambda:path" in uri) or re.match(
        f"{ARN_PARTITION_REGEX}:lambda", uri
    ):
        invocation_context.context = get_event_request_context(invocation_context)
        if integration_type == "AWS_PROXY":
            return LambdaProxyIntegration().invoke(invocation_context)
        elif integration_type == "AWS":
            return LambdaIntegration().invoke(invocation_context)

    elif integration_type == "AWS":
        if "kinesis:action/" in uri:
            return KinesisIntegration().invoke(invocation_context)

        if "states:action/" in uri:
            return StepFunctionIntegration().invoke(invocation_context)

        if ":dynamodb:action" in uri:
            return DynamoDBIntegration().invoke(invocation_context)

        if "s3:path/" in uri or "s3:action/" in uri:
            return S3Integration().invoke(invocation_context)

        if integration_method == "POST" and ":sqs:path" in uri:
            return SQSIntegration().invoke(invocation_context)

        if method == "POST" and ":sns:path" in uri:
            return SNSIntegration().invoke(invocation_context)

        if (
            method == "POST"
            and re.match(f"{ARN_PARTITION_REGEX}:apigateway:", uri)
            and "events:action/PutEvents" in uri
        ):
            return EventBridgeIntegration().invoke(invocation_context)

    elif integration_type in ["HTTP_PROXY", "HTTP"]:
        return HTTPIntegration().invoke(invocation_context)

    elif integration_type == "MOCK":
        return MockIntegration().invoke(invocation_context)

    if method == "OPTIONS":
        # fall back to returning CORS headers if this is an OPTIONS request
        return get_cors_response(headers)

    raise Exception(
        f'API Gateway integration type "{integration_type}", method "{method}", URI "{uri}" not yet implemented'
    )