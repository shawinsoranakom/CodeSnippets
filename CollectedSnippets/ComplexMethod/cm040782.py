def create_topic(
        self,
        context: RequestContext,
        name: topicName,
        attributes: TopicAttributesMap | None = None,
        tags: TagList | None = None,
        data_protection_policy: attributeValue | None = None,
        **kwargs,
    ) -> CreateTopicResponse:
        store = self.get_store(context.account_id, context.region)
        topic_arn = sns_topic_arn(
            topic_name=name, region_name=context.region, account_id=context.account_id
        )
        attributes = dict(attributes) if attributes else {}
        if attributes.get("FifoTopic") and attributes["FifoTopic"].lower() == "true":
            pattern = SNS_TOPIC_NAME_PATTERN_FIFO
        else:
            # AWS does not seem to save explicit settings of fifo = false
            attributes.pop("FifoTopic", None)
            pattern = SNS_TOPIC_NAME_PATTERN

        if not re.match(pattern, name):
            raise InvalidParameterException("Invalid parameter: Topic Name")

        if existing_topic := store.topics.get(topic_arn):
            existing_attrs = existing_topic["attributes"]
            # TODO: validate attribute names
            for k, v in attributes.items():
                # special case for FifoTopic
                if k == "FifoTopic" and v == "false" and "FifoTopic" not in existing_attrs:
                    continue

                if not existing_attrs.get(k) or not existing_attrs.get(k) == v:
                    raise InvalidParameterException(
                        "Invalid parameter: Attributes Reason: Topic already exists with different attributes"
                    )
            tag_resource_success = self._check_matching_tags(context, topic_arn, tags)
            if not tag_resource_success:
                raise InvalidParameterException(
                    "Invalid parameter: Tags Reason: Topic already exists with different tags"
                )
            return CreateTopicResponse(TopicArn=topic_arn)

        attributes["EffectiveDeliveryPolicy"] = _create_default_effective_delivery_policy()

        topic = _create_topic(
            name=name,
            attributes=attributes,
            data_protection_policy=data_protection_policy,
            context=context,
        )
        if tags:
            self._tag_resource(context, resource_arn=topic_arn, tags=tags)

        store.topics[topic_arn] = topic

        return CreateTopicResponse(TopicArn=topic_arn)