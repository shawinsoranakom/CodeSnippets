def test_nested_conditions(
        self,
        aws_client,
        deploy_cfn_template,
        cleanups,
        env_type,
        should_create_bucket,
        should_create_policy,
        snapshot,
    ):
        """
        Tests the case where a condition references another condition

        EnvType == "prod" && BucketName != "" ==> creates bucket + policy
        EnvType == "test" && BucketName != "" ==> creates bucket only
        EnvType == "test" && BucketName == "" ==> no resource created
        EnvType == "prod" && BucketName == "" ==> no resource created
        """
        bucket_name = f"ls-test-bucket-{short_uid()}" if should_create_bucket else ""
        stack_name = f"condition-test-stack-{short_uid()}"
        changeset_name = "initial"
        cleanups.append(lambda: aws_client.cloudformation.delete_stack(StackName=stack_name))
        snapshot.add_transformer(snapshot.transform.cloudformation_api())
        if bucket_name:
            snapshot.add_transformer(snapshot.transform.regex(bucket_name, "<bucket-name>"))
        snapshot.add_transformer(snapshot.transform.regex(stack_name, "<stack-name>"))

        template = load_file(
            os.path.join(THIS_DIR, "../../../templates/conditions/nested-conditions.yaml")
        )
        create_cs_result = aws_client.cloudformation.create_change_set(
            StackName=stack_name,
            ChangeSetName=changeset_name,
            TemplateBody=template,
            ChangeSetType="CREATE",
            Parameters=[
                {"ParameterKey": "EnvType", "ParameterValue": env_type},
                {"ParameterKey": "BucketName", "ParameterValue": bucket_name},
            ],
        )
        snapshot.match("create_cs_result", create_cs_result)

        aws_client.cloudformation.get_waiter("change_set_create_complete").wait(
            ChangeSetName=changeset_name, StackName=stack_name
        )

        describe_changeset_result = aws_client.cloudformation.describe_change_set(
            ChangeSetName=changeset_name, StackName=stack_name
        )
        snapshot.match("describe_changeset_result", describe_changeset_result)
        aws_client.cloudformation.execute_change_set(
            ChangeSetName=changeset_name, StackName=stack_name
        )
        aws_client.cloudformation.get_waiter("stack_create_complete").wait(StackName=stack_name)

        stack_resources = aws_client.cloudformation.describe_stack_resources(StackName=stack_name)
        if should_create_policy:
            stack_policy = [
                sr
                for sr in stack_resources["StackResources"]
                if sr["ResourceType"] == "AWS::S3::BucketPolicy"
            ][0]
            snapshot.add_transformer(
                snapshot.transform.regex(stack_policy["PhysicalResourceId"], "<stack-policy>"),
                priority=-1,
            )

        snapshot.match("stack_resources", stack_resources)
        stack_events = aws_client.cloudformation.describe_stack_events(StackName=stack_name)
        snapshot.match("stack_events", stack_events)
        describe_stack_result = aws_client.cloudformation.describe_stacks(StackName=stack_name)
        snapshot.match("describe_stack_result", describe_stack_result)

        # manual assertions

        # check that bucket exists
        try:
            aws_client.s3.head_bucket(Bucket=bucket_name)
            bucket_exists = True
        except Exception:
            bucket_exists = False

        assert bucket_exists == should_create_bucket

        if bucket_exists:
            # check if a policy exists on the bucket
            try:
                aws_client.s3.get_bucket_policy(Bucket=bucket_name)
                bucket_policy_exists = True
            except Exception:
                bucket_policy_exists = False

            assert bucket_policy_exists == should_create_policy