def test_lambda_eventinvokeconfig_exceptions(
        self,
        create_lambda_function,
        snapshot,
        lambda_su_role,
        account_id,
        aws_client_factory,
        aws_client,
    ):
        """some parts could probably be split apart (e.g. overwriting with update)"""
        lambda_client = aws_client_factory(config=Config(parameter_validation=False)).lambda_
        snapshot.add_transformer(
            SortingTransformer(
                key="FunctionEventInvokeConfigs", sorting_fn=lambda conf: conf["FunctionArn"]
            )
        )
        function_name = f"fn-eventinvoke-{short_uid()}"
        function_name_2 = f"fn-eventinvoke-2-{short_uid()}"
        create_lambda_function(
            handler_file=TEST_LAMBDA_PYTHON_ECHO,
            func_name=function_name,
            runtime=Runtime.python3_12,
            role=lambda_su_role,
        )
        get_fn_result = lambda_client.get_function(FunctionName=function_name)
        fn_arn = get_fn_result["Configuration"]["FunctionArn"]

        create_lambda_function(
            handler_file=TEST_LAMBDA_PYTHON_ECHO,
            func_name=function_name_2,
            runtime=Runtime.python3_12,
            role=lambda_su_role,
        )
        get_fn_result_2 = lambda_client.get_function(FunctionName=function_name_2)
        fn_arn_2 = get_fn_result_2["Configuration"]["FunctionArn"]

        # one version and one alias

        fn_version_result = lambda_client.publish_version(FunctionName=function_name)
        snapshot.match("fn_version_result", fn_version_result)
        fn_version = fn_version_result["Version"]

        fn_alias_result = lambda_client.create_alias(
            FunctionName=function_name, Name="eventinvokealias", FunctionVersion=fn_version
        )
        snapshot.match("fn_alias_result", fn_alias_result)
        fn_alias = fn_alias_result["Name"]

        # FunctionName tests

        region_name = lambda_client.meta.region_name
        fake_arn = f"arn:{get_partition(region_name)}:lambda:{region_name}:{account_id}:function:doesnotexist"

        with pytest.raises(lambda_client.exceptions.ResourceNotFoundException) as e:
            lambda_client.put_function_event_invoke_config(
                FunctionName="doesnotexist", MaximumRetryAttempts=1
            )
        snapshot.match("put_functionname_name_notfound", e.value.response)

        with pytest.raises(lambda_client.exceptions.ResourceNotFoundException) as e:
            lambda_client.put_function_event_invoke_config(
                FunctionName=fake_arn, MaximumRetryAttempts=1
            )
        snapshot.match("put_functionname_arn_notfound", e.value.response)

        # Arguments missing

        with pytest.raises(lambda_client.exceptions.InvalidParameterValueException) as e:
            lambda_client.put_function_event_invoke_config(FunctionName="doesnotexist")
        snapshot.match("put_functionname_nootherargs", e.value.response)

        # Destination value tests

        with pytest.raises(lambda_client.exceptions.InvalidParameterValueException) as e:
            lambda_client.put_function_event_invoke_config(
                FunctionName=function_name,
                DestinationConfig={"OnSuccess": {"Destination": fake_arn}},
            )
        snapshot.match("put_destination_lambda_doesntexist", e.value.response)

        with pytest.raises(lambda_client.exceptions.InvalidParameterValueException) as e:
            lambda_client.put_function_event_invoke_config(
                FunctionName=function_name, DestinationConfig={"OnSuccess": {"Destination": fn_arn}}
            )
        snapshot.match("put_destination_recursive", e.value.response)

        response = lambda_client.put_function_event_invoke_config(
            FunctionName=function_name, DestinationConfig={"OnSuccess": {"Destination": fn_arn_2}}
        )
        snapshot.match("put_destination_other_lambda", response)

        with pytest.raises(lambda_client.exceptions.InvalidParameterValueException) as e:
            lambda_client.put_function_event_invoke_config(
                FunctionName=function_name,
                DestinationConfig={
                    "OnSuccess": {"Destination": fn_arn.replace(":lambda:", ":iam:")}
                },
            )
        snapshot.match("put_destination_invalid_service_arn", e.value.response)

        response = lambda_client.put_function_event_invoke_config(
            FunctionName=function_name, DestinationConfig={"OnSuccess": {}}
        )
        snapshot.match("put_destination_success_no_destination_arn", response)

        response = lambda_client.put_function_event_invoke_config(
            FunctionName=function_name, DestinationConfig={"OnFailure": {}}
        )
        snapshot.match("put_destination_failure_no_destination_arn", response)

        with pytest.raises(lambda_client.exceptions.ClientError) as e:
            lambda_client.put_function_event_invoke_config(
                FunctionName=function_name,
                DestinationConfig={
                    "OnFailure": {"Destination": fn_arn.replace(":lambda:", ":_-/!lambda:")}
                },
            )
        snapshot.match("put_destination_invalid_arn_pattern", e.value.response)

        # Function Name & Qualifier tests
        response = lambda_client.put_function_event_invoke_config(
            FunctionName=function_name, MaximumRetryAttempts=1
        )
        snapshot.match("put_destination_latest", response)
        response = lambda_client.put_function_event_invoke_config(
            FunctionName=function_name, Qualifier="$LATEST", MaximumRetryAttempts=1
        )
        snapshot.match("put_destination_latest_explicit_qualifier", response)

        response = lambda_client.put_function_event_invoke_config(
            FunctionName=function_name, Qualifier=fn_version, MaximumRetryAttempts=1
        )
        snapshot.match("put_destination_version", response)
        response = lambda_client.put_function_event_invoke_config(
            FunctionName=function_name, Qualifier=fn_alias, MaximumRetryAttempts=1
        )
        snapshot.match("put_alias_functionname_qualifier", response)

        with pytest.raises(lambda_client.exceptions.ResourceNotFoundException) as e:
            lambda_client.put_function_event_invoke_config(
                FunctionName=function_name,
                Qualifier=f"{fn_alias}doesnotexist",
                MaximumRetryAttempts=1,
            )
        snapshot.match("put_alias_doesnotexist", e.value.response)
        response = lambda_client.put_function_event_invoke_config(
            FunctionName=fn_alias_result["AliasArn"], MaximumRetryAttempts=1
        )
        snapshot.match("put_alias_qualifiedarn", response)
        response = lambda_client.put_function_event_invoke_config(
            FunctionName=fn_alias_result["AliasArn"], Qualifier=fn_alias, MaximumRetryAttempts=1
        )
        snapshot.match("put_alias_qualifiedarn_qualifier", response)
        with pytest.raises(lambda_client.exceptions.InvalidParameterValueException) as e:
            lambda_client.put_function_event_invoke_config(
                FunctionName=fn_alias_result["AliasArn"],
                Qualifier=f"{fn_alias}doesnotexist",
                MaximumRetryAttempts=1,
            )
        snapshot.match("put_alias_qualifiedarn_qualifierconflict", e.value.response)

        response = lambda_client.put_function_event_invoke_config(
            FunctionName=f"{function_name}:{fn_alias}", MaximumRetryAttempts=1
        )
        snapshot.match("put_alias_shorthand", response)
        response = lambda_client.put_function_event_invoke_config(
            FunctionName=f"{function_name}:{fn_alias}", Qualifier=fn_alias, MaximumRetryAttempts=1
        )
        snapshot.match("put_alias_shorthand_qualifier", response)

        with pytest.raises(lambda_client.exceptions.InvalidParameterValueException) as e:
            lambda_client.put_function_event_invoke_config(
                FunctionName=f"{function_name}:{fn_alias}",
                Qualifier=f"{fn_alias}doesnotexist",
                MaximumRetryAttempts=1,
            )
        snapshot.match("put_alias_shorthand_qualifierconflict", e.value.response)

        # apparently this also works with function numbers (not in the docs!)
        response = lambda_client.put_function_event_invoke_config(
            FunctionName=f"{function_name}:{fn_version}", MaximumRetryAttempts=1
        )
        snapshot.match("put_version_shorthand", response)

        response = lambda_client.put_function_event_invoke_config(
            FunctionName=f"{function_name}:$LATEST", Qualifier="$LATEST", MaximumRetryAttempts=1
        )
        snapshot.match("put_shorthand_qualifier_match", response)

        with pytest.raises(lambda_client.exceptions.InvalidParameterValueException) as e:
            lambda_client.put_function_event_invoke_config(
                FunctionName=f"{function_name}:{fn_version}",
                Qualifier="$LATEST",
                MaximumRetryAttempts=1,
            )
        snapshot.match("put_shorthand_qualifier_mismatch_1", e.value.response)

        with pytest.raises(lambda_client.exceptions.InvalidParameterValueException) as e:
            lambda_client.put_function_event_invoke_config(
                FunctionName=f"{function_name}:$LATEST",
                Qualifier=fn_version,
                MaximumRetryAttempts=1,
            )
        snapshot.match("put_shorthand_qualifier_mismatch_2", e.value.response)

        with pytest.raises(lambda_client.exceptions.InvalidParameterValueException) as e:
            lambda_client.put_function_event_invoke_config(
                FunctionName=f"{function_name}:{fn_version}",
                Qualifier=fn_alias,
                MaximumRetryAttempts=1,
            )
        snapshot.match("put_shorthand_qualifier_mismatch_3", e.value.response)

        put_maxevent_maxvalue_result = lambda_client.put_function_event_invoke_config(
            FunctionName=function_name, MaximumRetryAttempts=2, MaximumEventAgeInSeconds=21600
        )
        snapshot.match("put_maxevent_maxvalue_result", put_maxevent_maxvalue_result)

        # Test overwrite existing values +  differences between put & update
        # first create a config with both values set, then overwrite it with only one value set

        first_overwrite_response = lambda_client.put_function_event_invoke_config(
            FunctionName=function_name, MaximumRetryAttempts=2, MaximumEventAgeInSeconds=60
        )
        snapshot.match("put_pre_overwrite", first_overwrite_response)
        second_overwrite_response = lambda_client.put_function_event_invoke_config(
            FunctionName=function_name, MaximumRetryAttempts=0
        )
        snapshot.match("put_post_overwrite", second_overwrite_response)
        second_overwrite_existing_response = lambda_client.put_function_event_invoke_config(
            FunctionName=function_name, MaximumRetryAttempts=0
        )
        snapshot.match("second_overwrite_existing_response", second_overwrite_existing_response)
        get_postoverwrite_response = lambda_client.get_function_event_invoke_config(
            FunctionName=function_name
        )
        snapshot.match("get_post_overwrite", get_postoverwrite_response)
        assert get_postoverwrite_response["MaximumRetryAttempts"] == 0
        assert "MaximumEventAgeInSeconds" not in get_postoverwrite_response

        pre_update_response = lambda_client.put_function_event_invoke_config(
            FunctionName=function_name, MaximumRetryAttempts=2, MaximumEventAgeInSeconds=60
        )
        snapshot.match("pre_update_response", pre_update_response)
        update_response = lambda_client.update_function_event_invoke_config(
            FunctionName=function_name, MaximumRetryAttempts=0
        )
        snapshot.match("update_response", update_response)

        update_response_existing = lambda_client.update_function_event_invoke_config(
            FunctionName=function_name, MaximumRetryAttempts=0
        )
        snapshot.match("update_response_existing", update_response_existing)

        get_postupdate_response = lambda_client.get_function_event_invoke_config(
            FunctionName=function_name
        )
        assert get_postupdate_response["MaximumRetryAttempts"] == 0
        assert get_postupdate_response["MaximumEventAgeInSeconds"] == 60

        # Test delete & listing
        list_response = lambda_client.list_function_event_invoke_configs(FunctionName=function_name)
        snapshot.match("list_configs", list_response)

        paged_response = lambda_client.list_function_event_invoke_configs(
            FunctionName=function_name, MaxItems=2
        )  # 2 out of 3
        assert len(paged_response["FunctionEventInvokeConfigs"]) == 2
        assert paged_response["NextMarker"]

        delete_latest = lambda_client.delete_function_event_invoke_config(
            FunctionName=function_name, Qualifier="$LATEST"
        )
        snapshot.match("delete_latest", delete_latest)
        delete_version = lambda_client.delete_function_event_invoke_config(
            FunctionName=function_name, Qualifier=fn_version
        )
        snapshot.match("delete_version", delete_version)
        delete_alias = lambda_client.delete_function_event_invoke_config(
            FunctionName=function_name, Qualifier=fn_alias
        )
        snapshot.match("delete_alias", delete_alias)

        list_response_postdelete = lambda_client.list_function_event_invoke_configs(
            FunctionName=function_name
        )
        snapshot.match("list_configs_postdelete", list_response_postdelete)
        assert len(list_response_postdelete["FunctionEventInvokeConfigs"]) == 0

        # already deleted, try to delete again
        with pytest.raises(lambda_client.exceptions.ResourceNotFoundException) as e:
            lambda_client.delete_function_event_invoke_config(FunctionName=function_name)
        snapshot.match("delete_function_not_found", e.value.response)

        with pytest.raises(lambda_client.exceptions.ResourceNotFoundException) as e:
            lambda_client.delete_function_event_invoke_config(FunctionName="doesnotexist")
        snapshot.match("delete_function_doesnotexist", e.value.response)

        # more excs

        with pytest.raises(lambda_client.exceptions.ResourceNotFoundException) as e:
            lambda_client.list_function_event_invoke_configs(FunctionName="doesnotexist")
        snapshot.match("list_function_doesnotexist", e.value.response)

        with pytest.raises(lambda_client.exceptions.ResourceNotFoundException) as e:
            lambda_client.get_function_event_invoke_config(FunctionName="doesnotexist")
        snapshot.match("get_function_doesnotexist", e.value.response)

        with pytest.raises(lambda_client.exceptions.ResourceNotFoundException) as e:
            lambda_client.get_function_event_invoke_config(
                FunctionName=function_name, Qualifier="doesnotexist"
            )
        snapshot.match("get_qualifier_doesnotexist", e.value.response)

        with pytest.raises(lambda_client.exceptions.ResourceNotFoundException) as e:
            lambda_client.update_function_event_invoke_config(
                FunctionName="doesnotexist", MaximumRetryAttempts=0
            )
        snapshot.match("update_eventinvokeconfig_function_doesnotexist", e.value.response)

        # ARN is valid but the alias doesn't have an event invoke config anymore (see previous delete)
        with pytest.raises(lambda_client.exceptions.ResourceNotFoundException) as e:
            lambda_client.get_function_event_invoke_config(FunctionName=fn_alias_result["AliasArn"])
        snapshot.match("get_eventinvokeconfig_doesnotexist", e.value.response)

        with pytest.raises(lambda_client.exceptions.ResourceNotFoundException) as e:
            lambda_client.update_function_event_invoke_config(
                FunctionName=fn_alias_result["AliasArn"], MaximumRetryAttempts=0
            )
        snapshot.match(
            "update_eventinvokeconfig_config_doesnotexist_with_qualifier", e.value.response
        )

        with pytest.raises(lambda_client.exceptions.ResourceNotFoundException) as e:
            lambda_client.update_function_event_invoke_config(
                FunctionName=fn_arn, MaximumRetryAttempts=0
            )
        snapshot.match(
            "update_eventinvokeconfig_config_doesnotexist_without_qualifier", e.value.response
        )