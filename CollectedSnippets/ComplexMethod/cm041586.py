def test_create_execute_api_vpc_endpoint(
    create_rest_api_with_integration,
    dynamodb_create_table,
    create_vpc_endpoint,
    default_vpc,
    create_lambda_function,
    ec2_create_security_group,
    snapshot,
    aws_client,
    region_name,
):
    poll_sleep = 5 if is_aws_cloud() else 1
    # TODO: create a re-usable ec2_api() transformer
    snapshot.add_transformers_list(
        [
            snapshot.transform.key_value("DnsName"),
            snapshot.transform.key_value("GroupId"),
            snapshot.transform.key_value("GroupName"),
            snapshot.transform.key_value("SubnetIds"),
            snapshot.transform.key_value("VpcId"),
            snapshot.transform.key_value("VpcEndpointId"),
            snapshot.transform.key_value("HostedZoneId"),
            *snapshot.transform.apigateway_api(),
        ]
    )

    # create table
    table = dynamodb_create_table()["TableDescription"]
    table_name = table["TableName"]

    # insert items
    item_ids = ("test", "test2", "test 3")
    for item_id in item_ids:
        aws_client.dynamodb.put_item(TableName=table_name, Item={"id": {"S": item_id}})

    # construct request mapping template
    request_templates = {APPLICATION_JSON: json.dumps({"TableName": table_name})}

    # deploy REST API with integration
    integration_uri = f"arn:aws:apigateway:{region_name}:dynamodb:action/Scan"
    api_id = create_rest_api_with_integration(
        integration_uri=integration_uri,
        req_templates=request_templates,
        integration_type="AWS",
    )

    # get service names
    service_name = f"com.amazonaws.{region_name}.execute-api"
    service_names = aws_client.ec2.describe_vpc_endpoint_services()["ServiceNames"]
    assert service_name in service_names

    # create security group
    vpc_id = default_vpc["VpcId"]
    security_group = ec2_create_security_group(
        VpcId=vpc_id,
        Description="Test SG for API GW",
        GroupName=f"test-sg-{short_uid()}",
        ports=[443],
    )
    security_group = security_group["GroupId"]
    subnets = aws_client.ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])
    subnets = [sub["SubnetId"] for sub in subnets["Subnets"]]

    # get or create execute-api VPC endpoint
    endpoints = aws_client.ec2.describe_vpc_endpoints(MaxResults=1000)["VpcEndpoints"]
    matching = [ep for ep in endpoints if ep["ServiceName"] == service_name]
    if matching:
        endpoint_id = matching[0]["VpcEndpointId"]
    else:
        result = create_vpc_endpoint(
            ServiceName=service_name,
            VpcEndpointType="Interface",
            SubnetIds=subnets,
            SecurityGroupIds=[security_group],
        )
        endpoint_id = result["VpcEndpointId"]

    # wait until VPC endpoint is in state "available"
    def _check_available():
        result = aws_client.ec2.describe_vpc_endpoints(VpcEndpointIds=[endpoint_id])
        _endpoint_details = result["VpcEndpoints"][0]
        # may have multiple entries in AWS
        _endpoint_details["DnsEntries"] = _endpoint_details["DnsEntries"][:1]
        _endpoint_details.pop("SubnetIds", None)
        _endpoint_details.pop("NetworkInterfaceIds", None)
        assert _endpoint_details["State"] == "available"
        snapshot.match("endpoint-details", _endpoint_details)
        return _endpoint_details

    endpoint_details: VpcEndpoint = retry(_check_available, retries=30, sleep=poll_sleep)

    # update API with VPC endpoint
    patches = [
        {"op": "replace", "path": "/endpointConfiguration/types/EDGE", "value": "PRIVATE"},
        {"op": "add", "path": "/endpointConfiguration/vpcEndpointIds", "value": endpoint_id},
    ]
    aws_client.apigateway.update_rest_api(restApiId=api_id, patchOperations=patches)

    # create Lambda that invokes API via VPC endpoint (required as the endpoint is only accessible within the VPC)
    lambda_code = textwrap.dedent(
        """
    def handler(event, context):
        import requests
        url = event["url"]
        headers = event["headers"]

        result = requests.post(url, headers=headers)
        return {"content": result.content.decode("utf-8"), "code": result.status_code}
    """
    )
    func_name = f"test-{short_uid()}"
    vpc_config = {
        "SubnetIds": subnets,
        "SecurityGroupIds": [security_group],
    }
    create_lambda_function(
        func_name=func_name,
        handler_file=lambda_code,
        libs=TEST_LAMBDA_LIBS,
        timeout=10,
        VpcConfig=vpc_config,
    )

    # create resource policy
    statement = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": "execute-api:Invoke",
                "Resource": ["execute-api:/*"],
            }
        ],
    }
    patches = [{"op": "replace", "path": "/policy", "value": json.dumps(statement)}]
    result = aws_client.apigateway.update_rest_api(restApiId=api_id, patchOperations=patches)
    result["policy"] = json.loads(to_bytes(result["policy"]).decode("unicode_escape"))
    snapshot.match("api-details", result)

    # re-deploy API
    create_rest_api_deployment(
        aws_client.apigateway, restApiId=api_id, stageName=DEFAULT_STAGE_NAME
    )

    subdomain = f"{api_id}-{endpoint_id}"
    endpoint = api_invoke_url(subdomain, stage=DEFAULT_STAGE_NAME, path="/test")
    host_header = urlparse(endpoint).netloc

    # create Lambda function that invokes the API GW (private VPC endpoint not accessible from outside of AWS)
    if not is_aws_cloud():
        api_host = get_main_endpoint_from_container()
        endpoint = endpoint.replace(host_header, f"{api_host}:{config.GATEWAY_LISTEN[0].port}")

    def _invoke_api(url: str, headers: dict[str, str]):
        invoke_response = aws_client.lambda_.invoke(
            FunctionName=func_name, Payload=json.dumps({"url": url, "headers": headers})
        )
        payload = json.load(invoke_response["Payload"])
        items = json.loads(payload["content"])["Items"]
        assert len(items) == len(item_ids)

    # invoke Lambda and assert result
    # AWS
    #   url: https://{rest-api-id}-{vpce-id}.execute-api.{region}.amazonaws.com/{stage}
    #   host: {rest-api-id}.execute-api.{region}.amazonaws.com
    # LocalStack
    #   url: http://localhost.localstack.cloud:4566/{stage}
    #   host: {rest-api-id}-{vpce-id}.execute-api.localhost.localstack.cloud
    retry(lambda: _invoke_api(endpoint, {"host": host_header}), retries=15, sleep=poll_sleep)

    # invoke Lambda and assert result
    # AWS
    #   url: https://{public-dns-hostname}.execute-api.{region}.vpce.amazonaws.com/{stage}
    #   x-apigw-api-id: {rest-api-id}
    # LocalStack
    #   url: http://{public-dns-hostname}.execute-api.{region}.vpce.{localstack-host}/{stage}
    #   x-apigw-api-id: {rest-api-id}
    protocol = "https" if is_aws_cloud() else "http"
    vpc_endpoint_public_dns = endpoint_details["DnsEntries"][0]["DnsName"]
    public_dns_url = f"{protocol}://{vpc_endpoint_public_dns}/{DEFAULT_STAGE_NAME}/test"
    retry(
        lambda: _invoke_api(public_dns_url, {"x-apigw-api-id": api_id}),
        retries=15,
        sleep=poll_sleep,
    )

    # invoke Lambda and assert result
    # AWS
    #   url: https://{public-dns-hostname}.execute-api.{region}.vpce.amazonaws.com/{stage}
    #   host: {rest-api-id}.execute-api.{region}.amazonaws.com
    # LocalStack
    #   url: http://{public-dns-hostname}.execute-api.{region}.vpce.{localstack_host}/{stage}
    #   host: {rest-api-id}.execute-api.{region}.{localstack-host}
    host = api_invoke_url(api_id).partition("//")[-1].strip("/")
    retry(
        lambda: _invoke_api(public_dns_url, {"Host": host}),
        retries=15,
        sleep=poll_sleep,
    )