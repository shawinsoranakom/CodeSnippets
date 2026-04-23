def test_create_change_set_update_without_parameters(
    cleanup_stacks,
    cleanup_changesets,
    is_change_set_created_and_available,
    is_change_set_finished,
    snapshot,
    aws_client,
):
    snapshot.add_transformer(snapshot.transform.cloudformation_api())
    """after creating a stack via a CREATE change set we send an UPDATE change set changing the SNS topic name"""
    stack_name = f"stack-{short_uid()}"
    change_set_name = f"change-set-{short_uid()}"
    change_set_name2 = f"change-set-{short_uid()}"

    template_path = os.path.join(
        os.path.dirname(__file__), "../../../templates/sns_topic_simple.yaml"
    )

    response = aws_client.cloudformation.create_change_set(
        StackName=stack_name,
        ChangeSetName=change_set_name,
        TemplateBody=load_template_raw(template_path),
        ChangeSetType="CREATE",
    )
    snapshot.match("create_change_set", response)
    change_set_id = response["Id"]
    stack_id = response["StackId"]
    assert change_set_id
    assert stack_id

    try:
        # Change set can now either be already created/available or it is pending/unavailable
        wait_until(is_change_set_created_and_available(change_set_id))
        aws_client.cloudformation.execute_change_set(ChangeSetName=change_set_id)
        wait_until(is_change_set_finished(change_set_id))
        template = load_template_raw(template_path)

        update_response = aws_client.cloudformation.create_change_set(
            StackName=stack_name,
            ChangeSetName=change_set_name2,
            TemplateBody=template.replace("sns-topic-simple", "sns-topic-simple-2"),
            ChangeSetType="UPDATE",
        )
        assert wait_until(is_change_set_created_and_available(update_response["Id"]))
        snapshot.match(
            "describe_change_set",
            aws_client.cloudformation.describe_change_set(ChangeSetName=update_response["Id"]),
        )
        snapshot.match(
            "list_change_set", aws_client.cloudformation.list_change_sets(StackName=stack_name)
        )

        describe_response = aws_client.cloudformation.describe_change_set(
            ChangeSetName=update_response["Id"]
        )
        changes = describe_response["Changes"]
        assert len(changes) == 1
        assert changes[0]["Type"] == "Resource"
        change = changes[0]["ResourceChange"]
        assert change["Action"] == "Modify"
        assert change["ResourceType"] == "AWS::SNS::Topic"
        assert change["LogicalResourceId"] == "topic123"
        assert "sns-topic-simple" in change["PhysicalResourceId"]
        assert change["Replacement"] == "True"
        assert "Properties" in change["Scope"]
        assert len(change["Details"]) == 1
        assert change["Details"][0]["Target"]["Name"] == "TopicName"
        assert change["Details"][0]["Target"]["RequiresRecreation"] == "Always"
    finally:
        cleanup_changesets(changesets=[change_set_id])
        cleanup_stacks(stacks=[stack_id])