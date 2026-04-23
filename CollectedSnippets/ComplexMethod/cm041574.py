def test_create_change_set_with_ssm_parameter(
    cleanup_changesets,
    cleanup_stacks,
    is_change_set_created_and_available,
    is_stack_created,
    aws_client,
):
    """References a simple stack parameter"""

    stack_name = f"stack-{short_uid()}"
    change_set_name = f"change-set-{short_uid()}"
    parameter_name = f"ls-param-{short_uid()}"
    parameter_value = f"ls-param-value-{short_uid()}"
    sns_topic_logical_id = "topic123"
    parameter_logical_id = "parameter123"

    aws_client.ssm.put_parameter(Name=parameter_name, Value=parameter_value, Type="String")
    template_path = os.path.join(
        os.path.dirname(__file__), "../../../templates/dynamicparameter_ssm_string.yaml"
    )
    template_rendered = render_template(
        load_template_raw(template_path), parameter_name=parameter_name
    )
    response = aws_client.cloudformation.create_change_set(
        StackName=stack_name,
        ChangeSetName=change_set_name,
        TemplateBody=template_rendered,
        ChangeSetType="CREATE",
    )
    change_set_id = response["Id"]
    stack_id = response["StackId"]
    assert change_set_id
    assert stack_id

    try:
        # make sure the change set wasn't executed (which would create a new topic)
        list_topics_response = aws_client.sns.list_topics()
        matching_topics = [
            t for t in list_topics_response["Topics"] if parameter_value in t["TopicArn"]
        ]
        assert matching_topics == []

        # stack is initially in REVIEW_IN_PROGRESS state. only after executing the change_set will it change its status
        stack_response = aws_client.cloudformation.describe_stacks(StackName=stack_id)
        assert stack_response["Stacks"][0]["StackStatus"] == "REVIEW_IN_PROGRESS"

        # Change set can now either be already created/available or it is pending/unavailable
        wait_until(is_change_set_created_and_available(change_set_id))
        describe_response = aws_client.cloudformation.describe_change_set(
            ChangeSetName=change_set_id
        )

        assert describe_response["ChangeSetName"] == change_set_name
        assert describe_response["ChangeSetId"] == change_set_id
        assert describe_response["StackId"] == stack_id
        assert describe_response["StackName"] == stack_name
        assert describe_response["ExecutionStatus"] == "AVAILABLE"
        assert describe_response["Status"] == "CREATE_COMPLETE"
        changes = describe_response["Changes"]
        assert len(changes) == 1
        assert changes[0]["Type"] == "Resource"
        assert changes[0]["ResourceChange"]["Action"] == "Add"
        assert changes[0]["ResourceChange"]["ResourceType"] == "AWS::SNS::Topic"
        assert changes[0]["ResourceChange"]["LogicalResourceId"] == sns_topic_logical_id

        parameters = describe_response["Parameters"]
        assert len(parameters) == 1
        assert parameters[0]["ParameterKey"] == parameter_logical_id
        assert parameters[0]["ParameterValue"] == parameter_name
        assert parameters[0]["ResolvedValue"] == parameter_value  # the important part

        aws_client.cloudformation.execute_change_set(ChangeSetName=change_set_id)
        wait_until(is_stack_created(stack_id))

        topics = aws_client.sns.list_topics()
        topic_arns = [x["TopicArn"] for x in topics["Topics"]]
        assert any((parameter_value in t) for t in topic_arns)
    finally:
        cleanup_changesets([change_set_id])
        cleanup_stacks([stack_id])