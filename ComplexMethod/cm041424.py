def test_lambda_provisioned_concurrency_moves_with_alias(
        self, create_lambda_function, snapshot, aws_client
    ):
        """
        create fn ⇒ publish version ⇒ create alias for version ⇒ put concurrency on alias
        ⇒ new version with change ⇒ change alias to new version ⇒ concurrency moves with alias? same behavior for calls to alias/version?
        """

        # TODO: validate once implemented
        min_concurrent_executions = 10 + 2  # for alias and version
        check_concurrency_quota(aws_client, min_concurrent_executions)

        func_name = f"test_lambda_{short_uid()}"
        alias_name = f"test_alias_{short_uid()}"
        snapshot.add_transformer(snapshot.transform.regex(alias_name, "<alias-name>"))

        create_result = create_lambda_function(
            func_name=func_name,
            handler_file=TEST_LAMBDA_INVOCATION_TYPE,
            runtime=Runtime.python3_12,
            client=aws_client.lambda_,
            timeout=2,
        )
        snapshot.match("create-result", create_result)

        fn = aws_client.lambda_.get_function_configuration(
            FunctionName=func_name, Qualifier="$LATEST"
        )
        snapshot.match("get-function-configuration", fn)

        first_ver = aws_client.lambda_.publish_version(
            FunctionName=func_name, RevisionId=fn["RevisionId"], Description="my-first-version"
        )
        snapshot.match("publish_version_1", first_ver)

        get_function_configuration = aws_client.lambda_.get_function_configuration(
            FunctionName=func_name, Qualifier=first_ver["Version"]
        )
        snapshot.match("get_function_configuration_version_1", get_function_configuration)

        aws_client.lambda_.get_waiter("function_updated_v2").wait(
            FunctionName=func_name, Qualifier=first_ver["Version"]
        )

        # There's no ProvisionedConcurrencyConfiguration yet
        assert (
            get_invoke_init_type(aws_client.lambda_, func_name, first_ver["Version"]) == "on-demand"
        )

        # Create Alias and add ProvisionedConcurrencyConfiguration to it
        alias = aws_client.lambda_.create_alias(
            FunctionName=func_name, FunctionVersion=first_ver["Version"], Name=alias_name
        )
        snapshot.match("create_alias", alias)
        get_function_result = aws_client.lambda_.get_function(
            FunctionName=func_name, Qualifier=first_ver["Version"]
        )
        snapshot.match("get_function_before_provisioned", get_function_result)
        aws_client.lambda_.put_provisioned_concurrency_config(
            FunctionName=func_name, Qualifier=alias_name, ProvisionedConcurrentExecutions=1
        )
        assert wait_until(concurrency_update_done(aws_client.lambda_, func_name, alias_name))
        get_function_result = aws_client.lambda_.get_function(
            FunctionName=func_name, Qualifier=alias_name
        )
        snapshot.match("get_function_after_provisioned", get_function_result)

        # Alias AND Version now both use provisioned-concurrency (!)
        assert (
            get_invoke_init_type(aws_client.lambda_, func_name, first_ver["Version"])
            == "provisioned-concurrency"
        )
        assert (
            get_invoke_init_type(aws_client.lambda_, func_name, alias_name)
            == "provisioned-concurrency"
        )

        # Update lambda configuration and publish new version
        aws_client.lambda_.update_function_configuration(FunctionName=func_name, Timeout=10)
        assert wait_until(update_done(aws_client.lambda_, func_name))
        lambda_conf = aws_client.lambda_.get_function_configuration(FunctionName=func_name)
        snapshot.match("get_function_after_update", lambda_conf)

        # Move existing alias to the new version
        new_version = aws_client.lambda_.publish_version(
            FunctionName=func_name, RevisionId=lambda_conf["RevisionId"]
        )
        snapshot.match("publish_version_2", new_version)
        new_alias = aws_client.lambda_.update_alias(
            FunctionName=func_name, FunctionVersion=new_version["Version"], Name=alias_name
        )
        snapshot.match("update_alias", new_alias)

        # lambda should now be provisioning new "hot" execution environments for this new alias->version pointer
        # the old one should be de-provisioned
        get_provisioned_config_result = aws_client.lambda_.get_provisioned_concurrency_config(
            FunctionName=func_name, Qualifier=alias_name
        )
        snapshot.match("get_provisioned_config_after_alias_move", get_provisioned_config_result)
        assert wait_until(
            concurrency_update_done(aws_client.lambda_, func_name, alias_name),
            strategy="linear",
            wait=30,
            max_retries=20,
            _max_wait=600,
        )  # this is SLOW (~6-8 min)

        # concurrency should still only work for the alias now
        # NOTE: the old version has been de-provisioned and will run 'on-demand' now!
        assert (
            get_invoke_init_type(aws_client.lambda_, func_name, first_ver["Version"]) == "on-demand"
        )
        assert (
            get_invoke_init_type(aws_client.lambda_, func_name, new_version["Version"])
            == "provisioned-concurrency"
        )
        assert (
            get_invoke_init_type(aws_client.lambda_, func_name, alias_name)
            == "provisioned-concurrency"
        )

        # ProvisionedConcurrencyConfig should only be "registered" to the alias, not the referenced version
        with pytest.raises(
            aws_client.lambda_.exceptions.ProvisionedConcurrencyConfigNotFoundException
        ) as e:
            aws_client.lambda_.get_provisioned_concurrency_config(
                FunctionName=func_name, Qualifier=new_version["Version"]
            )
        snapshot.match("provisioned_concurrency_notfound", e.value.response)