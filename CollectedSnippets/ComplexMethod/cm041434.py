def test_create_url_config_custom_id_tag_alias(self, create_lambda_function, aws_client):
        custom_id_value = "my-custom-subdomain"
        function_name = f"test-function-{short_uid()}"
        zip_contents = testutil.create_zip_file(TEST_LAMBDA_PYTHON_ECHO, get_content=True)

        create_lambda_function(
            func_name=function_name,
            zip_file=zip_contents,
            runtime=Runtime.nodejs20_x,
            handler="lambda_handler.handler",
            Tags={TAG_KEY_CUSTOM_URL: custom_id_value},
        )

        def _assert_create_function_url(qualifier: str | None, expected_url_id: str):
            params = {"FunctionName": function_name, "AuthType": "NONE"}
            if qualifier:
                # Note: boto3 will throw an exception if the Qualifier parameter is None or ""
                params["Qualifier"] = qualifier

            aws_client.lambda_.get_waiter("function_updated_v2").wait(FunctionName=function_name)
            url_config_created = aws_client.lambda_.create_function_url_config(**params)
            assert f"://{expected_url_id}.lambda-url." in url_config_created["FunctionUrl"]

        def _assert_create_aliased_function_url(fn_version: str, fn_alias: str):
            aws_client.lambda_.create_alias(
                FunctionName=function_name, FunctionVersion=fn_version, Name=fn_alias
            )

            aws_client.lambda_.add_permission(
                FunctionName=function_name,
                StatementId="urlPermission",
                Action="lambda:InvokeFunctionUrl",
                Principal="*",
                FunctionUrlAuthType="NONE",
                Qualifier=fn_alias,
            )

            _assert_create_function_url(fn_alias, f"{custom_id_value}-{fn_alias}")

        # Publishes a new version and creates an aliased URL
        update_function_code_v1_resp = aws_client.lambda_.update_function_code(
            FunctionName=function_name, ZipFile=zip_contents, Publish=True
        )
        version = update_function_code_v1_resp.get("Version")
        _assert_create_aliased_function_url(fn_version=version, fn_alias="v1")

        # Alias the $LATEST version
        _assert_create_aliased_function_url(fn_version="$LATEST", fn_alias="latest")

        # Update the code, creating an unpublished version
        update_function_code_latest_resp = aws_client.lambda_.update_function_code(
            FunctionName=function_name, ZipFile=zip_contents
        )

        # Assert that both functions are equal
        function_v1_sha256 = update_function_code_v1_resp.get("CodeSha256")
        function_latest_sha256 = update_function_code_latest_resp.get("CodeSha256")
        assert function_v1_sha256 and function_latest_sha256
        assert function_v1_sha256 == function_latest_sha256

        # Assert that update actually did occur
        last_modified_v1 = update_function_code_v1_resp.get("LastModified")
        last_modified_latest = update_function_code_latest_resp.get("LastModified")
        assert last_modified_latest > last_modified_v1

        # Create a URL for an unpublished function
        _assert_create_function_url(qualifier=None, expected_url_id=custom_id_value)

        # Ensure that these compound url-id's are stored correctly
        with pytest.raises(aws_client.lambda_.exceptions.ResourceConflictException) as ex:
            aws_client.lambda_.create_function_url_config(
                FunctionName=function_name, AuthType="NONE", Qualifier="v1"
            )
        assert ex.match("ResourceConflictException")

        # Ensure that all aliased URLs can be correctly retrieved
        for alias in ["v1", "latest"]:
            function_url = aws_client.lambda_.get_function_url_config(
                FunctionName=function_name, Qualifier=alias
            ).get("FunctionUrl")
            assert f"://{custom_id_value}-{alias}.lambda-url." in function_url

        # Finally, check if the non-aliased URL can be retrieved
        function_url = aws_client.lambda_.get_function_url_config(FunctionName=function_name).get(
            "FunctionUrl"
        )
        assert f"://{custom_id_value}.lambda-url." in function_url