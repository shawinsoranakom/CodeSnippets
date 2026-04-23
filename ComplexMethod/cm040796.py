def create(
        self,
        request: ResourceRequest[SNSTopicProperties],
    ) -> ProgressEvent[SNSTopicProperties]:
        """
        Create a new resource.

        Primary identifier fields:
          - /properties/TopicArn



        Create-only properties:
          - /properties/TopicName
          - /properties/FifoTopic

        Read-only properties:
          - /properties/TopicArn

        IAM permissions required:
          - sns:CreateTopic
          - sns:TagResource
          - sns:Subscribe
          - sns:GetTopicAttributes
          - sns:PutDataProtectionPolicy

        """
        model = request.desired_state
        sns = request.aws_client_factory.sns

        attributes = {
            k: v
            for k, v in model.items()
            if v is not None
            if k not in ["TopicName", "Subscription", "Tags"]
        }
        if (fifo_topic := attributes.get("FifoTopic")) is not None:
            attributes["FifoTopic"] = canonicalize_bool_to_str(fifo_topic)

        if archive_policy := attributes.get("ArchivePolicy"):
            archive_policy["MessageRetentionPeriod"] = str(archive_policy["MessageRetentionPeriod"])
            attributes["ArchivePolicy"] = json.dumps(archive_policy)

        if (content_based_dedup := attributes.get("ContentBasedDeduplication")) is not None:
            attributes["ContentBasedDeduplication"] = canonicalize_bool_to_str(content_based_dedup)

        # Default name
        if model.get("TopicName") is None:
            model["TopicName"] = (
                f"topic-{short_uid()}.fifo" if fifo_topic else f"topic-{short_uid()}"
            )

        create_sns_response = sns.create_topic(Name=model["TopicName"], Attributes=attributes)
        model["TopicArn"] = create_sns_response["TopicArn"]

        # now we add subscriptions if they exists
        for subscription in model.get("Subscription", []):
            sns.subscribe(
                TopicArn=model["TopicArn"],
                Protocol=subscription["Protocol"],
                Endpoint=subscription["Endpoint"],
            )
        if tags := model.get("Tags"):
            sns.tag_resource(ResourceArn=model["TopicArn"], Tags=tags)

        return ProgressEvent(
            status=OperationStatus.SUCCESS,
            resource_model=model,
            custom_context=request.custom_context,
        )