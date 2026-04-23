def test_put_integration_validation(
    aws_client, account_id, region_name, create_rest_apigw, snapshot, partition
):
    snapshot.add_transformers_list(
        [
            snapshot.transform.key_value("cacheNamespace"),
        ]
    )

    api_id, _, root_id = create_rest_apigw(name="test-apigw")

    aws_client.apigateway.put_method(
        restApiId=api_id, resourceId=root_id, httpMethod="GET", authorizationType="NONE"
    )
    aws_client.apigateway.put_method_response(
        restApiId=api_id, resourceId=root_id, httpMethod="GET", statusCode="200"
    )

    http_types = ["HTTP", "HTTP_PROXY"]
    aws_types = ["AWS", "AWS_PROXY"]
    types_requiring_integration_method = http_types + ["AWS"]
    types_not_requiring_integration_method = ["MOCK"]

    for _type in types_requiring_integration_method:
        # Ensure that integrations of these types fail if no integrationHttpMethod is provided
        with pytest.raises(ClientError) as ex:
            aws_client.apigateway.put_integration(
                restApiId=api_id,
                resourceId=root_id,
                httpMethod="GET",
                type=_type,
                uri="http://example.com",
            )
        snapshot.match(f"required-integration-method-{_type}", ex.value.response)

    for _type in types_not_requiring_integration_method:
        # Ensure that integrations of these types do not need the integrationHttpMethod
        response = aws_client.apigateway.put_integration(
            restApiId=api_id,
            resourceId=root_id,
            httpMethod="GET",
            type=_type,
            uri="http://example.com",
        )
        snapshot.match(f"not-required-integration-method-{_type}", response)

    for _type in http_types:
        # Ensure that it works fine when providing the integrationHttpMethod-argument
        response = aws_client.apigateway.put_integration(
            restApiId=api_id,
            resourceId=root_id,
            httpMethod="GET",
            type=_type,
            uri="http://example.com",
            integrationHttpMethod="POST",
        )
        snapshot.match(f"http-method-{_type}", response)

    for _type in ["AWS"]:
        # Ensure that it works fine when providing the integrationHttpMethod + credentials
        response = aws_client.apigateway.put_integration(
            restApiId=api_id,
            resourceId=root_id,
            credentials=f"arn:{partition}:iam::{account_id}:role/service-role/testfunction-role-oe783psq",
            httpMethod="GET",
            type=_type,
            uri=f"arn:{partition}:apigateway:{region_name}:s3:path/b/k",
            integrationHttpMethod="POST",
        )
        snapshot.match(f"aws-integration-{_type}", response)

    for _type in aws_types:
        # Ensure that credentials are not required when URI points to a Lambda stream
        response = aws_client.apigateway.put_integration(
            restApiId=api_id,
            resourceId=root_id,
            httpMethod="GET",
            type=_type,
            uri=f"arn:{partition}:apigateway:{region_name}:lambda:path/2015-03-31/functions/arn:{partition}:lambda:{region_name}:{account_id}:function:MyLambda/invocations",
            integrationHttpMethod="POST",
        )
        snapshot.match(f"aws-integration-type-{_type}", response)

    for _type in ["AWS_PROXY"]:
        # Ensure that aws_proxy does not support S3
        with pytest.raises(ClientError) as ex:
            aws_client.apigateway.put_integration(
                restApiId=api_id,
                resourceId=root_id,
                credentials=f"arn:{partition}:iam::{account_id}:role/service-role/testfunction-role-oe783psq",
                httpMethod="GET",
                type=_type,
                uri=f"arn:{partition}:apigateway:{region_name}:s3:path/b/k",
                integrationHttpMethod="POST",
            )
        snapshot.match(f"no-s3-support-{_type}", ex.value.response)

    for _type in http_types:
        # Ensure that the URI is valid HTTP
        with pytest.raises(ClientError) as ex:
            aws_client.apigateway.put_integration(
                restApiId=api_id,
                resourceId=root_id,
                httpMethod="GET",
                type=_type,
                uri="non-valid-http",
                integrationHttpMethod="POST",
            )
        snapshot.match(f"invalid-uri-{_type}", ex.value.response)

    # Ensure that the URI is an ARN
    with pytest.raises(ClientError) as ex:
        aws_client.apigateway.put_integration(
            restApiId=api_id,
            resourceId=root_id,
            httpMethod="GET",
            type="AWS",
            uri="non-valid-arn",
            integrationHttpMethod="POST",
        )
    snapshot.match("invalid-uri-not-an-arn", ex.value.response)

    # Ensure that the URI is a valid ARN
    with pytest.raises(ClientError) as ex:
        aws_client.apigateway.put_integration(
            restApiId=api_id,
            resourceId=root_id,
            httpMethod="GET",
            type="AWS",
            uri=f"arn:{partition}:iam::0000000000:role/service-role/asdf",
            integrationHttpMethod="POST",
        )
    snapshot.match("invalid-uri-invalid-arn", ex.value.response)