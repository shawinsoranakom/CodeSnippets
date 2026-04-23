def set_queue_attributes(
        self, context: RequestContext, queue_url: String, attributes: QueueAttributeMap, **kwargs
    ) -> None:
        queue = self._resolve_queue(context, queue_url=queue_url)

        if not attributes:
            return

        queue.validate_queue_attributes(attributes)

        for k, v in attributes.items():
            if k in sqs_constants.INTERNAL_QUEUE_ATTRIBUTES:
                raise InvalidAttributeName(f"Unknown Attribute {k}.")
            if k in sqs_constants.DELETE_IF_DEFAULT and v == sqs_constants.DELETE_IF_DEFAULT[k]:
                if k in queue.attributes:
                    del queue.attributes[k]
            else:
                queue.attributes[k] = v

        # Special cases
        if queue.attributes.get(QueueAttributeName.Policy) == "":
            del queue.attributes[QueueAttributeName.Policy]

        redrive_policy = queue.attributes.get(QueueAttributeName.RedrivePolicy)
        if redrive_policy == "":
            del queue.attributes[QueueAttributeName.RedrivePolicy]
            return

        if redrive_policy:
            _redrive_policy = json.loads(redrive_policy)
            dl_target_arn = _redrive_policy.get("deadLetterTargetArn")
            max_receive_count = _redrive_policy.get("maxReceiveCount")
            # TODO: use the actual AWS responses
            if not dl_target_arn:
                raise InvalidParameterValueException(
                    "The required parameter 'deadLetterTargetArn' is missing"
                )
            if max_receive_count is None:
                raise InvalidParameterValueException(
                    "The required parameter 'maxReceiveCount' is missing"
                )
            try:
                max_receive_count = int(max_receive_count)
                valid_count = 1 <= max_receive_count <= 1000
            except ValueError:
                valid_count = False
            if not valid_count:
                raise InvalidParameterValueException(
                    f"Value {redrive_policy} for parameter RedrivePolicy is invalid. Reason: Invalid value for "
                    f"maxReceiveCount: {max_receive_count}, valid values are from 1 to 1000 both inclusive."
                )