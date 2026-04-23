def test_hot_reloading(
        self,
        create_lambda_function_aws,
        runtime,
        handler_file,
        handler_filename,
        lambda_su_role,
        cleanups,
        aws_client,
    ):
        """Test hot reloading of lambda code"""
        # Hot reloading is debounced with 500ms
        # 0.6 works on Linux, but it takes slightly longer on macOS
        sleep_time = 0.8
        function_name = f"test-hot-reloading-{short_uid()}"
        hot_reloading_bucket = config.BUCKET_MARKER_LOCAL
        tmp_path = config.dirs.mounted_tmp
        hot_reloading_dir_path = os.path.join(tmp_path, f"hot-reload-{short_uid()}")
        mkdir(hot_reloading_dir_path)
        cleanups.append(lambda: rm_rf(hot_reloading_dir_path))
        function_content = load_file(handler_file)
        with open(os.path.join(hot_reloading_dir_path, handler_filename), mode="w") as f:
            f.write(function_content)

        mount_path = get_host_path_for_path_in_docker(hot_reloading_dir_path)
        create_function_response = create_lambda_function_aws(
            FunctionName=function_name,
            Handler="handler.handler",
            Code={"S3Bucket": hot_reloading_bucket, "S3Key": mount_path},
            Role=lambda_su_role,
            Runtime=runtime,
        )
        # The AWS Toolkit for VS Code depends on this naming convention:
        # https://github.com/aws/aws-toolkit-vscode/blob/1f6250148ba4f2c22e89613b8e7801bd8c4be062/packages/core/src/lambda/utils.ts#L212
        assert create_function_response["CodeSha256"].startswith("hot-reloading")

        get_function_response = aws_client.lambda_.get_function(FunctionName=function_name)
        code_location_path = Path.from_uri(get_function_response["Code"]["Location"])
        assert str(code_location_path) == mount_path

        response = aws_client.lambda_.invoke(FunctionName=function_name, Payload=b"{}")
        response_dict = json.load(response["Payload"])
        assert response_dict["counter"] == 1
        assert response_dict["constant"] == "value1"
        response = aws_client.lambda_.invoke(FunctionName=function_name, Payload=b"{}")
        response_dict = json.load(response["Payload"])
        assert response_dict["counter"] == 2
        assert response_dict["constant"] == "value1"
        with open(os.path.join(hot_reloading_dir_path, handler_filename), mode="w") as f:
            f.write(function_content.replace("value1", "value2"))
        # we have to sleep here, since the hot reloading is debounced with 500ms
        time.sleep(sleep_time)
        response = aws_client.lambda_.invoke(FunctionName=function_name, Payload=b"{}")
        response_dict = json.load(response["Payload"])
        assert response_dict["counter"] == 1
        assert response_dict["constant"] == "value2"
        response = aws_client.lambda_.invoke(FunctionName=function_name, Payload=b"{}")
        response_dict = json.load(response["Payload"])
        assert response_dict["counter"] == 2
        assert response_dict["constant"] == "value2"

        # test subdirs
        test_folder = os.path.join(hot_reloading_dir_path, "test-folder")
        mkdir(test_folder)
        # make sure the creation of the folder triggered reload
        time.sleep(sleep_time)
        response = aws_client.lambda_.invoke(FunctionName=function_name, Payload=b"{}")
        response_dict = json.load(response["Payload"])
        assert response_dict["counter"] == 1
        assert response_dict["constant"] == "value2"
        # now writing something in the new folder to check if it will reload
        with open(os.path.join(test_folder, "test-file"), mode="w") as f:
            f.write("test-content")
        time.sleep(sleep_time)
        response = aws_client.lambda_.invoke(FunctionName=function_name, Payload=b"{}")
        response_dict = json.load(response["Payload"])
        assert response_dict["counter"] == 1
        assert response_dict["constant"] == "value2"