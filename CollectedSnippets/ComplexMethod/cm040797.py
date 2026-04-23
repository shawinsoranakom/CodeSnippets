def update(
        self,
        request: ResourceRequest[SNSTopicProperties],
    ) -> ProgressEvent[SNSTopicProperties]:
        """
        Update a resource

        IAM permissions required:
          - sns:SetTopicAttributes
          - sns:TagResource
          - sns:UntagResource
          - sns:Subscribe
          - sns:Unsubscribe
          - sns:GetTopicAttributes
          - sns:ListTagsForResource
          - sns:ListSubscriptionsByTopic
          - sns:GetDataProtectionPolicy
          - sns:PutDataProtectionPolicy
          - sns:CreateTopic (Not in the original spec)
          - sns:DeleteTopic (Not in the original spec)
        """
        desired_state = request.desired_state
        previous_state = request.previous_state
        sns = request.aws_client_factory.sns

        current_topic_arn = previous_state.get("TopicArn")
        if not current_topic_arn:
            raise ValueError("TopicArn not found in previous_state")

        # Check if TopicName has changed (requires recreation)
        desired_topic_name = desired_state.get("TopicName")
        previous_topic_name = previous_state.get("TopicName")

        if not previous_topic_name:
            raise ValueError("Previous topic name is not present.")

        if desired_topic_name != previous_topic_name:
            # TopicName changed - need to create new topic and delete old one

            # First, get current subscriptions and tags to preserve them
            try:
                current_subscriptions = sns.list_subscriptions_by_topic(
                    TopicArn=current_topic_arn
                ).get("Subscriptions", [])
                current_tags_response = sns.list_tags_for_resource(ResourceArn=current_topic_arn)
                current_tags = current_tags_response.get("Tags", [])
            except Exception:
                # If we can't get current state, proceed without preserving subscriptions/tags
                current_subscriptions = []
                current_tags = []

            create_result = self.create(request)
            if create_result.status != OperationStatus.SUCCESS:
                return create_result

            new_topic_arn = create_result.resource_model["TopicArn"]

            # Preserve existing subscriptions on new topic
            for subscription in current_subscriptions:
                if subscription.get("Protocol") and subscription.get("Endpoint"):
                    try:
                        sns.subscribe(
                            TopicArn=new_topic_arn,
                            Protocol=subscription["Protocol"],
                            Endpoint=subscription["Endpoint"],
                        )
                    except Exception:
                        # Continue if subscription fails
                        pass

            # Preserve existing tags if not overridden by new tags
            if current_tags:
                new_tags = desired_state.get("Tags", [])
                new_tag_keys = {tag["Key"] for tag in new_tags}

                # Add current tags that aren't being overridden
                tags_to_preserve = [tag for tag in current_tags if tag["Key"] not in new_tag_keys]
                if tags_to_preserve:
                    try:
                        sns.tag_resource(ResourceArn=new_topic_arn, Tags=tags_to_preserve)
                    except Exception:
                        # Continue if tagging fails
                        pass

            # Delete old topic
            try:
                delete_request = ResourceRequest(
                    _original_payload=previous_state,
                    aws_client_factory=request.aws_client_factory,
                    request_token=request.request_token,
                    stack_name=request.stack_name,
                    stack_id=request.stack_id,
                    account_id=request.account_id,
                    region_name=request.region_name,
                    desired_state=request.previous_state,
                    logical_resource_id=request.logical_resource_id,
                    resource_type=request.logical_resource_id,
                    logger=request.logger,
                    custom_context=request.custom_context,
                    action=request.action,
                )
                self.delete(delete_request)
            except Exception:
                # Continue even if delete fails - new topic is created
                pass

            desired_state["TopicArn"] = new_topic_arn

            return ProgressEvent(
                status=OperationStatus.SUCCESS,
                resource_model=desired_state,
                custom_context=request.custom_context,
            )

        # Normal update path - TopicName hasn't changed
        desired_state["TopicArn"] = current_topic_arn

        if desired_state.get("DisplayName") != previous_state.get("DisplayName"):
            display_name = desired_state.get("DisplayName")
            if display_name is not None:
                sns.set_topic_attributes(
                    TopicArn=current_topic_arn,
                    AttributeName="DisplayName",
                    AttributeValue=display_name,
                )

        desired_tags = desired_state.get("Tags", [])
        previous_tags = previous_state.get("Tags", [])

        desired_tags_dict = {tag["Key"]: tag["Value"] for tag in desired_tags}
        previous_tags_dict = {tag["Key"]: tag["Value"] for tag in previous_tags}

        tags_to_add = []
        for key, value in desired_tags_dict.items():
            if key not in previous_tags_dict or previous_tags_dict[key] != value:
                tags_to_add.append({"Key": key, "Value": value})

        tags_to_remove = []
        for key in previous_tags_dict:
            if key not in desired_tags_dict:
                tags_to_remove.append(key)

        if tags_to_add:
            sns.tag_resource(ResourceArn=current_topic_arn, Tags=tags_to_add)

        if tags_to_remove:
            sns.untag_resource(ResourceArn=current_topic_arn, TagKeys=tags_to_remove)

        return ProgressEvent(
            status=OperationStatus.SUCCESS,
            resource_model=desired_state,
            custom_context=request.custom_context,
        )