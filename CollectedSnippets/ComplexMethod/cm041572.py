def test_create_change_set_without_parameters(
    cleanup_stacks, cleanup_changesets, is_change_set_created_and_available, aws_client
):
    stack_name = f"stack-{short_uid()}"
    change_set_name = f"change-set-{short_uid()}"

    template_path = os.path.join(
        os.path.dirname(__file__), "../../../templates/sns_topic_simple.yaml"
    )
    response = aws_client.cloudformation.create_change_set(
        StackName=stack_name,
        ChangeSetName=change_set_name,
        TemplateBody=load_template_raw(template_path),
        ChangeSetType="CREATE",
    )
    change_set_id = response["Id"]
    stack_id = response["StackId"]
    assert change_set_id
    assert stack_id

    try:
        # make sure the change set wasn't executed (which would create a topic)
        topics = aws_client.sns.list_topics()
        topic_arns = [x["TopicArn"] for x in topics["Topics"]]
        assert not any("sns-topic-simple" in arn for arn in topic_arns)
        # stack is initially in REVIEW_IN_PROGRESS state. only after executing the change_set will it change its status
        stack_response = aws_client.cloudformation.describe_stacks(StackName=stack_id)
        assert stack_response["Stacks"][0]["StackStatus"] == "REVIEW_IN_PROGRESS"

        # Change set can now either be already created/available or it is pending/unavailable
        wait_until(
            is_change_set_created_and_available(change_set_id), 2, 10, strategy="exponential"
        )
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
        assert changes[0]["ResourceChange"]["LogicalResourceId"] == "topic123"
    finally:
        cleanup_stacks([stack_id])
        cleanup_changesets([change_set_id])