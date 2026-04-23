def test_function_revisions_version_and_alias(
        self, create_lambda_function, snapshot, aws_client
    ):
        """Tests revision id lifecycle for 1) publishing function versions and 2) creating and updating aliases
        Shortcut notation to clarify branching:
        revN: revision counter for $LATEST
        rev_vN: revision counter for versions
        rev_aN: revision counter for aliases
        """
        # rev1: create function
        function_name = f"fn-{short_uid()}"
        create_function_response = create_lambda_function(
            func_name=function_name,
            handler_file=TEST_LAMBDA_PYTHON_ECHO,
            runtime=Runtime.python3_12,
        )
        snapshot.match("create_function_response_rev1", create_function_response)
        rev1_create_function = create_function_response["CreateFunctionResponse"]["RevisionId"]

        # rev2: created function becomes active
        get_function_response_rev2 = aws_client.lambda_.get_function(FunctionName=function_name)
        snapshot.match("get_function_active_rev2", get_function_response_rev2)
        rev2_active_state = get_function_response_rev2["Configuration"]["RevisionId"]
        assert rev1_create_function != rev2_active_state

        with pytest.raises(aws_client.lambda_.exceptions.PreconditionFailedException) as e:
            aws_client.lambda_.publish_version(FunctionName=function_name, RevisionId="wrong")
        snapshot.match("publish_version_revision_exception", e.value.response)

        # rev_v1: publish version
        fn_version_response = aws_client.lambda_.publish_version(
            FunctionName=function_name, RevisionId=rev2_active_state
        )
        snapshot.match("publish_version_response_rev_v1", fn_version_response)
        function_version = fn_version_response["Version"]
        rev_v1_publish_version = fn_version_response["RevisionId"]
        assert rev2_active_state != rev_v1_publish_version

        # rev_v2: published version becomes active does NOT change revision
        aws_client.lambda_.get_waiter("published_version_active").wait(FunctionName=function_name)
        get_function_response_rev_v2 = aws_client.lambda_.get_function(
            FunctionName=function_name, Qualifier=function_version
        )
        snapshot.match("get_function_published_version_rev_v2", get_function_response_rev_v2)
        rev_v2_publish_version_done = get_function_response_rev_v2["Configuration"]["RevisionId"]
        assert rev_v1_publish_version == rev_v2_publish_version_done

        # publish_version changes the revision id of $LATEST
        get_function_response_rev3 = aws_client.lambda_.get_function(FunctionName=function_name)
        snapshot.match("get_function_latest_rev3", get_function_response_rev3)
        rev3_publish_version = get_function_response_rev3["Configuration"]["RevisionId"]
        assert rev2_active_state != rev3_publish_version

        # rev_a1: create alias
        alias_name = "revision_alias"
        create_alias_response = aws_client.lambda_.create_alias(
            FunctionName=function_name,
            Name=alias_name,
            FunctionVersion=function_version,
        )
        snapshot.match("create_alias_response_rev_a1", create_alias_response)
        rev_a1_create_alias = create_alias_response["RevisionId"]
        assert rev_v2_publish_version_done != rev_a1_create_alias

        # create_alias does NOT change the revision id of $LATEST
        get_function_response_rev4 = aws_client.lambda_.get_function(FunctionName=function_name)
        snapshot.match("get_function_latest_rev4", get_function_response_rev4)
        rev4_create_alias = get_function_response_rev4["Configuration"]["RevisionId"]
        assert rev3_publish_version == rev4_create_alias

        # create_alias does NOT change the revision id of versions
        get_function_response_rev_v3 = aws_client.lambda_.get_function(
            FunctionName=function_name, Qualifier=function_version
        )
        snapshot.match("get_function_published_version_rev_v3", get_function_response_rev_v3)
        rev_v3_create_alias = get_function_response_rev_v3["Configuration"]["RevisionId"]
        assert rev_v2_publish_version_done == rev_v3_create_alias

        with pytest.raises(aws_client.lambda_.exceptions.PreconditionFailedException) as e:
            aws_client.lambda_.update_alias(
                FunctionName=function_name,
                Name=alias_name,
                RevisionId="wrong",
            )
        snapshot.match("update_alias_revision_exception", e.value.response)

        # rev_a2: update alias
        update_alias_response = aws_client.lambda_.update_alias(
            FunctionName=function_name,
            Name=alias_name,
            Description="something changed",
            RevisionId=rev_a1_create_alias,
        )
        snapshot.match("update_alias_response_rev_a2", update_alias_response)
        rev_a2_update_alias = update_alias_response["RevisionId"]
        assert rev_a1_create_alias != rev_a2_update_alias