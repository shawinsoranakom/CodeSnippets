def test_lambda_url_echo_invoke(
        self, create_lambda_function, snapshot, aws_client, invoke_mode
    ):
        if invoke_mode == "RESPONSE_STREAM" and not is_aws_cloud():
            pytest.skip(
                "'RESPONSE_STREAM should invoke the lambda using InvokeWithResponseStream, "
                "but this is not implemented on LS yet. '"
            )

        snapshot.add_transformer(
            snapshot.transform.key_value(
                "FunctionUrl", "<function-url>", reference_replacement=False
            )
        )
        function_name = f"test-fnurl-echo-{short_uid()}"

        create_lambda_function(
            func_name=function_name,
            zip_file=testutil.create_zip_file(TEST_LAMBDA_URL, get_content=True),
            runtime=Runtime.nodejs20_x,
            handler="lambda_url.handler",
        )

        if invoke_mode:
            url_config = aws_client.lambda_.create_function_url_config(
                FunctionName=function_name, AuthType="NONE", InvokeMode=invoke_mode
            )
        else:
            url_config = aws_client.lambda_.create_function_url_config(
                FunctionName=function_name,
                AuthType="NONE",
            )
        snapshot.match("create_lambda_url_config", url_config)

        permissions_response = aws_client.lambda_.add_permission(
            FunctionName=function_name,
            StatementId="urlPermission",
            Action="lambda:InvokeFunctionUrl",
            Principal="*",
            FunctionUrlAuthType="NONE",
        )
        snapshot.match("add_permission", permissions_response)

        url = f"{url_config['FunctionUrl']}custom_path/extend?test_param=test_value"

        # TODO: add more cases
        result = safe_requests.post(url, data="text", headers={"Content-Type": "text/plain"})
        assert result.status_code == 200

        if invoke_mode != "RESPONSE_STREAM":
            event = json.loads(result.content)["event"]
            assert event["body"] == "text"
            assert event["isBase64Encoded"] is False

            result = safe_requests.post(url)
            event = json.loads(result.content)["event"]

        else:
            response_chunks = []
            for chunk in result.iter_content(chunk_size=1024):
                if chunk:  # Filter out keep-alive new chunks
                    response_chunks.append(chunk.decode("utf-8"))

            # Join the chunks to form the complete response string
            complete_response = "".join(response_chunks)

            response_json = json.loads(complete_response)
            event = json.loads(response_json["body"])["event"]
            # TODO the chunk-event actually contains a key "body": "text" - not sure if we need more/other validation here
            # but it's not implemented in LS anyhow yet

        assert "Body" not in event
        assert event["isBase64Encoded"] is False