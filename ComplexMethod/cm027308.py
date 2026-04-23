def valid_subscribe_topic(topic: Any) -> str:
    """Validate that we can subscribe using this MQTT topic."""
    validated_topic = valid_topic(topic)
    if "+" in validated_topic:
        for i in (i for i, c in enumerate(validated_topic) if c == "+"):
            if (i > 0 and validated_topic[i - 1] != "/") or (
                i < len(validated_topic) - 1 and validated_topic[i + 1] != "/"
            ):
                raise vol.Invalid(
                    "Single-level wildcard must occupy an entire level of the filter"
                )

    index = validated_topic.find("#")
    if index != -1:
        if index != len(validated_topic) - 1:
            # If there are multiple wildcards, this will also trigger
            raise vol.Invalid(
                "Multi-level wildcard must be the last character in the topic filter."
            )
        if len(validated_topic) > 1 and validated_topic[index - 1] != "/":
            raise vol.Invalid(
                "Multi-level wildcard must be after a topic level separator."
            )

    return validated_topic