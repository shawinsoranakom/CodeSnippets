def test_number_of_function_versions_sync(create_lambda_function, s3_bucket, aws_client):
    """Test how many function versions LocalStack can support; validating **synchronous** invokes."""
    num_function_versions = 2 if is_aws_cloud() else 100

    function_name = f"test-lambda-perf-{short_uid()}"
    create_lambda_function(
        handler_file=TEST_LAMBDA_PYTHON_S3_INTEGRATION,
        func_name=function_name,
        runtime=Runtime.python3_12,
        Environment={"Variables": {"S3_BUCKET_NAME": s3_bucket}},
    )

    # Publish function versions
    versions = ["$LATEST"]
    for i in range(num_function_versions):
        # Publishing a new function version requires updating the function configuration or code
        aws_client.lambda_.update_function_configuration(
            FunctionName=function_name, Description=str(i + 1)
        )
        aws_client.lambda_.get_waiter("function_updated_v2").wait(FunctionName=function_name)
        publish_version_response = aws_client.lambda_.publish_version(FunctionName=function_name)
        versions.append(publish_version_response["Version"])

    # Invoke each function version once
    for version in versions:
        invoke_response = aws_client.lambda_.invoke(
            FunctionName=function_name,
            InvocationType=InvocationType.RequestResponse,
            Qualifier=version,
        )
        assert "FunctionError" not in invoke_response
        assert invoke_response["ExecutedVersion"] == version
        payload = json.load(invoke_response["Payload"])
        assert payload["function_version"] == version
        request_id = invoke_response["ResponseMetadata"]["RequestId"]
        assert payload["s3_key"] == request_id