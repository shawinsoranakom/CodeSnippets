def test_url_config_list_paging(self, create_lambda_function, snapshot, aws_client):
        snapshot.add_transformer(
            snapshot.transform.key_value("FunctionUrl", "lambda-url", reference_replacement=False)
        )
        snapshot.add_transformer(
            SortingTransformer("FunctionUrlConfigs", sorting_fn=lambda x: x["FunctionArn"])
        )
        function_name = f"test-function-{short_uid()}"
        alias_name = "urlalias"

        create_lambda_function(
            func_name=function_name,
            zip_file=testutil.create_zip_file(TEST_LAMBDA_NODEJS, get_content=True),
            runtime=Runtime.nodejs20_x,
            handler="lambda_handler.handler",
        )

        fn_version_result = aws_client.lambda_.publish_version(FunctionName=function_name)
        snapshot.match("fn_version_result", fn_version_result)
        create_alias_result = aws_client.lambda_.create_alias(
            FunctionName=function_name,
            Name=alias_name,
            FunctionVersion=fn_version_result["Version"],
        )
        snapshot.match("create_alias_result", create_alias_result)

        with pytest.raises(aws_client.lambda_.exceptions.ResourceNotFoundException) as e:
            aws_client.lambda_.list_function_url_configs(FunctionName="doesnotexist")
        snapshot.match("list_function_notfound", e.value.response)

        list_all_empty = aws_client.lambda_.list_function_url_configs(FunctionName=function_name)
        snapshot.match("list_all_empty", list_all_empty)

        url_config_fn = aws_client.lambda_.create_function_url_config(
            FunctionName=function_name, AuthType="NONE"
        )
        snapshot.match("url_config_fn", url_config_fn)
        url_config_alias = aws_client.lambda_.create_function_url_config(
            FunctionName=f"{function_name}:{alias_name}", Qualifier=alias_name, AuthType="NONE"
        )
        snapshot.match("url_config_alias", url_config_alias)

        list_all = aws_client.lambda_.list_function_url_configs(FunctionName=function_name)
        snapshot.match("list_all", list_all)

        total_configs = [url_config_fn["FunctionUrl"], url_config_alias["FunctionUrl"]]

        list_max_1_item = aws_client.lambda_.list_function_url_configs(
            FunctionName=function_name, MaxItems=1
        )
        assert len(list_max_1_item["FunctionUrlConfigs"]) == 1
        assert list_max_1_item["FunctionUrlConfigs"][0]["FunctionUrl"] in total_configs

        list_max_2_item = aws_client.lambda_.list_function_url_configs(
            FunctionName=function_name, MaxItems=2
        )
        assert len(list_max_2_item["FunctionUrlConfigs"]) == 2
        assert list_max_2_item["FunctionUrlConfigs"][0]["FunctionUrl"] in total_configs
        assert list_max_2_item["FunctionUrlConfigs"][1]["FunctionUrl"] in total_configs

        list_max_1_item_marker = aws_client.lambda_.list_function_url_configs(
            FunctionName=function_name, MaxItems=1, Marker=list_max_1_item["NextMarker"]
        )
        assert len(list_max_1_item_marker["FunctionUrlConfigs"]) == 1
        assert list_max_1_item_marker["FunctionUrlConfigs"][0]["FunctionUrl"] in total_configs
        assert (
            list_max_1_item_marker["FunctionUrlConfigs"][0]["FunctionUrl"]
            != list_max_1_item["FunctionUrlConfigs"][0]["FunctionUrl"]
        )