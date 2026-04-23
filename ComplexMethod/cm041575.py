def test_execute_change_set(
    is_change_set_finished,
    is_change_set_created_and_available,
    is_change_set_failed_and_unavailable,
    cleanup_changesets,
    cleanup_stacks,
    aws_client,
):
    """check if executing a change set succeeds in creating/modifying the resources in changed"""

    stack_name = f"stack-{short_uid()}"
    change_set_name = f"change-set-{short_uid()}"
    template_path = os.path.join(
        os.path.dirname(__file__), "../../../templates/sns_topic_simple.yaml"
    )
    template_body = load_template_raw(template_path)

    response = aws_client.cloudformation.create_change_set(
        StackName=stack_name,
        ChangeSetName=change_set_name,
        TemplateBody=template_body,
        ChangeSetType="CREATE",
    )
    change_set_id = response["Id"]
    stack_id = response["StackId"]
    assert change_set_id
    assert stack_id

    try:
        assert wait_until(is_change_set_created_and_available(change_set_id=change_set_id))
        aws_client.cloudformation.execute_change_set(ChangeSetName=change_set_id)
        assert wait_until(is_change_set_finished(change_set_id))
        # check if stack resource was created
        topics = aws_client.sns.list_topics()
        topic_arns = [x["TopicArn"] for x in topics["Topics"]]
        assert any(("sns-topic-simple" in t) for t in topic_arns)

        # new change set name
        change_set_name = f"change-set-{short_uid()}"
        # check if update with identical stack leads to correct behavior
        response = aws_client.cloudformation.create_change_set(
            StackName=stack_name,
            ChangeSetName=change_set_name,
            TemplateBody=template_body,
            ChangeSetType="UPDATE",
        )
        change_set_id = response["Id"]
        stack_id = response["StackId"]
        assert wait_until(is_change_set_failed_and_unavailable(change_set_id=change_set_id))
        describe_failed_change_set_result = aws_client.cloudformation.describe_change_set(
            ChangeSetName=change_set_id
        )
        assert describe_failed_change_set_result["ChangeSetName"] == change_set_name
        assert (
            describe_failed_change_set_result["StatusReason"]
            == "The submitted information didn't contain changes. Submit different information to create a change set."
        )
        with pytest.raises(ClientError) as e:
            aws_client.cloudformation.execute_change_set(ChangeSetName=change_set_id)
        e.match("InvalidChangeSetStatus")
        e.match(
            rf"ChangeSet \[{change_set_id}\] cannot be executed in its current status of \[FAILED\]"
        )
    finally:
        cleanup_changesets([change_set_id])
        cleanup_stacks([stack_id])