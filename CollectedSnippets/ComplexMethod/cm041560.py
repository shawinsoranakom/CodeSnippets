def test_sns_topic_update_name(deploy_cfn_template, aws_client, snapshot):
    """Test updating SNS Topic with TopicName change (requires resource replacement)."""
    snapshot.add_transformer(snapshot.transform.key_value("TopicArn"))
    snapshot.add_transformer(
        snapshot.transform.key_value(
            "SubscriptionArn", "PendingConfirmation", reference_replacement=False
        ),
    )

    initial_topic_name = f"test-topic-{short_uid()}"

    stack = deploy_cfn_template(
        parameters={
            "TopicName": initial_topic_name,
            "DisplayName": "Initial Display Name",
            "Environment": "test",  # tag
            "Project": "localstack",  # tag
        },
        template_path=os.path.join(
            os.path.dirname(__file__), "../../../templates/sns_topic_update.yaml"
        ),
    )

    initial_topic_arn = stack.outputs["TopicArn"]

    initial_attrs = aws_client.sns.get_topic_attributes(TopicArn=initial_topic_arn)
    snapshot.match("initial-topic-attributes", initial_attrs)

    # Store initial tags to verify they are preserved
    initial_tags = aws_client.sns.list_tags_for_resource(ResourceArn=initial_topic_arn)
    initial_tag_dict = {tag["Key"]: tag["Value"] for tag in initial_tags["Tags"]}
    assert initial_tag_dict["Environment"] == "test"
    assert initial_tag_dict["Project"] == "localstack"

    # Get initial subscriptions
    initial_subscriptions = aws_client.sns.list_subscriptions_by_topic(TopicArn=initial_topic_arn)
    snapshot.match("initial-subscriptions", initial_subscriptions)

    new_topic_name = f"test-topic-new-{short_uid()}"

    # Update the stack with new TopicName
    updated_stack = deploy_cfn_template(
        parameters={
            "TopicName": new_topic_name,
            "DisplayName": "Updated Display Name",
            "Environment": "production",  # tag
            "Project": "localstack",  # tag
        },
        template_path=os.path.join(
            os.path.dirname(__file__), "../../../templates/sns_topic_update.yaml"
        ),
        stack_name=stack.stack_name,
        is_update=True,
    )

    new_topic_arn = updated_stack.outputs["TopicArn"]
    assert new_topic_arn != initial_topic_arn  # Confirm topic was replaced

    # Verify new topic state
    new_attrs = aws_client.sns.get_topic_attributes(TopicArn=new_topic_arn)
    snapshot.match("new-topic-attributes", new_attrs)

    # Verify tags were preserved and updated
    new_tags = aws_client.sns.list_tags_for_resource(ResourceArn=new_topic_arn)
    new_tag_dict = {tag["Key"]: tag["Value"] for tag in new_tags["Tags"]}

    # Assert tags were preserved (Project tag should still exist)
    assert "Project" in new_tag_dict
    assert new_tag_dict["Project"] == initial_tag_dict["Project"]  # Should be "localstack"
    # Assert Environment tag was updated
    assert new_tag_dict["Environment"] == "production"

    # Verify subscriptions were preserved
    new_subscriptions = aws_client.sns.list_subscriptions_by_topic(TopicArn=new_topic_arn)
    snapshot.match("new-subscriptions", new_subscriptions)

    # Verify old topic was deleted
    try:
        aws_client.sns.get_topic_attributes(TopicArn=initial_topic_arn)
        raise AssertionError("Old topic should have been deleted")
    except aws_client.sns.exceptions.NotFoundException:
        # Expected - old topic should be deleted
        pass