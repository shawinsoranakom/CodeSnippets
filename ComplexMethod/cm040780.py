def _validate_message_attributes(
    message_attributes: MessageAttributeMap, position: int | None = None
) -> None:
    """
    Validate the message attributes, and raises an exception if those do not follow AWS validation
    See: https://docs.aws.amazon.com/sns/latest/dg/sns-message-attributes.html
    Regex from: https://stackoverflow.com/questions/40718851/regex-that-does-not-allow-consecutive-dots
    :param message_attributes: the message attributes map for the message
    :param position: given to give the Batch Entry position if coming from `publishBatch`
    :raises: InvalidParameterValueException
    :return: None
    """
    for attr_name, attr in message_attributes.items():
        if len(attr_name) > 256:
            raise InvalidParameterValueException(
                "Length of message attribute name must be less than 256 bytes."
            )
        _validate_message_attribute_name(attr_name)
        # `DataType` is a required field for MessageAttributeValue
        if (data_type := attr.get("DataType")) is None:
            if position:
                at = f"publishBatchRequestEntries.{position}.member.messageAttributes.{attr_name}.member.dataType"
            else:
                at = f"messageAttributes.{attr_name}.member.dataType"

            raise CommonServiceException(
                code="ValidationError",
                message=f"1 validation error detected: Value null at '{at}' failed to satisfy constraint: Member must not be null",
                sender_fault=True,
            )

        if data_type not in (
            "String",
            "Number",
            "Binary",
        ) and not ATTR_TYPE_REGEX.match(data_type):
            raise InvalidParameterValueException(
                f"The message attribute '{attr_name}' has an invalid message attribute type, the set of supported type prefixes is Binary, Number, and String."
            )
        if not any(attr_value.endswith("Value") for attr_value in attr):
            raise InvalidParameterValueException(
                f"The message attribute '{attr_name}' must contain non-empty message attribute value for message attribute type '{data_type}'."
            )

        value_key_data_type = "Binary" if data_type.startswith("Binary") else "String"
        value_key = f"{value_key_data_type}Value"
        if value_key not in attr:
            raise InvalidParameterValueException(
                f"The message attribute '{attr_name}' with type '{data_type}' must use field '{value_key_data_type}'."
            )
        elif not attr[value_key]:
            raise InvalidParameterValueException(
                f"The message attribute '{attr_name}' must contain non-empty message attribute value for message attribute type '{data_type}'.",
            )