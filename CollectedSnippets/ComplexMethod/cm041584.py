def test_rest_api_to_dynamodb_integration(
    ddb_action,
    dynamodb_create_table,
    create_rest_api_with_integration,
    snapshot,
    aws_client,
):
    snapshot.add_transformer(snapshot.transform.key_value("date", reference_replacement=False))
    snapshot.add_transformer(snapshot.transform.key_value("x-amzn-trace-id"))
    snapshot.add_transformer(
        snapshot.transform.key_value("content-length", reference_replacement=False)
    )
    snapshot.add_transformer(
        snapshot.transform.key_value("x-amz-apigw-id", reference_replacement=False)
    )

    # create table
    table = dynamodb_create_table()["TableDescription"]
    table_name = table["TableName"]

    # insert items
    item_ids = ("test", "test2", "test 3")
    for item_id in item_ids:
        aws_client.dynamodb.put_item(TableName=table_name, Item={"id": {"S": item_id}})

    # construct request mapping template
    if ddb_action == "PutItem":
        template = json.dumps(
            {
                "TableName": table_name,
                "Item": {"id": {"S": "$input.params('id')"}},
            }
        )
    elif ddb_action == "Query":
        template = json.dumps(
            {
                "TableName": table_name,
                "KeyConditionExpression": "id = :id",
                "ExpressionAttributeValues": {":id": {"S": "$input.params('id')"}},
            }
        )
    elif ddb_action == "Scan":
        template = json.dumps({"TableName": table_name})
    request_templates = {APPLICATION_JSON: template}

    # deploy REST API with integration
    region_name = aws_client.apigateway.meta.region_name
    integration_uri = f"arn:aws:apigateway:{region_name}:dynamodb:action/{ddb_action}"
    api_id = create_rest_api_with_integration(
        integration_uri=integration_uri,
        req_templates=request_templates,
        integration_type="AWS",
    )

    def _invoke_endpoint(id_param=None):
        url = api_invoke_url(api_id, stage=DEFAULT_STAGE_NAME, path=f"/test?id={id_param}")
        response = requests.post(url)
        assert response.status_code == 200
        return {
            "status_code": response.status_code,
            "content": response.json(),
            "headers": {k.lower(): v for k, v in dict(response.headers).items()},
        }

    def _invoke_with_retries(id_param=None):
        return retry(lambda: _invoke_endpoint(id_param), retries=15, sleep=2)

    # run assertions

    if ddb_action == "PutItem":
        result = _invoke_with_retries("test-new")
        snapshot.match("result-put-item", result)
        result = aws_client.dynamodb.scan(TableName=table_name)
        result["Items"] = sorted(result["Items"], key=lambda x: x["id"]["S"])
        snapshot.match("result-scan", result)

    elif ddb_action == "Query":
        # retrieve valid item IDs
        for item_id in item_ids:
            result = _invoke_with_retries(item_id)
            snapshot.match(f"result-{item_id}", result)
        # retrieve invalid item ID
        result = _invoke_with_retries("test-invalid")
        snapshot.match("result-invalid", result)

    elif ddb_action == "Scan":
        result = _invoke_with_retries()
        result["content"]["Items"] = sorted(result["content"]["Items"], key=lambda x: x["id"]["S"])
        snapshot.match("result-scan", result)