def valid_topic(topic: Any) -> str:
    """Validate that this is a valid topic name/filter.

    This function is not cached and is not expected to be called
    directly outside of this module. It is not marked as protected
    only because its tested directly in test_util.py.

    If it gets used outside of valid_subscribe_topic and
    valid_publish_topic, it may need an lru_cache decorator or
    an lru_cache decorator on the function where its used.
    """
    validated_topic = cv.string(topic)
    try:
        raw_validated_topic = validated_topic.encode("utf-8")
    except UnicodeError as err:
        raise vol.Invalid("MQTT topic name/filter must be valid UTF-8 string.") from err
    if not raw_validated_topic:
        raise vol.Invalid("MQTT topic name/filter must not be empty.")
    if len(raw_validated_topic) > 65535:
        raise vol.Invalid(
            "MQTT topic name/filter must not be longer than 65535 encoded bytes."
        )

    for char in validated_topic:
        if char == "\0":
            raise vol.Invalid("MQTT topic name/filter must not contain null character.")
        if char <= "\u001f" or "\u007f" <= char <= "\u009f":
            raise vol.Invalid(
                "MQTT topic name/filter must not contain control characters."
            )
        if "\ufdd0" <= char <= "\ufdef" or (ord(char) & 0xFFFF) in (0xFFFE, 0xFFFF):
            raise vol.Invalid("MQTT topic name/filter must not contain non-characters.")

    return validated_topic