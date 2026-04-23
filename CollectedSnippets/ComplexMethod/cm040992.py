def check_attributes(message_attributes: MessageBodyAttributeMap):
    if not message_attributes:
        return
    for attribute_name in message_attributes:
        if len(attribute_name) >= 256:
            raise InvalidParameterValueException(
                "Message (user) attribute names must be shorter than 256 Bytes"
            )
        if not re.match(sqs_constants.ATTR_NAME_CHAR_REGEX, attribute_name.lower()):
            raise InvalidParameterValueException(
                "Message (user) attributes name can only contain upper and lower score characters, digits, periods, "
                "hyphens and underscores. "
            )
        if not re.match(sqs_constants.ATTR_NAME_PREFIX_SUFFIX_REGEX, attribute_name.lower()):
            raise InvalidParameterValueException(
                "You can't use message attribute names beginning with 'AWS.' or 'Amazon.'. "
                "These strings are reserved for internal use. Additionally, they cannot start or end with '.'."
            )

        attribute = message_attributes[attribute_name]
        attribute_type = attribute.get("DataType")
        if not attribute_type:
            raise InvalidParameterValueException("Missing required parameter DataType")
        if not re.match(sqs_constants.ATTR_TYPE_REGEX, attribute_type):
            raise InvalidParameterValueException(
                f"Type for parameter MessageAttributes.Attribute_name.DataType must be prefixed"
                f'with "String", "Binary", or "Number", but was: {attribute_type}'
            )
        if len(attribute_type) >= 256:
            raise InvalidParameterValueException(
                "Message (user) attribute types must be shorter than 256 Bytes"
            )

        if attribute_type == "String":
            try:
                attribute_value = attribute.get("StringValue")

                if not attribute_value:
                    raise InvalidParameterValueException(
                        f"Message (user) attribute '{attribute_name}' must contain a non-empty value of type 'String'."
                    )

                check_message_content(attribute_value)
            except InvalidMessageContents as e:
                # AWS throws a different exception here
                raise InvalidParameterValueException(e.args[0])