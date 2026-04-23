def test_failure_options_for_stack_update(
        self, rollback_disabled, length_expected, aws_client, cleanups
    ):
        stack_name = f"stack-{short_uid()}"
        template = open(
            os.path.join(
                os.path.dirname(__file__), "../../../templates/multiple_bucket_update.yaml"
            ),
        ).read()

        aws_client.cloudformation.create_stack(
            StackName=stack_name,
            TemplateBody=template,
        )
        cleanups.append(lambda: aws_client.cloudformation.delete_stack(StackName=stack_name))

        def _assert_stack_process_finished():
            return stack_process_is_finished(aws_client.cloudformation, stack_name)

        assert wait_until(_assert_stack_process_finished)
        resources = aws_client.cloudformation.describe_stack_resources(StackName=stack_name)[
            "StackResources"
        ]
        created_resources = [
            resource for resource in resources if "CREATE_COMPLETE" in resource["ResourceStatus"]
        ]
        assert len(created_resources) == 2

        aws_client.cloudformation.update_stack(
            StackName=stack_name,
            TemplateBody=template,
            DisableRollback=rollback_disabled,
            Parameters=[
                {"ParameterKey": "Days", "ParameterValue": "-1"},
            ],
        )

        assert wait_until(_assert_stack_process_finished)

        resources = aws_client.cloudformation.describe_stack_resources(StackName=stack_name)[
            "StackResources"
        ]
        updated_resources = [
            resource
            for resource in resources
            if resource["ResourceStatus"] in ["CREATE_COMPLETE", "UPDATE_COMPLETE"]
        ]
        assert len(updated_resources) == length_expected