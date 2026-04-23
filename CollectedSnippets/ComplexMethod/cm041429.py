def test_lambda_code_location_zipfile(
        self, snapshot, create_lambda_function_aws, lambda_su_role, aws_client
    ):
        function_name = f"code-function-{short_uid()}"
        zip_file_bytes = create_lambda_archive(load_file(TEST_LAMBDA_PYTHON_ECHO), get_content=True)
        create_response = create_lambda_function_aws(
            FunctionName=function_name,
            Handler="index.handler",
            Code={"ZipFile": zip_file_bytes},
            PackageType="Zip",
            Role=lambda_su_role,
            Runtime=Runtime.python3_12,
        )
        snapshot.match("create-response-zip-file", create_response)
        get_function_response = aws_client.lambda_.get_function(FunctionName=function_name)
        snapshot.match("get-function-response", get_function_response)
        code_location = get_function_response["Code"]["Location"]
        response = requests.get(code_location)
        assert zip_file_bytes == response.content
        h = sha256(zip_file_bytes)
        b64digest = to_str(base64.b64encode(h.digest()))
        assert b64digest == get_function_response["Configuration"]["CodeSha256"]
        assert len(zip_file_bytes) == get_function_response["Configuration"]["CodeSize"]
        zip_file_bytes_updated = create_lambda_archive(
            load_file(TEST_LAMBDA_PYTHON_VERSION), get_content=True
        )
        update_function_response = aws_client.lambda_.update_function_code(
            FunctionName=function_name, ZipFile=zip_file_bytes_updated
        )
        snapshot.match("update-function-response", update_function_response)
        get_function_response_updated = aws_client.lambda_.get_function(FunctionName=function_name)
        snapshot.match("get-function-response-updated", get_function_response_updated)
        code_location_updated = get_function_response_updated["Code"]["Location"]
        response = requests.get(code_location_updated)
        assert zip_file_bytes_updated == response.content
        h = sha256(zip_file_bytes_updated)
        b64digest_updated = to_str(base64.b64encode(h.digest()))
        assert b64digest != b64digest_updated
        assert b64digest_updated == get_function_response_updated["Configuration"]["CodeSha256"]
        assert (
            len(zip_file_bytes_updated)
            == get_function_response_updated["Configuration"]["CodeSize"]
        )